package com.orez.usb;

import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.app.Service;
import android.content.Intent;
import android.content.pm.ServiceInfo;
import android.hardware.usb.UsbDevice;
import android.hardware.usb.UsbManager;
import android.net.Uri;
import android.os.Build;
import android.os.IBinder;
import android.os.PowerManager;
import android.os.ParcelFileDescriptor;
import android.os.SystemClock;
import java.io.FileInputStream;
import java.io.InputStream;
import java.io.IOException;
import java.nio.channels.FileChannel;
import java.security.MessageDigest;
import java.util.Locale;
import org.json.JSONObject;

public final class WriteService extends Service {
    public static final String ACTION_START="com.orez.usb.START";
    public static final String ACTION_CANCEL="com.orez.usb.CANCEL";
    public static volatile boolean running=false, cancelled=false, success=false;
    public static volatile String phase="Ready", detail="Choose a Linux ISO and a blank USB drive.";
    public static volatile long done=0,total=0;
    public static volatile String monitorState="Disabled";
    public static volatile boolean checksumMatched=false;
    private volatile boolean monitorActive=false;
    private Thread monitorThread;
    private LiveMonitorClient monitorClient;
    private String reportIsoSha256="", reportUsbProduct="USB mass storage";
    private long reportIsoBytes=0, reportUsbBytes=0;
    private int reportUsbVid=0, reportUsbPid=0;
    private static final String CHANNEL="orez_linux_writer";
    private static final int NOTIFICATION_ID=730;
    private PowerManager.WakeLock wakeLock;
    private Thread worker;
    private long lastNotificationAt=0;

    @Override public IBinder onBind(Intent intent){return null;}

    @Override public int onStartCommand(Intent intent,int flags,int startId) {
        if(intent==null) return START_NOT_STICKY;
        if(ACTION_CANCEL.equals(intent.getAction())) {
            cancelled=true;
            setStatus("Cancelling","Stopping safely at the next sector boundary.",done,total);
            return START_NOT_STICKY;
        }
        if(!ACTION_START.equals(intent.getAction()) || running) return START_NOT_STICKY;

        UsbDevice device=(UsbDevice)intent.getParcelableExtra("usbDevice");
        Uri uri=intent.getParcelableExtra("isoUri");
        String expected=intent.getStringExtra("expectedSha256");
        long expectedBytes=intent.getLongExtra("isoBytes",-1);
        String pairCode=intent.getStringExtra("liveMonitorPairCode");
        intent.removeExtra("liveMonitorPairCode");
        if(pairCode!=null && !pairCode.trim().isEmpty() && !LiveMonitorClient.isValidCode(pairCode)) {
            phase="Stopped before USB writing"; detail="The live-monitor pairing code is invalid. No write was started.";
            stopSelf(startId); return START_NOT_STICKY;
        }
        if(device==null || uri==null || expected==null || !expected.matches("(?i)[0-9a-f]{64}") || expectedBytes<=0) {
            phase="Stopped before USB writing"; detail="The reviewed ISO or USB details are missing. No write was started.";
            stopSelf(startId); return START_NOT_STICKY;
        }

        cancelled=false; success=false; running=true; done=0; total=expectedBytes;
        reportIsoSha256=expected.toLowerCase(Locale.ROOT); reportIsoBytes=expectedBytes;
        reportUsbProduct=device.getProductName()==null?"USB mass storage":device.getProductName();
        reportUsbVid=device.getVendorId(); reportUsbPid=device.getProductId(); reportUsbBytes=0;
        checksumMatched=false;
        monitorState=(pairCode==null || pairCode.trim().isEmpty())?"Disabled":"Starting";
        phase="Starting"; detail="Checking the ISO and reviewed USB before writing.";
        createChannel();
        if(Build.VERSION.SDK_INT>=29) startForeground(NOTIFICATION_ID,notification(),ServiceInfo.FOREGROUND_SERVICE_TYPE_CONNECTED_DEVICE);
        else startForeground(NOTIFICATION_ID,notification());
        try {
            PowerManager pm=(PowerManager)getSystemService(POWER_SERVICE);
            wakeLock=pm.newWakeLock(PowerManager.PARTIAL_WAKE_LOCK,"OREZ:USBImageWriter");
            wakeLock.acquire(4L*60L*60L*1000L);
        } catch(Exception ignored) {}

        Runnable startWriter=()->{
            worker=new Thread(()->runWriter(device,uri,expected.toLowerCase(Locale.ROOT),expectedBytes),"orez-linux-image-writer");
            worker.start();
        };
        if(pairCode!=null && !pairCode.trim().isEmpty()) {
            try { startLiveMonitor(pairCode,startWriter); }
            catch(Exception e) {
                running=false; phase="Stopped before USB writing";
                detail="Live-monitor setup failed; no USB write was started. "+e.getMessage();
                updateNotification(true); stopForeground(STOP_FOREGROUND_REMOVE); stopSelf(startId);
                return START_NOT_STICKY;
            }
        } else {
            startWriter.run();
        }
        return START_NOT_STICKY;
    }

    private void runWriter(UsbDevice reviewed,Uri uri,String expected,long expectedBytes) {
        UsbBot bot=null;
        try {
            checkCancelled();
            UsbManager manager=(UsbManager)getSystemService(USB_SERVICE);
            UsbDevice current=manager.getDeviceList().get(reviewed.getDeviceName());
            if(current==null || current.getDeviceId()!=reviewed.getDeviceId() ||
                current.getVendorId()!=reviewed.getVendorId() || current.getProductId()!=reviewed.getProductId() ||
                !manager.hasPermission(current))
                throw new IOException("The reviewed USB is no longer connected or its permission changed. Select it again.");

            setStatus("Validating Linux ISO","Checking ISO9660, El Torito, hybrid partition map and x86_64 EFI loader.",0,expectedBytes);
            try(ParcelFileDescriptor pfd=getContentResolver().openFileDescriptor(uri,"r");
                FileInputStream file=new FileInputStream(pfd.getFileDescriptor())) {
                if(file.getChannel().size()!=expectedBytes) throw new IOException("The ISO size changed after review.");
                HybridIsoValidator.Info info=HybridIsoValidator.inspect(file.getChannel());
                if(info.bytes!=expectedBytes) throw new IOException("The ISO size changed during inspection.");
            }

            setStatus("Checking SHA-256","Hashing the complete ISO before allowing any USB write.",0,expectedBytes);
            String initialHash=hashSource(uri,expectedBytes);
            if(!initialHash.equals(expected))
                throw new IOException("SHA-256 does not match the official checksum you entered. The USB has not been written.");
            checksumMatched=true;

            checkCancelled();
            setStatus("Opening reviewed USB","Checking the USB again; no formatting or write probe is used.",0,expectedBytes);
            bot=new UsbBot(manager,current);
            long paddedBytes=((expectedBytes+511L)/512L)*512L;
            reportUsbBytes=bot.capacityBytes();
            if(bot.capacityBytes()<paddedBytes)
                throw new IOException("The selected USB is too small. ISO needs "+paddedBytes+" bytes; USB has "+bot.capacityBytes()+" bytes.");
            bot.preflight();

            setStatus("Writing raw Linux image","Writing the original hybrid ISO from USB sector zero. Do not disconnect the OTG adapter.",0,expectedBytes);
            MessageDigest sourceDigest=sha256();
            try(InputStream in=getContentResolver().openInputStream(uri)) {
                if(in==null) throw new IOException("Cannot reopen the selected ISO.");
                byte[] buffer=new byte[UsbBot.MAX_TRANSFER];
                long remaining=expectedBytes,lba=0,offset=0;
                while(remaining>0) {
                    checkCancelled();
                    int actual=(int)Math.min(buffer.length,remaining);
                    readFully(in,buffer,actual);
                    sourceDigest.update(buffer,0,actual);
                    int padded=(actual+511)&~511;
                    for(int i=actual;i<padded;i++) buffer[i]=0;
                    bot.write(lba,buffer,0,padded);
                    lba+=padded/512; offset+=actual; remaining-=actual;
                    setStatus("Writing raw Linux image","Writing "+formatBytes(offset)+" of "+formatBytes(expectedBytes),offset,expectedBytes);
                    checkStillAttached(manager,reviewed);
                }
                if(in.read()!=-1) throw new IOException("The selected ISO grew while it was being written. USB is incomplete.");
            }
            String writtenSourceHash=hex(sourceDigest.digest());
            if(!writtenSourceHash.equals(expected) || !writtenSourceHash.equals(initialHash))
                throw new IOException("The ISO changed during writing. USB is incomplete and must be rewritten from the beginning.");

            checkCancelled();
            setStatus("Flushing USB cache","Waiting for the drive to commit the image.",expectedBytes,expectedBytes);
            bot.sync();

            setStatus("Reading back USB","Comparing every written byte against the original ISO.",0,expectedBytes);
            MessageDigest sourceVerify=sha256(),deviceVerify=sha256();
            try(InputStream in=getContentResolver().openInputStream(uri)) {
                if(in==null) throw new IOException("Cannot reopen the ISO for read-back comparison.");
                byte[] expectedBuffer=new byte[UsbBot.MAX_TRANSFER];
                byte[] deviceBuffer=new byte[UsbBot.MAX_TRANSFER];
                long remaining=expectedBytes,lba=0,offset=0;
                while(remaining>0) {
                    checkCancelled();
                    int actual=(int)Math.min(expectedBuffer.length,remaining);
                    readFully(in,expectedBuffer,actual);
                    int padded=(actual+511)&~511;
                    for(int i=actual;i<padded;i++) expectedBuffer[i]=0;
                    bot.read(lba,deviceBuffer,0,padded);
                    for(int i=0;i<actual;i++) {
                        if(expectedBuffer[i]!=deviceBuffer[i])
                            throw new IOException("Read-back mismatch at image byte "+(offset+i)+". USB is not verified; do not boot from it.");
                    }
                    for(int i=actual;i<padded;i++) {
                        if(deviceBuffer[i]!=0)
                            throw new IOException("Read-back padding mismatch near the end of the ISO. USB is not verified.");
                    }
                    sourceVerify.update(expectedBuffer,0,actual);
                    deviceVerify.update(deviceBuffer,0,actual);
                    lba+=padded/512; offset+=actual; remaining-=actual;
                    setStatus("Reading back USB","Verified "+formatBytes(offset)+" of "+formatBytes(expectedBytes),offset,expectedBytes);
                    checkStillAttached(manager,reviewed);
                }
                if(in.read()!=-1) throw new IOException("The source ISO changed size during read-back verification.");
            }
            String sourceHash=hex(sourceVerify.digest()),usbHash=hex(deviceVerify.digest());
            if(!sourceHash.equals(expected) || !usbHash.equals(expected) || !sourceHash.equals(usbHash))
                throw new IOException("The full USB read-back SHA-256 does not match the ISO. USB is not verified.");

            success=true;
            setStatus("Complete","Raw ISO write and full USB read-back SHA-256 verification passed. Safely eject the USB before moving it to your PC.",expectedBytes,expectedBytes);
        } catch(Exception e) {
            success=false;
            String msg=e.getMessage()==null?e.toString():e.getMessage();
            if(cancelled) setStatus("Cancelled — USB incomplete","The write was cancelled. Do not boot from this USB; start again from sector zero. "+msg,done,total);
            else setStatus("Failed — USB not verified",msg+" No automatic retry was attempted. If writing had started, recreate the USB from the beginning.",done,total);
        } finally {
            if(bot!=null) bot.close();
            running=false;
            stopLiveMonitor();
            if(wakeLock!=null && wakeLock.isHeld()) wakeLock.release();
            updateNotification(true);
            stopForeground(STOP_FOREGROUND_DETACH);
            stopSelf();
        }
    }

    private void startLiveMonitor(String pairingCode,Runnable onConnected) throws IOException {
        monitorClient=new LiveMonitorClient(pairingCode);
        monitorActive=true;
        monitorState="Connecting…";
        monitorThread=new Thread(()->{
            LiveMonitorClient client=monitorClient;
            boolean connected=false;
            try {
                // Require one successful authenticated report before any USB sector is written.
                client.report(buildMonitorStatus());
                connected=true;
                monitorState="Connected · "+client.shortSessionId();
                onConnected.run();
            } catch(Exception e) {
                running=false;
                success=false;
                phase="Stopped before USB writing";
                detail="Live monitoring could not be established. The USB has not been changed. "+
                        (e.getMessage()==null?"Connection unavailable":e.getMessage());
                monitorState="Connection failed";
                updateNotification(true);
                stopForeground(STOP_FOREGROUND_REMOVE);
                stopSelf();
            }

            while(connected && monitorActive) {
                try { Thread.sleep(10000); }
                catch(InterruptedException e) { break; }
                if(!monitorActive) break;
                try {
                    client.report(buildMonitorStatus());
                    monitorState="Connected · "+client.shortSessionId();
                } catch(Exception e) {
                    String reason=e.getMessage()==null?"Connection unavailable":e.getMessage();
                    monitorState="Offline · "+reason;
                    // The authorized local USB job continues even if a later report fails.
                }
            }

            if(connected) {
                try {
                    client.report(buildMonitorStatus());
                    monitorState="Final status sent";
                } catch(Exception e) {
                    monitorState="Final report unavailable · "+(e.getMessage()==null?"connection error":e.getMessage());
                }
            }
            client.close();
            if(monitorClient==client) monitorClient=null;
        },"orez-linux-live-monitor");
        monitorThread.setDaemon(true);
        monitorThread.start();
    }

    private JSONObject buildMonitorStatus() throws Exception {
        return new JSONObject()
            .put("version","0.3.1")
            .put("phase",phase)
            .put("detail",detail)
            .put("running",running)
            .put("success",success)
            .put("isoSha256",reportIsoSha256)
            .put("isoBytes",reportIsoBytes)
            .put("targetArchitecture","x86_64")
            .put("usbProduct",reportUsbProduct)
            .put("usbVid",reportUsbVid)
            .put("usbPid",reportUsbPid)
            .put("usbBytes",reportUsbBytes)
            .put("done",done)
            .put("total",total)
            .put("checksumMatch",checksumMatched)
            .put("checksumSource",checksumMatched?"user-provided official SHA256SUMS":"");
    }

    private void stopLiveMonitor() {
        monitorActive=false;
        Thread t=monitorThread;
        if(t!=null) {
            t.interrupt();
            try { t.join(2000); } catch(InterruptedException e) { Thread.currentThread().interrupt(); }
        }
    }

    private void checkCancelled() throws IOException {
        if(cancelled || Thread.currentThread().isInterrupted()) throw new IOException("Cancellation requested.");
    }
    private void checkStillAttached(UsbManager manager,UsbDevice reviewed) throws IOException {
        UsbDevice d=manager.getDeviceList().get(reviewed.getDeviceName());
        if(d==null || d.getDeviceId()!=reviewed.getDeviceId() ||
           d.getVendorId()!=reviewed.getVendorId() || d.getProductId()!=reviewed.getProductId())
            throw new IOException("The selected USB was disconnected or changed.");
    }

    private String hashSource(Uri uri,long size) throws Exception {
        MessageDigest digest=sha256();
        try(InputStream in=getContentResolver().openInputStream(uri)) {
            if(in==null) throw new IOException("Cannot read the selected ISO.");
            byte[] b=new byte[256*1024]; long count=0; int n;
            while((n=in.read(b))!=-1) {
                checkCancelled(); digest.update(b,0,n); count+=n;
                if(count>size) throw new IOException("The ISO size changed during checksum calculation.");
                setStatus("Checking SHA-256","Hashed "+formatBytes(count)+" of "+formatBytes(size),count,size);
            }
            if(count!=size) throw new IOException("The ISO was truncated while calculating SHA-256.");
        }
        return hex(digest.digest());
    }

    private static void readFully(InputStream in,byte[] b,int n) throws IOException {
        int p=0;
        while(p<n) {
            int got=in.read(b,p,n-p);
            if(got<0) throw new IOException("The ISO ended unexpectedly. USB is incomplete if writing had started.");
            if(got==0) continue;
            p+=got;
        }
    }

    private void setStatus(String p,String d,long completed,long maximum) {
        phase=p; detail=d; done=completed; total=maximum; updateNotification(false);
    }
    private void createChannel() {
        if(Build.VERSION.SDK_INT>=26) {
            NotificationChannel c=new NotificationChannel(CHANNEL,"Linux USB image writing",NotificationManager.IMPORTANCE_LOW);
            c.setDescription("Progress and completion state for OREZ USB Studio.");
            ((NotificationManager)getSystemService(NOTIFICATION_SERVICE)).createNotificationChannel(c);
        }
    }
    private Notification notification() {
        Intent open=new Intent(this,MainActivity.class);
        PendingIntent pi=PendingIntent.getActivity(this,0,open,PendingIntent.FLAG_UPDATE_CURRENT|PendingIntent.FLAG_IMMUTABLE);
        Notification.Builder b=Build.VERSION.SDK_INT>=26?new Notification.Builder(this,CHANNEL):new Notification.Builder(this);
        int percent=total>0?(int)Math.min(100,done*100/total):0;
        return b.setSmallIcon(android.R.drawable.stat_sys_upload)
            .setContentTitle("OREZ USB Studio · "+phase)
            .setContentText(detail)
            .setContentIntent(pi).setOnlyAlertOnce(true).setOngoing(running)
            .setProgress(100,percent,running && total<=0).build();
    }
    private void updateNotification(boolean force) {
        long now=SystemClock.elapsedRealtime();
        if(!force && running && now-lastNotificationAt<1000) return;
        lastNotificationAt=now;
        try { ((NotificationManager)getSystemService(NOTIFICATION_SERVICE)).notify(NOTIFICATION_ID,notification()); }
        catch(Exception ignored) {}
    }
    private static MessageDigest sha256() throws Exception { return MessageDigest.getInstance("SHA-256"); }
    private static String hex(byte[] bytes) {
        StringBuilder s=new StringBuilder(bytes.length*2);
        for(byte b:bytes) s.append(String.format(Locale.ROOT,"%02x",b&255));
        return s.toString();
    }
    private static String formatBytes(long n) {
        return String.format(Locale.ROOT,"%.2f GiB",n/1073741824.0);
    }

    @Override public void onDestroy() {
        stopLiveMonitor();
        if(running) cancelled=true;
        if(wakeLock!=null && wakeLock.isHeld()) wakeLock.release();
        super.onDestroy();
    }
}
