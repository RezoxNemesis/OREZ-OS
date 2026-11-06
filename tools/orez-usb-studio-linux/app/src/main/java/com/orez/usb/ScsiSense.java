package com.orez.usb;

/** Small pure-Java decoder for SCSI REQUEST SENSE response data. */
final class ScsiSense {
    private ScsiSense() {}

    static final class Info {
        final int senseKey, asc, ascq;
        Info(int key,int asc,int ascq) {
            this.senseKey=key&0x0f; this.asc=asc&0xff; this.ascq=ascq&0xff;
        }
        String description() {
            return name(senseKey)+" (sense 0x"+hex(senseKey)+", ASC/ASCQ 0x"+hex(asc)+"/0x"+hex(ascq)+")";
        }
    }

    static Info decode(byte[] response) {
        if(response==null || response.length<4) throw new IllegalArgumentException("SCSI sense response is too short.");
        int format=response[0]&0x7f;
        if(format==0x70 || format==0x71) {
            if(response.length<14) throw new IllegalArgumentException("Fixed-format SCSI sense response is truncated.");
            return new Info(response[2],response[12],response[13]);
        }
        if(format==0x72 || format==0x73)
            return new Info(response[1],response[2],response[3]);
        throw new IllegalArgumentException("Unrecognised SCSI sense response format 0x"+hex(format)+".");
    }

    static boolean isUnsupportedCacheFlush(int senseKey,int asc) {
        return (senseKey&0x0f)==0x05 && ((asc&0xff)==0x20 || (asc&0xff)==0x24);
    }

    private static String name(int key) {
        switch(key&0x0f) {
            case 0x00:return "NO SENSE";
            case 0x01:return "RECOVERED ERROR";
            case 0x02:return "NOT READY";
            case 0x03:return "MEDIUM ERROR";
            case 0x04:return "HARDWARE ERROR";
            case 0x05:return "ILLEGAL REQUEST";
            case 0x06:return "UNIT ATTENTION";
            case 0x07:return "DATA PROTECT (write-protected)";
            case 0x0b:return "ABORTED COMMAND";
            default:return "SENSE KEY 0x"+hex(key);
        }
    }
    private static String hex(int n) {
        return String.format(java.util.Locale.ROOT,"%02X",n&0xff);
    }
}
