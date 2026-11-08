package com.orez.usb;

import org.junit.Assume;
import org.junit.Test;
import static org.junit.Assert.*;

import java.io.*;
import java.nio.channels.FileChannel;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.security.MessageDigest;
import java.util.zip.*;

public class IsoImageTest {
    private static byte[] payload(int n) { byte[] b=new byte[n]; for(int i=0;i<n;i++) b[i]=(byte)(i*31+7); return b; }

    private static Path temp(byte[] data) throws IOException {
        Path p=Files.createTempFile("orez",".bin"); Files.write(p,data); p.toFile().deleteOnExit(); return p;
    }
    private static FileChannel open(Path p) throws IOException { return FileChannel.open(p,StandardOpenOption.READ); }
    private static byte[] readAll(InputStream in) throws IOException {
        ByteArrayOutputStream o=new ByteArrayOutputStream(); byte[] b=new byte[777]; int n;
        while((n=in.read(b))!=-1) o.write(b,0,n); return o.toByteArray();
    }

    private static byte[] storedZip(String[] names,byte[][] data,boolean deflateIso) throws IOException {
        ByteArrayOutputStream bytes=new ByteArrayOutputStream();
        try(ZipOutputStream z=new ZipOutputStream(bytes)) {
            for(int i=0;i<names.length;i++) {
                ZipEntry e=new ZipEntry(names[i]);
                if(!(deflateIso && names[i].endsWith(".iso"))) {
                    e.setMethod(ZipEntry.STORED); e.setSize(data[i].length); e.setCompressedSize(data[i].length);
                    CRC32 c=new CRC32(); c.update(data[i]); e.setCrc(c.getValue());
                }
                z.putNextEntry(e); z.write(data[i]); z.closeEntry();
            }
        }
        return bytes.toByteArray();
    }

    @Test public void plainFileIsWholeImage() throws Exception {
        Path p=temp(payload(4096));
        try(FileChannel c=open(p)) {
            IsoImage img=IsoImage.locate(c);
            assertFalse(img.fromZip()); assertEquals(0,img.offset); assertEquals(4096,img.length);
        }
    }

    @Test public void findsStoredIsoAndBundledChecksumInZip() throws Exception {
        byte[] iso=payload(100_000);
        String hash=hex(MessageDigest.getInstance("SHA-256").digest(iso));
        byte[] sum=(hash+"  OREZ-OS-0.1-live-amd64.iso\n").getBytes(StandardCharsets.US_ASCII);
        Path p=temp(storedZip(new String[]{"OREZ-OS-0.1-live-amd64.iso","OREZ-OS-0.1-live-amd64.iso.sha256"},new byte[][]{iso,sum},false));
        try(FileChannel c=open(p)) {
            IsoImage img=IsoImage.locate(c);
            assertTrue(img.fromZip());
            assertEquals("OREZ-OS-0.1-live-amd64.iso",img.entryName);
            assertEquals(iso.length,img.length);
            assertEquals(hash,img.bundledSha256);
            assertArrayEquals(iso,readAll(img.open(c)));
        }
    }

    @Test public void rejectsCompressedIso() throws Exception {
        Path p=temp(storedZip(new String[]{"x.iso"},new byte[][]{new byte[50_000]},true));
        try(FileChannel c=open(p)) {
            IsoImage.locate(c); fail("compressed ISO must be rejected");
        } catch(IOException e) { assertTrue(e.getMessage().contains("compressed")); }
    }

    @Test public void rejectsZipWithoutIso() throws Exception {
        Path p=temp(storedZip(new String[]{"readme.txt"},new byte[][]{"hi".getBytes()},false));
        try(FileChannel c=open(p)) { IsoImage.locate(c); fail(); }
        catch(IOException e) { assertTrue(e.getMessage().contains("does not contain")); }
    }

    @Test public void rejectsTruncatedZip() throws Exception {
        byte[] z=storedZip(new String[]{"a.iso"},new byte[][]{payload(20_000)},false);
        byte[] cut=java.util.Arrays.copyOf(z,z.length-30);
        try(FileChannel c=open(temp(cut))) { IsoImage.locate(c); fail(); }
        catch(IOException expected) {}
    }

    /** ZIP64 layout as written by the GitHub artifact uploader for a >4 GiB stored ISO. */
    @Test public void readsZip64Entry() throws Exception {
        byte[] iso=payload(9000);
        byte[] name="OREZ-OS-0.1-live-amd64.iso".getBytes(StandardCharsets.UTF_8);
        ByteArrayOutputStream o=new ByteArrayOutputStream();
        // local header with data descriptor flag and zip64 extra
        le32(o,0x04034b50); le16(o,45); le16(o,8); le16(o,0); le16(o,0); le16(o,0);
        le32(o,0); le32(o,0xffffffffL); le32(o,0xffffffffL); le16(o,name.length); le16(o,20);
        o.write(name); le16(o,1); le16(o,16); le64(o,0); le64(o,0);
        long dataAt=o.size(); o.write(iso);
        le32(o,0x08074b50); le32(o,0); le64(o,iso.length); le64(o,iso.length);
        long cd=o.size();
        le32(o,0x02014b50); le16(o,45); le16(o,45); le16(o,8); le16(o,0); le16(o,0); le16(o,0);
        le32(o,0); le32(o,0xffffffffL); le32(o,0xffffffffL); le16(o,name.length); le16(o,28); le16(o,0);
        le16(o,0); le16(o,0); le32(o,0); le32(o,0xffffffffL);
        o.write(name); le16(o,1); le16(o,24); le64(o,iso.length); le64(o,iso.length); le64(o,0);
        long cdSize=o.size()-cd, z64=o.size();
        le32(o,0x06064b50); le64(o,44); le16(o,45); le16(o,45); le32(o,0); le32(o,0);
        le64(o,1); le64(o,1); le64(o,cdSize); le64(o,cd);
        le32(o,0x07064b50); le32(o,0); le64(o,z64); le32(o,1);
        le32(o,0x06054b50); le16(o,0); le16(o,0); le16(o,0xffff); le16(o,0xffff);
        le32(o,0xffffffffL); le32(o,0xffffffffL); le16(o,0);
        try(FileChannel c=open(temp(o.toByteArray()))) {
            IsoImage img=IsoImage.locate(c);
            assertEquals(dataAt,img.offset); assertEquals(iso.length,img.length);
            assertArrayEquals(iso,readAll(img.open(c)));
        }
    }

    @Test public void picksHashForNamedFile() {
        String a="1".repeat(64), b="2".repeat(64);
        assertEquals(b,IsoImage.pickHash(a+"  other.iso\n"+b+" *dir/OREZ.iso\n","OREZ.iso"));
        assertEquals(a,IsoImage.pickHash(a+"\n","whatever.iso"));
        assertNull(IsoImage.pickHash("not a hash","x.iso"));
    }

    @Test public void knownOrezBuildIsRecognised() {
        assertNotNull(OrezReleases.label("CBD1435E4422A1E6C2300C2839AAAE46943BF3CB606FE97D6C216E7D875769BB"));
        assertNull(OrezReleases.label("0".repeat(64)));
    }

    /**
     * End-to-end check on the real downloaded OREZ artifact ZIP, when CI provides it
     * (env OREZ_ARTIFACT_ZIP). Hashes the ISO in place and runs the hybrid validator on it.
     */
    @Test public void realOrezArtifactZip() throws Exception {
        String path=System.getenv("OREZ_ARTIFACT_ZIP");
        Assume.assumeTrue(path!=null && new File(path).isFile());
        try(FileChannel c=open(Paths.get(path))) {
            IsoImage img=IsoImage.locate(c);
            assertTrue(img.fromZip());
            HybridIsoValidator.Info info=HybridIsoValidator.inspect(c,img.offset,img.length);
            assertEquals(img.length,info.bytes);
            MessageDigest d=MessageDigest.getInstance("SHA-256");
            try(InputStream in=img.open(c)) { byte[] b=new byte[1<<20]; int n; while((n=in.read(b))!=-1) d.update(b,0,n); }
            String h=hex(d.digest());
            System.out.println("OREZ artifact: entry="+img.entryName+" offset="+img.offset+" length="+img.length+" sha256="+h+" bundled="+img.bundledSha256+" label="+OrezReleases.label(h));
            assertNotNull("artifact ISO must match a pinned OREZ build",OrezReleases.label(h));
        }
    }

    private static String hex(byte[] b){StringBuilder s=new StringBuilder();for(byte x:b)s.append(String.format("%02x",x&255));return s.toString();}
    private static void le16(OutputStream o,int v) throws IOException {o.write(v);o.write(v>>>8);}
    private static void le32(OutputStream o,long v) throws IOException {for(int i=0;i<4;i++)o.write((int)(v>>>(8*i)));}
    private static void le64(OutputStream o,long v) throws IOException {for(int i=0;i<8;i++)o.write((int)(v>>>(8*i)));}
}
