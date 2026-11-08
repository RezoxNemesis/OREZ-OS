package com.orez.usb;

import android.hardware.usb.*;
import java.io.IOException;

/** Strict USB Mass Storage Bulk-Only Transport, SCSI transparent command set, LUN 0. */
public final class UsbBot implements AutoCloseable {
    public static final int MAX_TRANSFER = 16 * 1024;
    private static final int BLOCK = 512;
    private final UsbDeviceConnection connection;
    private final UsbInterface usbInterface;
    private final UsbEndpoint bulkIn, bulkOut;
    private int tag = 1;
    private boolean failed, closed, cacheFlushSupported = true;
    private long sectors;

    public static boolean supports(UsbDevice device) {
        for (int i=0;i<device.getInterfaceCount();i++) {
            UsbInterface face=device.getInterface(i);
            if(face.getInterfaceClass()==8 && face.getInterfaceSubclass()==6 && face.getInterfaceProtocol()==0x50) {
                boolean in=false,out=false;
                for(int j=0;j<face.getEndpointCount();j++) {
                    UsbEndpoint ep=face.getEndpoint(j);
                    if(ep.getType()==UsbConstants.USB_ENDPOINT_XFER_BULK) {
                        if(ep.getDirection()==UsbConstants.USB_DIR_IN) in=true;
                        if(ep.getDirection()==UsbConstants.USB_DIR_OUT) out=true;
                    }
                }
                if(in && out) return true;
            }
        }
        return false;
    }

    public UsbBot(UsbManager manager,UsbDevice device) throws IOException {
        UsbInterface selected=null;
        UsbEndpoint in=null,out=null;
        for(int i=0;i<device.getInterfaceCount();i++) {
            UsbInterface face=device.getInterface(i);
            if(face.getInterfaceClass()!=8 || face.getInterfaceSubclass()!=6 || face.getInterfaceProtocol()!=0x50) continue;
            UsbEndpoint candidateIn=null,candidateOut=null;
            for(int j=0;j<face.getEndpointCount();j++) {
                UsbEndpoint ep=face.getEndpoint(j);
                if(ep.getType()==UsbConstants.USB_ENDPOINT_XFER_BULK) {
                    if(ep.getDirection()==UsbConstants.USB_DIR_IN) candidateIn=ep;
                    if(ep.getDirection()==UsbConstants.USB_DIR_OUT) candidateOut=ep;
                }
            }
            if(candidateIn!=null && candidateOut!=null) { selected=face;in=candidateIn;out=candidateOut;break; }
        }
        if(selected==null) throw new IOException("This USB does not expose Bulk-Only Transport mass storage.");
        usbInterface=selected; bulkIn=in; bulkOut=out;
        connection=manager.openDevice(device);
        if(connection==null) throw new IOException("Android did not grant access to this USB device.");
        if(!connection.claimInterface(usbInterface,true)) {
            connection.close();
            throw new IOException("Could not claim the USB interface. Close file managers and reconnect the drive.");
        }
        try {
            byte[] capacity=new byte[8];
            byte[] cdb=new byte[10];cdb[0]=0x25;
            command(cdb,capacity,true);
            long last=be32(capacity,0), blockSize=be32(capacity,4);
            if(last==0xffffffffL) throw new IOException("USB drives of 2 TiB or larger are not supported.");
            if(blockSize!=BLOCK) throw new IOException("This release supports 512-byte USB sectors only; this drive reports "+blockSize+".");
            sectors=last+1;
            if(sectors<2048) throw new IOException("USB device reports an invalid or unusually small capacity.");
            preflight();
        } catch(IOException e) {
            close();
            throw e;
        }
    }

    public long sectors(){return sectors;}
    public long capacityBytes(){return sectors*BLOCK;}

    /** Read-only BOT check; no test pattern or destructive probe is issued. */
    public void preflight() throws IOException {
        byte[] b=new byte[BLOCK];
        read(0,b,0,BLOCK);
        read(sectors-1,b,0,BLOCK);
    }

    public synchronized void write(long lba,byte[] data,int offset,int length) throws IOException {
        transfer(lba,data,offset,length,false);
    }
    public synchronized void read(long lba,byte[] data,int offset,int length) throws IOException {
        transfer(lba,data,offset,length,true);
    }

    private void transfer(long lba,byte[] data,int offset,int length,boolean read) throws IOException {
        ensureUsable();
        if(data==null || offset<0 || length<=0 || offset>data.length-length || length%BLOCK!=0)
            throw new IOException("Invalid sector transfer buffer.");
        long blocks=length/BLOCK;
        if(lba<0 || blocks>sectors || lba>sectors-blocks)
            throw new IOException("A USB sector request is outside the selected drive.");
        int position=0;
        while(position<length) {
            int bytes=Math.min(MAX_TRANSFER,length-position);
            byte[] part=new byte[bytes];
            if(!read) System.arraycopy(data,offset+position,part,0,bytes);
            byte[] cdb=new byte[10];
            cdb[0]=(byte)(read?0x28:0x2a);
            putBe32(cdb,2,lba+(position/BLOCK));
            int count=bytes/BLOCK;
            cdb[7]=(byte)(count>>>8);cdb[8]=(byte)count;
            command(cdb,part,read);
            if(read) System.arraycopy(part,0,data,offset+position,bytes);
            position+=bytes;
        }
    }

    /**
     * Flushes the device write cache when supported. Some flash controllers return
     * ILLEGAL REQUEST for SYNCHRONIZE CACHE; in that case callers must still perform
     * a full read-back and advise a physical eject/reconnect before booting.
     */
    public synchronized boolean sync() throws IOException {
        if(!cacheFlushSupported) return false;
        byte[] cdb=new byte[10];cdb[0]=0x35;
        try {
            command(cdb,null,false);
            return true;
        } catch(ScsiCheckCondition e) {
            if(ScsiSense.isUnsupportedCacheFlush(e.sense.senseKey,e.sense.asc)) {
                cacheFlushSupported=false;
                return false;
            }
            throw e;
        }
    }

    private void command(byte[] cdb,byte[] data,boolean read) throws IOException {
        commandInternal(cdb,data,read,true);
    }

    private void commandInternal(byte[] cdb,byte[] data,boolean read,boolean allowSense) throws IOException {
        ensureUsable();
        if(cdb==null || cdb.length<1 || cdb.length>16) throw new IOException("Invalid SCSI command.");
        int size=data==null?0:data.length;
        if(size>MAX_TRANSFER) throw new IOException("SCSI transfer exceeds 16 KiB.");
        int current=tag++;
        byte[] cbw=new byte[31];
        putLe32(cbw,0,0x43425355L);
        putLe32(cbw,4,current&0xffffffffL);
        putLe32(cbw,8,size);
        cbw[12]=(byte)(read?0x80:0);
        cbw[14]=(byte)cdb.length;
        System.arraycopy(cdb,0,cbw,15,cdb.length);
        int sent=bulkFully(bulkOut,cbw,0,cbw.length,10000);
        if(sent!=31) throw transportFailure("USB command block returned "+sent+" of 31 bytes for "+describe(cdb)+".");
        if(size>0) {
            int actual=bulkFully(read?bulkIn:bulkOut,data,0,size,30000);
            if(actual!=size) throw transportFailure((read?"USB read":"USB write")+" data stage returned "+actual+" of "+size+" bytes for "+describe(cdb)+".");
        }
        byte[] csw=new byte[13];
        int got=bulkFully(bulkIn,csw,0,csw.length,30000);
        if(got!=13) {
            // USB Mass Storage BOT 6.7.2/6.7.3: when the status stage stalls the host clears
            // the bulk-in halt and reads the status block once more. This re-reads the
            // drive's verdict on the same command; it never re-sends the data, and the
            // full read-back still compares every byte afterwards.
            int first=got;
            if(clearHalt(bulkIn)) got=bulkFully(bulkIn,csw,0,csw.length,30000);
            if(got!=13) throw transportFailure("USB completion block returned "+first+" of 13 bytes for "+describe(cdb)+
                (got==first?"":", and "+got+" after clearing the endpoint stall")+".");
            statusRecoveries++;
        }
        if(le32(csw,0)!=0x53425355L || le32(csw,4)!=(current&0xffffffffL))
            throw transportFailure("USB completion signature or tag is invalid for "+describe(cdb)+".");
        long residue=le32(csw,8);
        int status=csw[12]&255;
        if(status==1) {
            if(!allowSense) {
                failed=true;
                throw new IOException("The drive also rejected SCSI REQUEST SENSE after "+describe(cdb)+". No retry was attempted.");
            }
            ScsiSense.Info sense;
            try {
                sense=requestSense();
            } catch(IOException e) {
                failed=true;
                throw new IOException(describe(cdb)+" was rejected (CHECK CONDITION), and REQUEST SENSE failed: "+e.getMessage());
            }
            throw new ScsiCheckCondition(describe(cdb),sense);
        }
        if(status!=0) throw transportFailure("USB Mass Storage reported phase error during "+describe(cdb)+".");
        if(residue!=0) throw transportFailure("USB reports "+residue+" untransferred bytes during "+describe(cdb)+".");
    }

    private ScsiSense.Info requestSense() throws IOException {
        byte[] cdb=new byte[6];cdb[0]=0x03;cdb[4]=18;
        byte[] response=new byte[18];
        commandInternal(cdb,response,true,false);
        return ScsiSense.decode(response);
    }

    private static String describe(byte[] cdb) {
        int op=cdb[0]&255;
        if(op==0x25) return "SCSI READ CAPACITY(10)";
        if(op==0x28 || op==0x2a)
            return (op==0x28?"SCSI READ(10)":"SCSI WRITE(10)")+" at LBA "+be32(cdb,2);
        if(op==0x35) return "SCSI SYNCHRONIZE CACHE(10)";
        if(op==0x03) return "SCSI REQUEST SENSE";
        return "SCSI opcode 0x"+String.format(java.util.Locale.ROOT,"%02X",op);
    }

    private static final class ScsiCheckCondition extends IOException {
        final ScsiSense.Info sense;
        ScsiCheckCondition(String command,ScsiSense.Info sense) {
            super(command+" was rejected by the drive: "+sense.description()+". No automatic retry was attempted.");
            this.sense=sense;
        }
    }

    /** Android bulkTransfer may legally complete only part of a requested data stage. */
    private int bulkFully(UsbEndpoint endpoint,byte[] buffer,int offset,int length,int timeout) {
        int completed=0;
        while(completed<length) {
            int n=connection.bulkTransfer(endpoint,buffer,offset+completed,length-completed,timeout);
            if(n<=0) return completed==0?n:completed;
            completed+=n;
        }
        return completed;
    }

    private int statusRecoveries;
    /** Number of commands whose status block was recovered after an endpoint stall. */
    public int statusRecoveries(){return statusRecoveries;}

    /** Standard CLEAR_FEATURE(ENDPOINT_HALT) request to one endpoint. */
    private boolean clearHalt(UsbEndpoint endpoint) {
        return connection.controlTransfer(0x02,0x01,0,endpoint.getAddress(),null,0,5000)>=0;
    }

    private IOException transportFailure(String message) {
        failed=true;
        return new IOException(message+" The USB may be incomplete. Reconnect it and restart the entire write; no automatic retry is made.");
    }
    private void ensureUsable() throws IOException {
        if(closed) throw new IOException("USB connection is closed.");
        if(failed) throw new IOException("USB transport has failed; no further commands will be issued.");
    }

    @Override public synchronized void close() {
        if(closed)return;
        closed=true;
        try { connection.releaseInterface(usbInterface); } catch(Exception ignored) {}
        connection.close();
    }

    private static long be32(byte[] b,int p) {
        return ((long)(b[p]&255)<<24)|((long)(b[p+1]&255)<<16)|((long)(b[p+2]&255)<<8)|(b[p+3]&255L);
    }
    private static void putBe32(byte[] b,int p,long value) {
        b[p]=(byte)(value>>>24);b[p+1]=(byte)(value>>>16);b[p+2]=(byte)(value>>>8);b[p+3]=(byte)value;
    }
    private static long le32(byte[] b,int p) {
        return (b[p]&255L)|((b[p+1]&255L)<<8)|((b[p+2]&255L)<<16)|((b[p+3]&255L)<<24);
    }
    private static void putLe32(byte[] b,int p,long value) {
        b[p]=(byte)value;b[p+1]=(byte)(value>>>8);b[p+2]=(byte)(value>>>16);b[p+3]=(byte)(value>>>24);
    }
}
