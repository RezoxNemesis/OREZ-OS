package com.orez.usb;

import java.io.IOException;
import java.security.MessageDigest;
import java.util.Locale;

/**
 * Read-only, full-image verification against an already inspected ISO hash.
 * Call only after the user has physically disconnected and reconnected the USB.
 */
final class UsbImageVerifier {
    private static final int SECTOR=512;
    private static final int CHUNK=UsbBot.MAX_TRANSFER;

    interface Reader {
        void read(long lba,byte[] buffer,int offset,int length) throws IOException;
    }
    interface Progress {
        void update(long verifiedBytes,long totalBytes);
    }

    private UsbImageVerifier() {}

    static String verify(Reader reader,long capacityBytes,long imageBytes,
                         String expectedSha256,Progress progress) throws Exception {
        if(reader==null) throw new IOException("USB reader is unavailable.");
        if(imageBytes<=0) throw new IOException("The ISO size is invalid.");
        if(expectedSha256==null || !expectedSha256.matches("(?i)[0-9a-f]{64}"))
            throw new IOException("A valid 64-character ISO SHA-256 is required.");
        if(imageBytes>Long.MAX_VALUE-(SECTOR-1))
            throw new IOException("The ISO size is too large.");
        long paddedBytes=((imageBytes+SECTOR-1)/SECTOR)*SECTOR;
        if(capacityBytes<paddedBytes)
            throw new IOException("The selected USB is too small for this ISO image.");

        MessageDigest digest=MessageDigest.getInstance("SHA-256");
        byte[] buffer=new byte[CHUNK];
        long remaining=imageBytes,lba=0,verified=0;
        while(remaining>0) {
            int actual=(int)Math.min((long)CHUNK,remaining);
            int padded=(actual+SECTOR-1)&~(SECTOR-1);
            reader.read(lba,buffer,0,padded);
            for(int i=actual;i<padded;i++) {
                if(buffer[i]!=0)
                    throw new IOException("USB end-padding mismatch at image byte "+(verified+i)+". Persistent media verification failed.");
            }
            digest.update(buffer,0,actual);
            lba+=padded/SECTOR;
            remaining-=actual;
            verified+=actual;
            if(progress!=null) progress.update(verified,imageBytes);
        }
        String actual=hex(digest.digest());
        if(!actual.equalsIgnoreCase(expectedSha256))
            throw new IOException("Persistent USB SHA-256 mismatch after reconnect. Expected "+
                    expectedSha256.toLowerCase(Locale.ROOT)+" but read "+actual+
                    ". Do not boot from this drive; its stored image differs from the ISO.");
        return actual;
    }

    private static String hex(byte[] bytes) {
        StringBuilder out=new StringBuilder(bytes.length*2);
        for(byte b:bytes) out.append(String.format(Locale.ROOT,"%02x",b&255));
        return out.toString();
    }
}
