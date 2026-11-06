package com.orez.formatter;

import java.io.IOException;

/** Creates a conventional MBR/FAT32 volume and verifies it by reading it back. */
public final class UsbFat32Formatter {
    private static final int SECTOR=512, RESERVED=32, PARTITION_START=2048, SECTORS_PER_CLUSTER=64;
    private UsbFat32Formatter() {}

    public static void format(UsbBot bot, Progress progress) throws IOException {
        long disk=bot.sectors();
        if(disk<=PARTITION_START+RESERVED+4096 || disk>0xffffffffL)
            throw new IOException("This formatter requires a 512-byte-sector USB between 2 GiB and 2 TiB.");
        long volumeSectors=disk-PARTITION_START;
        long fatSectors=1;
        long clusters;
        for(int i=0;i<8;i++){
            clusters=(volumeSectors-RESERVED-2*fatSectors)/SECTORS_PER_CLUSTER;
            long needed=((clusters+2)*4+SECTOR-1)/SECTOR;
            if(needed==fatSectors) break;
            fatSectors=needed;
        }
        clusters=(volumeSectors-RESERVED-2*fatSectors)/SECTORS_PER_CLUSTER;
        if(clusters<65525 || clusters>0x0ffffff5L || fatSectors>0xffffffffL)
            throw new IOException("The USB capacity is outside the supported FAT32 layout.");
        byte[] zero=new byte[UsbBot.MAX_TRANSFER];
        // Remove primary and backup GPT/ISO signatures before writing a new MBR.
        for(long l=0;l<34;l++) {
            bot.write(l,zero,0,SECTOR);
            if(progress!=null) progress.update("Clearing old partition metadata",l+1,34);
        }
        for(long l=Math.max(34,disk-33);l<disk;l++) {
            bot.write(l,zero,0,SECTOR);
            if(progress!=null) progress.update("Clearing backup partition metadata",l-Math.max(34,disk-33)+1,Math.min(33,disk-34));
        }
        if(!bot.sync() && progress!=null)
            progress.update("Drive has no cache-flush command; read-back verification will be used",1,1);

        byte[] mbr=new byte[SECTOR];
        mbr[446]=(byte)0x00; mbr[450]=(byte)0x0c;
        put32(mbr,454,PARTITION_START); put32(mbr,458,volumeSectors);
        mbr[510]=0x55; mbr[511]=(byte)0xaa;
        bot.write(0,mbr,0,SECTOR);

        byte[] boot=new byte[SECTOR];
        boot[0]=(byte)0xeb;boot[1]=0x58;boot[2]=(byte)0x90;
        ascii(boot,3,"MSWIN4.1");
        put16(boot,11,SECTOR);boot[13]=(byte)SECTORS_PER_CLUSTER;
        put16(boot,14,RESERVED);boot[16]=2;put16(boot,17,0);
        put16(boot,19,0);boot[21]=(byte)0xf8;put16(boot,22,0);
        put16(boot,24,63);put16(boot,26,255);put32(boot,28,PARTITION_START);
        put32(boot,32,volumeSectors);put32(boot,36,fatSectors);
        put16(boot,40,0);put16(boot,42,0);put32(boot,44,2);
        put16(boot,48,1);put16(boot,50,6);
        boot[64]=(byte)0x80;boot[66]=0x29;put32(boot,67,(int)(System.currentTimeMillis()/1000));
        ascii(boot,71,"OREZ USB  ");ascii(boot,82,"FAT32   ");
        boot[510]=0x55;boot[511]=(byte)0xaa;
        bot.write(PARTITION_START,boot,0,SECTOR);
        bot.write(PARTITION_START+6,boot,0,SECTOR);

        byte[] fsInfo=new byte[SECTOR];
        put32(fsInfo,0,0x41615252L);put32(fsInfo,484,0x61417272L);
        put32(fsInfo,488,clusters-1);put32(fsInfo,492,3);
        put32(fsInfo,508,0xaa550000L);
        bot.write(PARTITION_START+1,fsInfo,0,SECTOR);
        bot.write(PARTITION_START+7,fsInfo,0,SECTOR);

        byte[] firstFat=new byte[UsbBot.MAX_TRANSFER];
        firstFat[0]=(byte)0xf8;firstFat[1]=(byte)0xff;firstFat[2]=(byte)0xff;firstFat[3]=0x0f;
        firstFat[4]=(byte)0xff;firstFat[5]=(byte)0xff;firstFat[6]=(byte)0xff;firstFat[7]=0x0f;
        firstFat[8]=(byte)0xff;firstFat[9]=(byte)0xff;firstFat[10]=(byte)0xff;firstFat[11]=0x0f;
        long fat1=PARTITION_START+RESERVED, fat2=fat1+fatSectors;
        writeFat(bot,fat1,fatSectors,firstFat,progress,"Initializing FAT 1");
        writeFat(bot,fat2,fatSectors,firstFat,progress,"Initializing FAT 2");
        byte[] root=new byte[SECTOR];
        bot.write(PARTITION_START+RESERVED+2*fatSectors,root,0,SECTOR);
        if(!bot.sync() && progress!=null)
            progress.update("Verifying without device cache-flush support",1,1);

        byte[] verify=new byte[SECTOR];
        bot.read(0,verify,0,SECTOR);
        if(verify[510]!=0x55 || verify[511]!=(byte)0xaa || (verify[450]&255)!=0x0c)
            throw new IOException("MBR read-back verification failed.");
        bot.read(PARTITION_START,verify,0,SECTOR);
        if(verify[510]!=0x55 || verify[511]!=(byte)0xaa || !new String(verify,82,5).equals("FAT32"))
            throw new IOException("FAT32 boot-sector read-back verification failed.");
        bot.read(fat1,verify,0,SECTOR);
        if((verify[0]&255)!=0xf8 || (verify[8]&255)!=0xff)
            throw new IOException("FAT table read-back verification failed.");
        bot.read(fat2,verify,0,SECTOR);
        if((verify[0]&255)!=0xf8 || (verify[8]&255)!=0xff)
            throw new IOException("Second FAT read-back verification failed.");
        if(progress!=null) progress.update("FAT32 format verified",disk,disk);
    }

    private static void writeFat(UsbBot bot,long start,long sectors,byte[] first,Progress p,String label) throws IOException {
        long done=0;
        while(done<sectors){
            int count=(int)Math.min(UsbBot.MAX_TRANSFER/SECTOR,sectors-done);
            byte[] b=new byte[count*SECTOR];
            if(done==0) System.arraycopy(first,0,b,0,first.length);
            bot.write(start+done,b,0,b.length);done+=count;
            if(p!=null)p.update(label,done,sectors);
        }
    }
    private static void ascii(byte[] b,int o,String s){for(int i=0;i<s.length();i++)b[o+i]=(byte)s.charAt(i);}
    private static void put16(byte[] b,int o,long v){b[o]=(byte)v;b[o+1]=(byte)(v>>>8);}
    private static void put32(byte[] b,int o,long v){b[o]=(byte)v;b[o+1]=(byte)(v>>>8);b[o+2]=(byte)(v>>>16);b[o+3]=(byte)(v>>>24);}
    public interface Progress { void update(String phase,long done,long total); }
}
