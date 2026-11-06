package com.orez.formatter;

import android.app.Activity;
import android.app.AlertDialog;
import android.app.PendingIntent;
import android.content.*;
import android.hardware.usb.*;
import android.os.*;
import android.view.View;
import android.widget.*;
import java.io.IOException;
import java.util.ArrayList;
import java.util.Locale;

/** Separate launcher entry for restoring a failed or unmountable USB on the phone. */
public final class MainActivity extends Activity {
    private static final String PERMISSION="com.orez.formatter.USB_PERMISSION";
    private UsbManager manager;
    private UsbDevice selected;
    private TextView status,detail;
    private ProgressBar progress;
    private Button scan,format;
    private boolean busy=false,receiverRegistered=false;

    private final BroadcastReceiver receiver=new BroadcastReceiver(){
        @Override public void onReceive(Context c,Intent i){
            if(!PERMISSION.equals(i.getAction()))return;
            UsbDevice d=(UsbDevice)i.getParcelableExtra(UsbManager.EXTRA_DEVICE);
            if(d==null || selected==null || d.getDeviceId()!=selected.getDeviceId())return;
            if(manager.hasPermission(d)) inspect(d);
            else setStatus("USB permission denied","Android did not grant access. Reconnect the OTG drive and try again.");
        }
    };

    @Override public void onCreate(Bundle state){
        super.onCreate(state);
        manager=(UsbManager)getSystemService(USB_SERVICE);
        getWindow().setStatusBarColor(0xff0a121e);getWindow().setNavigationBarColor(0xff0a121e);
        LinearLayout root=new LinearLayout(this);root.setOrientation(1);root.setPadding(32,36,32,32);root.setBackgroundColor(0xff0a121e);
        TextView title=new TextView(this);title.setText("OREZ Flash Formatter");title.setTextSize(27);title.setTextColor(0xffebf2f9);root.addView(title);
        TextView intro=new TextView(this);intro.setText("Standalone flash-drive formatter. Detects a USB mass-storage device directly over OTG and creates a standard MBR + FAT32 volume for Android file managers.");intro.setTextSize(14);intro.setTextColor(0xff9badc2);root.addView(intro);
        status=new TextView(this);status.setTextColor(0xff63e7c7);status.setTextSize(18);status.setPadding(0,28,0,8);root.addView(status);
        detail=new TextView(this);detail.setTextColor(0xffebf2f9);detail.setTextSize(14);root.addView(detail);
        progress=new ProgressBar(this,null,android.R.attr.progressBarStyleHorizontal);root.addView(progress,new LinearLayout.LayoutParams(-1,18));
        scan=new Button(this);scan.setText("Detect connected USB");root.addView(scan);scan.setOnClickListener(v->scanUsb());
        format=new Button(this);format.setText("Format selected drive as FAT32");root.addView(format);format.setEnabled(false);format.setOnClickListener(v->confirmFormat());
        TextView warning=new TextView(this);warning.setText("WARNING: Formatting permanently erases the selected USB. Check the selected drive name and capacity carefully. This does not repair a physically failing drive. After recovery, select the Kubuntu ISO again and restart the complete write.");warning.setTextColor(0xffffc67d);warning.setTextSize(13);warning.setPadding(0,24,0,0);root.addView(warning);
        setContentView(root);
        IntentFilter f=new IntentFilter(PERMISSION);
        if(Build.VERSION.SDK_INT>=33)registerReceiver(receiver,f,Context.RECEIVER_NOT_EXPORTED);else registerReceiver(receiver,f);
        receiverRegistered=true;
        setStatus("Ready","Connect the SanDisk using your USB-C OTG adapter.");
    }

    private void scanUsb(){
        if(busy)return;
        ArrayList<UsbDevice> found=new ArrayList<>();
        for(UsbDevice d:manager.getDeviceList().values())if(UsbBot.supports(d))found.add(d);
        if(found.isEmpty()){selected=null;format.setEnabled(false);setStatus("No compatible USB detected","Reconnect the OTG adapter. The drive must expose USB Mass Storage BOT / SCSI.");return;}
        String[] labels=new String[found.size()];
        for(int i=0;i<found.size();i++){UsbDevice d=found.get(i);labels[i]=(d.getProductName()==null?"USB mass storage":d.getProductName())+String.format(Locale.ROOT," · %04X:%04X",d.getVendorId(),d.getProductId());}
        new AlertDialog.Builder(this).setTitle("Select your flash drive").setItems(labels,(x,n)->{
            selected=found.get(n);format.setEnabled(false);
            setStatus("Checking "+labels[n],"Opening a read-only capacity check. No sectors have been changed.");
            if(manager.hasPermission(selected))inspect(selected);
            else{
                Intent req=new Intent(PERMISSION).setPackage(getPackageName());
                PendingIntent pi=PendingIntent.getBroadcast(this,43,req,PendingIntent.FLAG_UPDATE_CURRENT|PendingIntent.FLAG_MUTABLE);
                manager.requestPermission(selected,pi);
            }
        }).setNegativeButton("Cancel",null).show();
    }

    private void inspect(UsbDevice device){
        new Thread(()->{
            try(UsbBot bot=new UsbBot(manager,device)){
                long bytes=bot.capacityBytes();
                runOnUiThread(()->{
                    if(!stillSelected(device))return;
                    format.setEnabled(true);
                    setStatus("USB detected · "+String.format(Locale.ROOT,"%.2f GiB",bytes/1073741824.0),
                        "Device: "+(device.getProductName()==null?"USB mass storage":device.getProductName())+
                        "\nCapacity: "+bytes+" bytes\n512-byte sectors · read-only preflight passed.\nReady for explicit formatting.");
                });
            }catch(Exception e){runOnUiThread(()->{format.setEnabled(false);setStatus("USB cannot be opened",e.getMessage()==null?e.toString():e.getMessage());});}
        },"orez-usb-recovery-probe").start();
    }

    private boolean stillSelected(UsbDevice d){
        UsbDevice current=manager.getDeviceList().get(d.getDeviceName());
        return current!=null && selected!=null && current.getDeviceId()==selected.getDeviceId() && manager.hasPermission(current);
    }

    private void confirmFormat(){
        if(busy || selected==null || !manager.hasPermission(selected))return;
        EditText confirm=new EditText(this);confirm.setSingleLine(true);confirm.setHint("Type FORMAT to confirm");
        AlertDialog d=new AlertDialog.Builder(this).setTitle("Final erase confirmation")
            .setMessage("This operation is destructive and cannot be undone. Type FORMAT below.")
            .setView(confirm).setNegativeButton("Cancel",null).setPositiveButton("Format USB",null).create();
        d.setOnShowListener(v->d.getButton(-1).setOnClickListener(b->{
            if(!"FORMAT".equals(confirm.getText().toString().trim())){confirm.setError("Type FORMAT exactly.");return;}
            if(!stillSelected(selected)){setStatus("USB disconnected","No formatting was performed.");d.dismiss();return;}
            d.dismiss();runFormat(selected);
        }));
        d.show();
    }

    private void runFormat(UsbDevice device){
        busy=true;scan.setEnabled(false);format.setEnabled(false);progress.setIndeterminate(true);
        setStatus("Formatting USB","Writing MBR, FAT32 boot records, FSInfo and allocation tables. Keep OTG connected.");
        new Thread(()->{
            try(UsbBot bot=new UsbBot(manager,device)){
                UsbFat32Formatter.format(bot,(phase,done,total)->runOnUiThread(()->{
                    progress.setIndeterminate(false);progress.setMax((int)Math.max(1,total));progress.setProgress((int)Math.min(done,total));
                    detail.setText(phase+" · "+done+" / "+total+" sectors");
                }));
                runOnUiThread(()->setStatus("FAT32 format verified","The MBR, boot sector and FAT allocation table passed read-back checks. Safely disconnect and reconnect the USB, then check Google Files."));
            }catch(Exception e){runOnUiThread(()->setStatus("Formatting failed — USB not verified",e.getMessage()==null?e.toString():e.getMessage()));}
            finally{runOnUiThread(()->{busy=false;scan.setEnabled(true);format.setEnabled(false);});}
        },"orez-usb-fat32-format").start();
    }

    private void setStatus(String p,String d){status.setText(p);detail.setText(d);}
    @Override protected void onDestroy(){if(receiverRegistered)try{unregisterReceiver(receiver);}catch(Exception ignored){}super.onDestroy();}
}
