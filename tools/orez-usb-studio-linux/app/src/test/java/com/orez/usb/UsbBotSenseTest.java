package com.orez.usb;

import org.junit.Test;
import static org.junit.Assert.*;

public class UsbBotSenseTest {
    @Test public void decodesFixedFormatSense() {
        byte[] data=new byte[18];
        data[0]=0x70; data[2]=0x05; data[12]=0x20; data[13]=0x00;
        ScsiSense.Info info=ScsiSense.decode(data);
        assertEquals(0x05,info.senseKey);
        assertEquals(0x20,info.asc);
        assertTrue(info.description().contains("ILLEGAL REQUEST"));
    }

    @Test public void decodesDescriptorFormatSense() {
        byte[] data=new byte[18];
        data[0]=0x72; data[1]=0x07; data[2]=0x27; data[3]=0x00;
        ScsiSense.Info info=ScsiSense.decode(data);
        assertEquals(0x07,info.senseKey);
        assertEquals(0x27,info.asc);
        assertTrue(info.description().contains("write-protected"));
    }

    @Test public void onlyRecognisesUnsupportedCommandOrFieldForCacheFlush() {
        assertTrue(ScsiSense.isUnsupportedCacheFlush(0x05,0x20));
        assertTrue(ScsiSense.isUnsupportedCacheFlush(0x05,0x24));
        assertFalse(ScsiSense.isUnsupportedCacheFlush(0x07,0x27));
        assertFalse(ScsiSense.isUnsupportedCacheFlush(0x03,0x11));
        assertFalse(ScsiSense.isUnsupportedCacheFlush(0x05,0x26));
    }

    @Test(expected=IllegalArgumentException.class)
    public void rejectsTruncatedFixedFormatSense() {
        ScsiSense.decode(new byte[]{0x70,0x00,0x05,0x00});
    }
}
