package com.orez.usb;

import java.io.EOFException;
import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.channels.FileChannel;
import java.nio.charset.StandardCharsets;
import java.util.Arrays;
import java.util.Locale;

/** Read-only validation for x86_64 Linux hybrid installation images. */
public final class HybridIsoValidator {
    private static final int BLOCK = 2048;
    private static final int MAX_DIRECTORY = 16 * 1024 * 1024;

    public static final class Info {
        public final long bytes;
        public final long volumeBlocks;
        public final String filesystem;
        public final boolean hybridMbr, gpt, efiBoot, updateImage;
        Info(long bytes, long blocks, String fs, boolean mbr, boolean gpt, boolean efi) {
            this(bytes,blocks,fs,mbr,gpt,efi,false);
        }
        Info(long bytes, long blocks, String fs, boolean mbr, boolean gpt, boolean efi, boolean update) {
            this.bytes=bytes; this.volumeBlocks=blocks; this.filesystem=fs;
            this.hybridMbr=mbr; this.gpt=gpt; this.efiBoot=efi; this.updateImage=update;
        }
        public String summary() {
            if(updateImage) return filesystem + " · OREZ OS update USB (not bootable — plug it into your running OREZ PC)";
            return filesystem + " · hybrid USB image · " + (efiBoot ? "x86_64 UEFI loader found" : "UEFI loader not confirmed");
        }
    }

    public static Info inspect(FileChannel file) throws IOException {
        return inspect(file,0,file.size());
    }

    /** Validates an ISO stored at {@code base} inside a larger file (for example a stored ZIP entry). */
    public static Info inspect(FileChannel file,long base,long size) throws IOException {
        if(base<0 || size<0 || base>file.size()-size) throw new EOFException("The image region is outside the selected file.");
        Region channel=new Region(file,base,size);
        long length=size;
        if(length<20L*BLOCK || length%512!=0) throw new IOException("The selected file is not a complete sector-aligned installation image.");
        byte[] pvd=read(channel,16L*BLOCK,BLOCK);
        if((pvd[0]&255)!=1 || !ascii(pvd,1,"CD001") || (pvd[6]&255)!=1)
            throw new IOException("No valid ISO9660 primary volume descriptor was found.");
        long volumeBlocks=u32(pvd,80);
        if(volumeBlocks<=16 || volumeBlocks*BLOCK>length+BLOCK)
            throw new IOException("The ISO9660 volume size is invalid or truncated.");

        byte[] mbr=read(channel,0,512), lba1=read(channel,512,512);
        boolean gpt=ascii(lba1,0,"EFI PART");
        boolean hybridMbr=hasMbrPartition(mbr);
        if(!hybridMbr && !gpt && ascii(pvd,40,"OREZ_UPDATE ")) {
            // OREZ update USB: a plain ISO9660 volume that the running OREZ PC mounts and reads.
            Entry root=Entry.from(Arrays.copyOfRange(pvd,156,190));
            Entry manifest=find(channel,root,"orez_update/update.json");
            Entry sums=find(channel,root,"orez_update/SHA256SUMS");
            if(manifest==null || manifest.directory || sums==null || sums.directory || manifest.size<16 || manifest.size>1<<20)
                throw new IOException("This OREZ update image is incomplete (update description or checksums missing).");
            byte[] json=read(channel,manifest.extent*BLOCK,(int)manifest.size);
            if(!new String(json,StandardCharsets.UTF_8).contains("\"schema\": 1"))
                throw new IOException("This OREZ update image uses a format this app does not know.");
            return new Info(length,volumeBlocks,"ISO9660",false,false,false,true);
        }
        if(!hybridMbr && !gpt)
            throw new IOException("This ISO has no recognised hybrid MBR/GPT USB layout. Use the official desktop hybrid ISO, not a netboot or live filesystem archive.");

        boolean bootRecord=false, terminator=false;
        long catalogLba=-1;
        for(int sector=17;sector<64;sector++) {
            byte[] d=read(channel,(long)sector*BLOCK,BLOCK);
            if(!ascii(d,1,"CD001")) break;
            int type=d[0]&255;
            if(type==0 && ascii(d,7,"EL TORITO SPECIFICATION")) {
                bootRecord=true; catalogLba=u32(d,71);
            }
            if(type==255){terminator=true;break;}
        }
        if(!terminator) throw new IOException("The ISO9660 volume descriptor sequence is incomplete.");
        if(!bootRecord || catalogLba<=0 || catalogLba>=length/BLOCK)
            throw new IOException("No valid El Torito boot catalogue was found.");
        byte[] catalog=read(channel,catalogLba*BLOCK,BLOCK);
        if(!validBootCatalog(catalog))
            throw new IOException("The El Torito boot catalogue failed its validation checksum.");

        Entry root=Entry.from(Arrays.copyOfRange(pvd,156,190));
        if(!root.directory) throw new IOException("Invalid ISO root directory.");
        Entry squashfs=find(channel,root,"casper/filesystem.squashfs");
        Entry kernel=find(channel,root,"casper/vmlinuz");
        if(kernel==null) kernel=find(channel,root,"casper/vmlinuz.efi");
        if(squashfs==null || squashfs.directory || kernel==null || kernel.directory)
            throw new IOException("This does not look like a standard OREZ OS / Ubuntu-family desktop installer (missing casper filesystem or kernel).");
        Entry efi=find(channel,root,"EFI/BOOT/BOOTX64.EFI");
        boolean efiBoot=efi!=null && !efi.directory && efi.size>=2;
        if(efiBoot) {
            byte[] mz=read(channel,efi.extent*BLOCK,2);
            efiBoot=mz[0]=='M' && mz[1]=='Z';
        }
        if(!efiBoot)
            throw new IOException("The ISO does not contain the expected x86_64 EFI bootloader. Choose the amd64/x86_64 OREZ OS image.");
        return new Info(length,volumeBlocks,"ISO9660",hybridMbr,gpt,true);
    }

    public static boolean hasMbrPartition(byte[] sector) {
        if(sector==null || sector.length<512 || sector[510]!=0x55 || (sector[511]&255)!=0xaa) return false;
        for(int i=446;i<510;i+=16) {
            int type=sector[i+4]&255;
            long count=u32(sector,i+12);
            if(type!=0 && count>0) return true;
        }
        return false;
    }

    public static boolean validBootCatalog(byte[] b) {
        if(b==null || b.length<64 || (b[0]&255)!=1 || (b[30]&255)!=0x55 || (b[31]&255)!=0xaa) return false;
        int sum=0;
        for(int i=0;i<32;i+=2) sum=(sum+(b[i]&255)+((b[i+1]&255)<<8))&0xffff;
        return sum==0 && ((b[32]&255)==0x88 || (b[32]&255)==0x00);
    }

    private static final class Entry {
        String name;
        long extent,size;
        boolean directory;
        static Entry from(byte[] r) throws IOException {
            if(r.length<34 || (r[0]&255)<34) throw new IOException("Malformed ISO directory record.");
            Entry e=new Entry();
            e.extent=u32(r,2); e.size=u32(r,10); e.directory=(r[25]&2)!=0;
            int n=r[32]&255;
            if(33+n>(r[0]&255) || n==0) throw new IOException("Malformed ISO filename.");
            e.name=decodeName(r,33,n);
            return e;
        }
    }

    private static Entry find(Region c,Entry root,String path) throws IOException {
        Entry current=root;
        for(String part:path.split("/")) {
            if(part.isEmpty()) continue;
            if(!current.directory) return null;
            Entry found=null;
            for(Entry e:children(c,current)) if(e.name.equalsIgnoreCase(part.replace('-','_'))){found=e;break;}
            if(found==null) return null;
            current=found;
        }
        return current;
    }

    private static Entry[] children(Region c,Entry dir) throws IOException {
        if(dir.size<=0 || dir.size>MAX_DIRECTORY || dir.extent<0)
            throw new IOException("An ISO directory has an unsupported size.");
        byte[] data=read(c,dir.extent*BLOCK,(int)dir.size);
        java.util.ArrayList<Entry> out=new java.util.ArrayList<>();
        for(int p=0;p<data.length;) {
            int n=data[p]&255;
            if(n==0){p=((p/BLOCK)+1)*BLOCK;continue;}
            if(n<34 || p+n>data.length) throw new IOException("Malformed ISO directory contents.");
            int nameLen=data[p+32]&255;
            if(nameLen==1 && (data[p+33]==0 || data[p+33]==1)){p+=n;continue;}
            out.add(Entry.from(Arrays.copyOfRange(data,p,p+n)));
            p+=n;
        }
        return out.toArray(new Entry[0]);
    }

    private static String decodeName(byte[] b,int p,int n) {
        String s=new String(b,p,n,StandardCharsets.US_ASCII);
        int version=s.indexOf(';');
        if(version>=0) s=s.substring(0,version);
        while(s.endsWith(".")) s=s.substring(0,s.length()-1);
        return s.toUpperCase(Locale.ROOT);
    }

    private static final class Region {
        final FileChannel file; final long base,size;
        Region(FileChannel file,long base,long size){this.file=file;this.base=base;this.size=size;}
    }

    private static byte[] read(Region c,long position,int length) throws IOException {
        if(position<0 || length<0 || position>c.size-length) throw new EOFException("ISO is truncated.");
        byte[] out=new byte[length];
        ByteBuffer b=ByteBuffer.wrap(out);
        long at=position;
        while(b.hasRemaining()) {
            int n=c.file.read(b,c.base+at);
            if(n<=0) throw new EOFException("Unable to read the selected ISO.");
            at+=n;
        }
        return out;
    }

    private static boolean ascii(byte[] b,int p,String s) {
        if(p<0 || p+s.length()>b.length) return false;
        for(int i=0;i<s.length();i++) if((b[p+i]&255)!=s.charAt(i)) return false;
        return true;
    }
    private static long u32(byte[] b,int p) {
        return (b[p]&255L)|((b[p+1]&255L)<<8)|((b[p+2]&255L)<<16)|((b[p+3]&255L)<<24);
    }
}
