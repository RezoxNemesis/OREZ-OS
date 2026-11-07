package com.orez.usb;

import org.junit.Test;
import static org.junit.Assert.*;
import java.io.IOException;
import java.security.MessageDigest;
import java.util.Arrays;

public class UsbImageVerifierTest {
    private static String hash(byte[] bytes) throws Exception {
        byte[] h=MessageDigest.getInstance("SHA-256").digest(bytes);
        StringBuilder s=new StringBuilder();
        for(byte b:h)s.append(String.format(java.util.Locale.ROOT,"%02x",b&255));
        return s.toString();
    }

    @Test public void acceptsExactImageReadAfterReconnect() throws Exception {
        byte[] image=new byte[700];
        for(int i=0;i<image.length;i++) image[i]=(byte)(i*31);
        byte[] media=new byte[1024];
        System.arraycopy(image,0,media,0,image.length);
        final long[] read={0};
        String result=UsbImageVerifier.verify((lba,b,o,n)->{
            System.arraycopy(media,(int)(lba*512),b,o,n);
            read[0]+=n;
        },media.length,image.length,hash(image),null);
        assertEquals(hash(image),result);
        assertEquals(1024,read[0]);
    }

    @Test public void rejectsPersistentDataMismatch() throws Exception {
        byte[] image=new byte[1024];
        byte[] media=Arrays.copyOf(image,image.length);
        media[700]=1;
        try {
            UsbImageVerifier.verify((lba,b,o,n)->System.arraycopy(media,(int)(lba*512),b,o,n),
                    media.length,image.length,hash(image),null);
            fail("Expected mismatch");
        } catch(IOException expected) {
            assertTrue(expected.getMessage().contains("SHA-256 mismatch"));
        }
    }

    @Test public void rejectsNonZeroSectorPadding() throws Exception {
        byte[] image=new byte[513];
        byte[] media=new byte[1024];
        media[600]=7;
        try {
            UsbImageVerifier.verify((lba,b,o,n)->System.arraycopy(media,(int)(lba*512),b,o,n),
                    media.length,image.length,hash(image),null);
            fail("Expected padding mismatch");
        } catch(IOException expected) {
            assertTrue(expected.getMessage().contains("padding mismatch"));
        }
    }

    @Test public void rejectsTooSmallUsbBeforeReading() throws Exception {
        byte[] image=new byte[513];
        try {
            UsbImageVerifier.verify((lba,b,o,n)->fail("Reader must not run"),
                    512,image.length,hash(image),null);
            fail("Expected capacity error");
        } catch(IOException expected) {
            assertTrue(expected.getMessage().contains("too small"));
        }
    }
}
