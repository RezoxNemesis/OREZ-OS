package com.orez.usb;

import java.io.EOFException;
import java.io.IOException;
import java.io.InputStream;
import java.nio.ByteBuffer;
import java.nio.channels.FileChannel;
import java.nio.charset.StandardCharsets;
import java.util.Locale;

/**
 * Where the installer image lives inside the file the user picked: either the whole
 * file (a plain .iso) or one uncompressed ("stored") entry of a ZIP such as the
 * GitHub Actions artifact download. Nothing is extracted; the image bytes are read
 * in place, so the SHA-256, validation, write and read-back all see the exact same bytes.
 */
public final class IsoImage {
    public final long offset, length;
    public final String entryName;      // null for a plain ISO
    public final String bundledSha256;  // checksum file found next to the ISO in the ZIP, or null

    private IsoImage(long offset,long length,String entryName,String bundledSha256) {
        this.offset=offset; this.length=length; this.entryName=entryName; this.bundledSha256=bundledSha256;
    }
    public boolean fromZip(){return entryName!=null;}

    private static final long MAX_SUM_FILE=4096;

    public static IsoImage locate(FileChannel file) throws IOException {
        long size=file.size();
        if(size>=4) {
            byte[] magic=read(file,0,4);
            if(le32(magic,0)==0x04034b50L) return locateZip(file,size);
        }
        return new IsoImage(0,size,null,null);
    }

    private static IsoImage locateZip(FileChannel file,long size) throws IOException {
        // End of central directory: 22 bytes + up to 65535 bytes of comment.
        int tailLength=(int)Math.min(size,22+65535);
        byte[] tail=read(file,size-tailLength,tailLength);
        int eocd=-1;
        for(int i=tailLength-22;i>=0;i--) if(le32(tail,i)==0x06054b50L){eocd=i;break;}
        if(eocd<0) throw new IOException("This ZIP is incomplete (no end-of-archive record). Download it again.");
        long eocdPos=size-tailLength+eocd;
        long entries=le16(tail,eocd+10), cdSize=le32(tail,eocd+12), cdOffset=le32(tail,eocd+16);
        if(le16(tail,eocd+4)!=0 && le16(tail,eocd+4)!=0xffff) throw new IOException("Multi-part ZIP archives are not supported.");
        if(entries==0xffff || cdSize==0xffffffffL || cdOffset==0xffffffffL) {
            if(eocdPos<20) throw new IOException("ZIP64 locator is missing.");
            byte[] loc=read(file,eocdPos-20,20);
            if(le32(loc,0)!=0x07064b50L) throw new IOException("ZIP64 locator is missing.");
            long z64=le64(loc,8);
            byte[] rec=read(file,z64,56);
            if(le32(rec,0)!=0x06064b50L) throw new IOException("ZIP64 end-of-archive record is invalid.");
            entries=le64(rec,32); cdSize=le64(rec,40); cdOffset=le64(rec,48);
        }
        if(entries<=0 || entries>10000 || cdSize<=0 || cdSize>16L*1024*1024 || cdOffset<0 || cdOffset>size-cdSize)
            throw new IOException("The ZIP directory is invalid or the download is truncated.");
        byte[] cd=read(file,cdOffset,(int)cdSize);

        String isoName=null,sumName=null;
        long isoLocal=-1,isoLength=-1,sumLocal=-1,sumLength=-1;
        int sumMethod=-1;
        int isoCount=0;
        int p=0;
        for(long n=0;n<entries;n++) {
            if(p+46>cd.length || le32(cd,p)!=0x02014b50L) throw new IOException("The ZIP directory is damaged.");
            int flags=le16(cd,p+8), method=le16(cd,p+10);
            long compressed=le32(cd,p+20), uncompressed=le32(cd,p+24);
            int nameLength=le16(cd,p+28), extraLength=le16(cd,p+30), commentLength=le16(cd,p+32);
            long local=le32(cd,p+42);
            if(p+46+nameLength+extraLength+commentLength>cd.length) throw new IOException("The ZIP directory is damaged.");
            String name=new String(cd,p+46,nameLength,StandardCharsets.UTF_8);
            // ZIP64 extended information: only the fields that overflowed are present, in this order.
            int e=p+46+nameLength, end=e+extraLength;
            while(e+4<=end) {
                int id=le16(cd,e), len=le16(cd,e+2), q=e+4;
                if(q+len>end) break;
                if(id==1) {
                    if(uncompressed==0xffffffffL && q+8<=e+4+len){uncompressed=le64(cd,q);q+=8;}
                    if(compressed==0xffffffffL && q+8<=e+4+len){compressed=le64(cd,q);q+=8;}
                    if(local==0xffffffffL && q+8<=e+4+len){local=le64(cd,q);q+=8;}
                }
                e+=4+len;
            }
            String base=name.substring(name.lastIndexOf('/')+1).toLowerCase(Locale.ROOT);
            if(base.endsWith(".iso") && !name.endsWith("/")) {
                isoCount++;
                if((flags&1)!=0) throw new IOException("The ISO inside this ZIP is encrypted.");
                if(method!=0 || compressed!=uncompressed)
                    throw new IOException("The ISO inside this ZIP is compressed. Extract the .iso with a file manager and select it directly.");
                isoName=name; isoLocal=local; isoLength=uncompressed;
            } else if(base.endsWith(".iso.sha256") || base.equals("sha256sums") || base.equals("sha256sums.txt")) {
                if((flags&1)==0 && compressed==uncompressed && uncompressed>0 && uncompressed<=MAX_SUM_FILE) {
                    sumName=name; sumLocal=local; sumLength=uncompressed; sumMethod=method;
                }
            }
            p+=46+nameLength+extraLength+commentLength;
        }
        if(isoCount==0) throw new IOException("This ZIP does not contain an .iso file.");
        if(isoCount>1) throw new IOException("This ZIP contains more than one .iso file; extract the one you want.");

        long data=dataOffset(file,isoLocal,cdOffset);
        if(isoLength<=0 || data>cdOffset-isoLength) throw new IOException("The ISO entry extends past its ZIP data; the download is truncated.");

        String bundled=null;
        if(sumName!=null && sumMethod==0) {
            try {
                long s=dataOffset(file,sumLocal,cdOffset);
                if(s<=cdOffset-sumLength) bundled=pickHash(new String(read(file,s,(int)sumLength),StandardCharsets.US_ASCII),isoName);
            } catch(IOException ignored) { bundled=null; }
        }
        return new IsoImage(data,isoLength,isoName,bundled);
    }

    private static long dataOffset(FileChannel file,long local,long limit) throws IOException {
        if(local<0 || local>limit-30) throw new IOException("A ZIP entry header is outside the archive.");
        byte[] h=read(file,local,30);
        if(le32(h,0)!=0x04034b50L) throw new IOException("A ZIP entry header is damaged.");
        return local+30+le16(h,26)+le16(h,28);
    }

    /** Returns the 64-hex checksum for {@code isoName} from a sha256sum-style text, or the sole hash present. */
    static String pickHash(String text,String isoName) {
        String wanted=isoName==null?"":isoName.substring(isoName.lastIndexOf('/')+1);
        String only=null; int count=0;
        for(String line:text.split("\\r?\\n")) {
            String t=line.trim();
            if(t.length()<64) continue;
            String h=t.substring(0,64).toLowerCase(Locale.ROOT);
            if(!h.matches("[0-9a-f]{64}") || (t.length()>64 && !Character.isWhitespace(t.charAt(64)))) continue;
            String file=t.substring(64).trim();
            if(file.startsWith("*")) file=file.substring(1);
            file=file.substring(file.lastIndexOf('/')+1);
            if(file.equals(wanted)) return h;
            only=h; count++;
        }
        return count==1?only:null;
    }

    /** An InputStream over exactly {@code length} bytes starting at {@code offset}, using positional reads. */
    public InputStream open(FileChannel file) { return new Range(file,offset,length); }

    static final class Range extends InputStream {
        private final FileChannel file; private long at; private final long end;
        Range(FileChannel file,long offset,long length){this.file=file;this.at=offset;this.end=offset+length;}
        @Override public int read() throws IOException {
            byte[] one=new byte[1]; int n=read(one,0,1); return n<0?-1:(one[0]&255);
        }
        @Override public int read(byte[] b,int off,int len) throws IOException {
            if(len==0) return 0;
            if(at>=end) return -1;
            int want=(int)Math.min(len,end-at);
            int n=file.read(ByteBuffer.wrap(b,off,want),at);
            if(n<0) throw new EOFException("The selected file ended before the ISO image did.");
            at+=n; return n;
        }
    }

    private static byte[] read(FileChannel c,long position,int length) throws IOException {
        if(position<0 || length<0 || position>c.size()-length) throw new EOFException("The selected file is truncated.");
        byte[] out=new byte[length]; ByteBuffer b=ByteBuffer.wrap(out); long at=position;
        while(b.hasRemaining()) {
            int n=c.read(b,at);
            if(n<=0) throw new EOFException("Unable to read the selected file.");
            at+=n;
        }
        return out;
    }
    private static int le16(byte[] b,int p){return (b[p]&255)|((b[p+1]&255)<<8);}
    private static long le32(byte[] b,int p){return (b[p]&255L)|((b[p+1]&255L)<<8)|((b[p+2]&255L)<<16)|((b[p+3]&255L)<<24);}
    private static long le64(byte[] b,int p){return le32(b,p)|(le32(b,p+4)<<32);}
}
