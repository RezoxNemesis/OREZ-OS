package com.orez.usb;

import org.junit.Test;
import static org.junit.Assert.*;

public class LiveMonitorClientTest {
    @Test public void acceptsCurrentPairingCodeFormat() {
        assertTrue(LiveMonitorClient.isValidCode(
                "0123456789abcdef0123456789abcdef." +
                "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"));
    }

    @Test public void rejectsMissingOrMalformedCredentials() {
        assertFalse(LiveMonitorClient.isValidCode(null));
        assertFalse(LiveMonitorClient.isValidCode(""));
        assertFalse(LiveMonitorClient.isValidCode("not-a-pairing-code"));
        assertFalse(LiveMonitorClient.isValidCode(
                "0123456789abcdef0123456789abcdef." +
                "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcde"));
        assertFalse(LiveMonitorClient.isValidCode(
                "0123456789abcdef0123456789abcdeg." +
                "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"));
    }

    @Test public void rejectsExtraPairingCodeParts() {
        assertFalse(LiveMonitorClient.isValidCode(
                "0123456789abcdef0123456789abcdef." +
                "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef.extra"));
    }
}
