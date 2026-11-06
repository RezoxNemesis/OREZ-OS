package com.orez.usb;

import android.app.Activity;
import android.app.AlertDialog;
import android.app.PendingIntent;
import android.content.*;
import android.content.pm.PackageManager;
import android.database.Cursor;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.hardware.usb.*;
import android.net.Uri;
import android.os.*;
import android.provider.OpenableColumns;
import android.text.InputType;
import android.text.TextWatcher;
import android.text.Editable;
import android.view.*;
import android.widget.*;
import java.io.FileInputStream;
import java.io.InputStream;
import java.util.ArrayList;
import java.util.Locale;

public final class MainActivity extends Activity {
    private static final int BG=Color.rgb(10,18,30), CARD=Color.rgb(20,32,49),
        TEXT=Color.rgb(235,242,249), MUTED=Color.rgb(155,173,194), MINT=Color.rgb(99,231,199),
        AMBER=Color.rgb(255,198,125);
    private static final String USB_PERMISSION="com.orez.usb.USB_PERMISSION";
    private final Handler handler=new Handler(Looper.getMainLooper());
    private UsbManager usbManager;
    private Uri isoUri;
    private UsbDevice selectedUsb;
    private long isoBytes,usbBytes;
    private String isoName="No Linux ISO selected",isoHash="",isoSummary="";
    private boolean inspecting=false,receiverRegistered=false;
    private TextView isoLabel,usbLabel,statusLabel,detailLabel,hashState;
    private EditText checksumInput,monitorPairCode;
    private CheckBox monitorConsent;
    private TextView monitorStateLabel;
    private Button selectIsoButton,selectUsbButton,createButton,cancelButton;
    private ProgressBar progress;
    private Runnable poll;

    private final BroadcastReceiver usbReceiver=new BroadcastReceiver() {
        @Override public void onReceive(Context context,Intent intent) {
            String action=intent.getAction();
            UsbDevice device=(UsbDevice)intent.getParcelableExtra(UsbManager.EXTRA_DEVICE);
            if(USB_PERMISSION.equals(action)) {
                if(device!=null && selectedUsb!=null &&
                   device.getDeviceId()==selectedUsb.getDeviceId() && usbManager.hasPermission(device)) {
                    inspectSelectedUsb(device);
                } else {
                    toast("USB permission was not granted. Select the drive again.");
                }
            } else if(UsbManager.ACTION_USB_DEVICE_DETACHED.equals(action)) {
                if(device!=null && selectedUsb!=null && device.getDeviceId()==selectedUsb.getDeviceId()) {
                    selectedUsb=null; usbBytes=0;
                    usbLabel.setText("USB disconnected. Reconnect it, then select it again.");
                    refreshControls();
                }
            }
        }
    };

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        usbManager=(UsbManager)getSystemService(USB_SERVICE);
        getWindow().setStatusBarColor(BG);
        getWindow().setNavigationBarColor(BG);
        getWindow().getDecorView().setSystemUiVisibility(0);
        buildUi();
        IntentFilter filter=new IntentFilter(USB_PERMISSION);
        filter.addAction(UsbManager.ACTION_USB_DEVICE_DETACHED);
        if(Build.VERSION.SDK_INT>=33) registerReceiver(usbReceiver,filter,Context.RECEIVER_NOT_EXPORTED);
        else registerReceiver(usbReceiver,filter);
        receiverRegistered=true;

        if(Build.VERSION.SDK_INT>=33 && checkSelfPermission("android.permission.POST_NOTIFICATIONS")!=PackageManager.PERMISSION_GRANTED)
            requestPermissions(new String[]{"android.permission.POST_NOTIFICATIONS"},31);

        poll=new Runnable(){@Override public void run(){
            if(isFinishing())return;
            statusLabel.setText(WriteService.phase);
            detailLabel.setText(WriteService.detail);
            if(monitorStateLabel!=null) monitorStateLabel.setText(WriteService.monitorState);
            long maximum=WriteService.total,completed=WriteService.done;
            progress.setIndeterminate(WriteService.running && maximum<=0);
            progress.setProgress(maximum>0?(int)Math.min(100,completed*100/maximum):0);
            cancelButton.setVisibility(WriteService.running?View.VISIBLE:View.GONE);
            refreshControls();
            handler.postDelayed(this,600);
        }};
        handler.post(poll);
    }

    private void buildUi() {
        ScrollView scroll=new ScrollView(this); scroll.setFillViewport(true); scroll.setBackgroundColor(BG);
        LinearLayout page=new LinearLayout(this); page.setOrientation(LinearLayout.VERTICAL);
        page.setPadding(dp(20),dp(22),dp(20),dp(32)); scroll.addView(page); setContentView(scroll);

        TextView brand=label("OREZ   /   USB STUDIO     0.4.0",12,MINT);
        brand.setLetterSpacing(.13f); page.addView(brand);
        TextView title=label("Linux installer.\nWritten the right way.",29,TEXT);
        title.setTypeface(Typeface.DEFAULT,Typeface.BOLD); page.addView(title);
        page.addView(label("Prepare a bootable Kubuntu / Ubuntu x86_64 USB directly from Android. The original hybrid ISO is cloned byte-for-byte; no extraction or FAT32 reformatting.",14,MUTED));
        page.addView(gap(16));
        TextView notice=label("LINUX ONLY  ·  AMD64 / x86_64  ·  UEFI HYBRID ISO\nThis release does not create Windows installation media.",13,AMBER);
        notice.setBackground(round(CARD,14));notice.setPadding(dp(14),dp(13),dp(14),dp(13));page.addView(notice);

        page.addView(sectionTitle("01  /  LINUX ISO"));
        isoLabel=label(isoName,14,TEXT); isoLabel.setBackground(round(CARD,14));isoLabel.setPadding(dp(14),dp(14),dp(14),dp(14));page.addView(isoLabel);
        selectIsoButton=button("Choose ISO from phone storage",false);page.addView(selectIsoButton);
        selectIsoButton.setOnClickListener(v->chooseIso());
        page.addView(label("Download the official amd64 desktop ISO and its SHA256SUMS file. Select the ISO here, then paste the exact SHA-256 value for that filename below.",13,MUTED));

        page.addView(sectionTitle("02  /  OFFICIAL SHA-256"));
        checksumInput=new EditText(this);
        checksumInput.setSingleLine(true);checksumInput.setTextColor(TEXT);checksumInput.setHintTextColor(MUTED);
        checksumInput.setHint("64-character SHA-256 from official SHA256SUMS");
        checksumInput.setTextSize(13);checksumInput.setInputType(InputType.TYPE_CLASS_TEXT|InputType.TYPE_TEXT_FLAG_NO_SUGGESTIONS);
        checksumInput.setPadding(dp(13),dp(11),dp(13),dp(11));checksumInput.setBackground(round(CARD,12));
        page.addView(checksumInput,new LinearLayout.LayoutParams(-1,dp(54)));
        hashState=label("ISO not checked yet.",13,MUTED);page.addView(hashState);
        checksumInput.addTextChangedListener(new TextWatcher(){
            public void beforeTextChanged(CharSequence s,int st,int c,int a){}
            public void onTextChanged(CharSequence s,int st,int before,int count){refreshControls();}
            public void afterTextChanged(Editable e){}
        });

        page.addView(sectionTitle("03  /  TARGET USB"));
        usbLabel=label("Connect your blank USB through the Type-C / OTG adapter, then select it.",14,TEXT);
        usbLabel.setBackground(round(CARD,14));usbLabel.setPadding(dp(14),dp(14),dp(14),dp(14));page.addView(usbLabel);
        selectUsbButton=button("Select connected USB drive",false);page.addView(selectUsbButton);
        selectUsbButton.setOnClickListener(v->scanUsb());

        page.addView(sectionTitle("04  /  OPTIONAL LIVE MONITOR"));
        TextView monitorPrivacy=label("With your permission, send live USB-writing progress and diagnostic details to the existing OREZ monitor so this chat can inspect the current status. Only the ISO SHA-256 and size, x86_64 target, USB model/VID/PID/capacity, progress, phase and error details are reported. No ISO contents, file paths, USB serial number or unrelated phone data are sent. Reporting uses HTTPS and can be left off.",13,MUTED);
        monitorPrivacy.setBackground(round(CARD,14));monitorPrivacy.setPadding(dp(14),dp(13),dp(14),dp(13));page.addView(monitorPrivacy);
        monitorConsent=new CheckBox(this);
        monitorConsent.setText("Enable Live Monitor for this USB-writing session");
        monitorConsent.setTextColor(TEXT);monitorConsent.setButtonTintList(android.content.res.ColorStateList.valueOf(MINT));
        page.addView(monitorConsent);
        monitorPairCode=new EditText(this);
        monitorPairCode.setSingleLine(true);monitorPairCode.setTextColor(TEXT);monitorPairCode.setHintTextColor(MUTED);
        monitorPairCode.setHint("Paste private pairing code from ChatGPT");
        monitorPairCode.setInputType(InputType.TYPE_CLASS_TEXT|InputType.TYPE_TEXT_VARIATION_PASSWORD);
        monitorPairCode.setImportantForAutofill(View.IMPORTANT_FOR_AUTOFILL_NO);
        monitorPairCode.setSaveEnabled(false);
        monitorPairCode.setPadding(dp(13),dp(11),dp(13),dp(11));monitorPairCode.setBackground(round(CARD,12));
        page.addView(monitorPairCode,new LinearLayout.LayoutParams(-1,dp(54)));
        monitorPairCode.setEnabled(false);
        monitorConsent.setOnCheckedChangeListener((button,checked)->{
            monitorPairCode.setEnabled(checked);
            if(!checked) monitorPairCode.setText("");
            if(monitorStateLabel!=null) monitorStateLabel.setText(checked?"Consent enabled for the next USB-writing session only.":"Live monitoring is off. No data will be transmitted.");
            refreshControls();
        });
        monitorPairCode.addTextChangedListener(new TextWatcher(){
            public void beforeTextChanged(CharSequence s,int st,int count,int after){}
            public void onTextChanged(CharSequence s,int st,int before,int count){refreshControls();}
            public void afterTextChanged(Editable e){}
        });
        monitorStateLabel=label("Live monitoring is off. No data will be transmitted.",13,MUTED);
        page.addView(monitorStateLabel);

        page.addView(sectionTitle("05  /  WRITE AND VERIFY"));
        TextView safety=label("The selected USB will be overwritten from sector zero. The app checks the ISO, checks the drive capacity, writes the original hybrid image, flushes it, then reads back every byte and compares SHA-256.",13,MUTED);
        safety.setBackground(round(CARD,14));safety.setPadding(dp(14),dp(13),dp(14),dp(13));page.addView(safety);
        createButton=button("Review & create Linux USB",true);page.addView(createButton);
        createButton.setOnClickListener(v->confirmWrite());
        cancelButton=button("Cancel current write",false);page.addView(cancelButton);
        cancelButton.setVisibility(View.GONE);
        cancelButton.setOnClickListener(v->new AlertDialog.Builder(this)
            .setTitle("Cancel USB writing?")
            .setMessage("The USB will be incomplete and must be written again from the beginning. Do not boot from it.")
            .setNegativeButton("Continue writing",null)
            .setPositiveButton("Cancel write",(d,w)->startService(new Intent(this,WriteService.class).setAction(WriteService.ACTION_CANCEL)))
            .show());

        statusLabel=label(WriteService.phase,19,TEXT);page.addView(statusLabel);
        progress=new ProgressBar(this,null,android.R.attr.progressBarStyleHorizontal);
        progress.setProgressTintList(android.content.res.ColorStateList.valueOf(MINT));
        page.addView(progress,new LinearLayout.LayoutParams(-1,dp(8)));
        detailLabel=label(WriteService.detail,13,MUTED);page.addView(detailLabel);
        Button reportButton=button("Share diagnostic report",false);page.addView(reportButton);
        reportButton.setOnClickListener(v->{
            Intent share=new Intent(Intent.ACTION_SEND).setType("text/plain")
                .putExtra(Intent.EXTRA_TEXT,WriteService.diagnosticReport());
            try { startActivity(Intent.createChooser(share,"Share OREZ USB diagnostic report")); }
            catch(Exception e) { toast("Could not open the sharing menu."); }
        });

        page.addView(gap(14));
        page.addView(label("Important: this app supports USB Mass Storage BOT with 512-byte logical sectors. UAS-only or 4K-sector devices may not work. A failed write is never automatically retried. Always use a blank drive and keep the phone powered.",12,AMBER));
        Button official=button("Open official Kubuntu downloads",false);page.addView(official);
        official.setOnClickListener(v->{
            try{startActivity(new Intent(Intent.ACTION_VIEW,Uri.parse("https://kubuntu.org/getkubuntu/")));}
            catch(Exception e){toast("Could not open the browser.");}
        });
        page.addView(label("Live monitoring is optional and off by default. A fresh private pairing code is required for each session. The connection is reporting-only from this Linux app: it never accepts remote USB-write, cancel or checksum commands. If the network fails, local writing continues.",12,MUTED));
        refreshControls();
    }

    private TextView sectionTitle(String text) {
        TextView t=label(text,12,MINT); t.setPadding(0,dp(18),0,dp(8)); return t;
    }
    private TextView label(String text,int size,int color) {
        TextView t=new TextView(this);t.setText(text);t.setTextSize(size);t.setTextColor(color);
        t.setPadding(0,dp(6),0,dp(6));return t;
    }
    private Button button(String text,boolean primary) {
        Button b=new Button(this);b.setText(text);b.setTextSize(14);b.setAllCaps(false);
        b.setTextColor(primary?BG:TEXT);b.setBackground(round(primary?MINT:CARD,14));
        b.setFilterTouchesWhenObscured(true);
        LinearLayout.LayoutParams lp=new LinearLayout.LayoutParams(-1,dp(54));lp.setMargins(0,dp(5),0,dp(5));b.setLayoutParams(lp);
        return b;
    }
    private GradientDrawable round(int color,int radius) {
        GradientDrawable d=new GradientDrawable();d.setColor(color);d.setCornerRadius(dp(radius));return d;
    }
    private View gap(int height) { View v=new View(this);v.setLayoutParams(new LinearLayout.LayoutParams(1,dp(height)));return v; }
    private int dp(int n){return (int)(n*getResources().getDisplayMetrics().density+.5f);}

    private void chooseIso() {
        if(WriteService.running || inspecting)return;
        Intent i=new Intent(Intent.ACTION_OPEN_DOCUMENT);
        i.addCategory(Intent.CATEGORY_OPENABLE);i.setType("*/*");
        i.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION|Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION);
        startActivityForResult(i,10);
    }

    @Override protected void onActivityResult(int request,int result,Intent data) {
        super.onActivityResult(request,result,data);
        if(request!=10 || result!=RESULT_OK || data==null || data.getData()==null)return;
        Uri uri=data.getData();
        try { getContentResolver().takePersistableUriPermission(uri,Intent.FLAG_GRANT_READ_URI_PERMISSION); } catch(Exception ignored){}
        isoUri=uri;isoHash="";isoBytes=0;isoSummary="";
        isoName=displayName(uri);
        isoLabel.setText("Inspecting "+isoName+"…");
        hashState.setText("Checking ISO structure and complete SHA-256. USB remains untouched.");
        inspecting=true;refreshControls();
        new Thread(()->{
            try {
                long size;
                HybridIsoValidator.Info info;
                try(ParcelFileDescriptor pfd=getContentResolver().openFileDescriptor(uri,"r");
                    FileInputStream f=new FileInputStream(pfd.getFileDescriptor())) {
                    size=f.getChannel().size();
                    info=HybridIsoValidator.inspect(f.getChannel());
                }
                String hash=hash(uri,size);
                final long bytes=size;
                runOnUiThread(()->{
                    isoBytes=bytes;isoHash=hash;isoSummary=info.summary();inspecting=false;
                    isoLabel.setText(isoName+"\n"+formatBytes(bytes)+"\n"+isoSummary+"\nSHA-256: "+hash);
                    hashState.setText("Structure check passed. Compare this SHA-256 with the official checksum file, then paste it above.");
                    refreshControls();
                });
            } catch(Exception e) {
                runOnUiThread(()->{
                    inspecting=false;isoHash="";isoBytes=0;
                    isoLabel.setText("ISO rejected: "+(e.getMessage()==null?e.toString():e.getMessage()));
                    hashState.setText("No USB data has been changed.");
                    refreshControls();
                });
            }
        },"orez-iso-inspect").start();
    }

    private String displayName(Uri uri) {
        String name=uri.getLastPathSegment();
        try(Cursor c=getContentResolver().query(uri,new String[]{OpenableColumns.DISPLAY_NAME},null,null,null)) {
            if(c!=null && c.moveToFirst()) name=c.getString(0);
        } catch(Exception ignored) {}
        if(name==null)name="Selected ISO";
        return name;
    }

    private String hash(Uri uri,long expectedBytes) throws Exception {
        java.security.MessageDigest digest=java.security.MessageDigest.getInstance("SHA-256");
        try(InputStream in=getContentResolver().openInputStream(uri)) {
            if(in==null)throw new java.io.IOException("Cannot read the selected file.");
            byte[] b=new byte[256*1024];long n=0;int k;
            while((k=in.read(b))!=-1){digest.update(b,0,k);n+=k;if(n>expectedBytes)throw new java.io.IOException("File size changed during checksum.");}
            if(n!=expectedBytes)throw new java.io.IOException("Selected ISO was truncated.");
        }
        StringBuilder out=new StringBuilder(64);
        for(byte b:digest.digest())out.append(String.format(Locale.ROOT,"%02x",b&255));
        return out.toString();
    }

    private void scanUsb() {
        if(WriteService.running || inspecting)return;
        ArrayList<UsbDevice> devices=new ArrayList<>();
        for(UsbDevice d:usbManager.getDeviceList().values()) if(UsbBot.supports(d)) devices.add(d);
        if(devices.isEmpty()) {
            new AlertDialog.Builder(this).setTitle("No supported USB drive found")
                .setMessage("Reconnect the OTG adapter and flash drive. This app requires USB Mass Storage BOT (SCSI transparent), not UAS-only mode.")
                .setPositiveButton("OK",null).show();
            return;
        }
        String[] labels=new String[devices.size()];
        for(int i=0;i<devices.size();i++)labels[i]=deviceName(devices.get(i));
        new AlertDialog.Builder(this).setTitle("Choose the blank USB drive").setItems(labels,(dialog,which)->{
            UsbDevice chosen=devices.get(which);selectedUsb=chosen;usbBytes=0;
            usbLabel.setText(deviceName(chosen)+"\nChecking capacity; no data will be written…");
            refreshControls();
            if(usbManager.hasPermission(chosen))inspectSelectedUsb(chosen);
            else {
                Intent request=new Intent(USB_PERMISSION).setPackage(getPackageName());
                PendingIntent pi=PendingIntent.getBroadcast(this,41,request,PendingIntent.FLAG_UPDATE_CURRENT|PendingIntent.FLAG_MUTABLE);
                usbManager.requestPermission(chosen,pi);
            }
        }).setNegativeButton("Cancel",null).show();
    }

    private void inspectSelectedUsb(UsbDevice device) {
        new Thread(()->{
            try(UsbBot bot=new UsbBot(usbManager,device)) {
                long bytes=bot.capacityBytes();
                runOnUiThread(()->{
                    UsbDevice current=usbManager.getDeviceList().get(device.getDeviceName());
                    if(current==null || current.getDeviceId()!=device.getDeviceId()) {
                        selectedUsb=null;usbBytes=0;usbLabel.setText("USB disconnected. Select it again.");
                    } else {
                        selectedUsb=device;usbBytes=bytes;
                        usbLabel.setText(deviceName(device)+"\n"+formatBytes(bytes)+" · 512-byte logical sectors\nRead-only connection check passed.");
                    }
                    refreshControls();
                });
            } catch(Exception e) {
                runOnUiThread(()->{
                    selectedUsb=null;usbBytes=0;
                    usbLabel.setText("USB check failed: "+(e.getMessage()==null?e.toString():e.getMessage()));
                    refreshControls();
                });
            }
        },"orez-usb-inspect").start();
    }

    private void confirmWrite() {
        if(!canWrite())return;
        EditText erase=new EditText(this);erase.setSingleLine(true);erase.setHint("Type ERASE to confirm");
        erase.setTextColor(TEXT);erase.setHintTextColor(MUTED);
        AlertDialog dialog=new AlertDialog.Builder(this)
            .setTitle("Review Linux USB creation")
            .setMessage("USB: "+deviceName(selectedUsb)+"\nCapacity: "+formatBytes(usbBytes)+
                "\n\nISO: "+isoName+"\nSize: "+formatBytes(isoBytes)+
                "\nSHA-256: "+isoHash+
                "\n\nThis overwrites the selected USB from sector zero and destroys its existing contents. The writer clones the original hybrid ISO, flushes it and compares a full read-back. Use only a blank drive.")
            .setView(erase).setNegativeButton("Cancel",null).setPositiveButton("Erase & write",null).create();
        dialog.setOnShowListener(v->dialog.getButton(AlertDialog.BUTTON_POSITIVE).setOnClickListener(btn->{
            if(!"ERASE".equals(erase.getText().toString().trim())) {
                erase.setError("Type ERASE exactly to authorize this USB overwrite.");
                return;
            }
            if(!canWrite() || !usbManager.hasPermission(selectedUsb)) {
                toast("The ISO, checksum or USB selection changed. Review them again.");
                dialog.dismiss();return;
            }
            Intent job=new Intent(this,WriteService.class).setAction(WriteService.ACTION_START)
                .putExtra("usbDevice",selectedUsb)
                .putExtra("isoUri",isoUri)
                .putExtra("isoBytes",isoBytes)
                .putExtra("expectedSha256",isoHash);
            if(monitorConsent!=null && monitorConsent.isChecked())
                job.putExtra("liveMonitorPairCode",monitorPairCode.getText().toString().trim());
            try {
                startForegroundService(job);
                if(monitorConsent!=null && monitorConsent.isChecked() && monitorPairCode!=null) monitorPairCode.setText("");
            } catch(Exception e) { toast("Could not start the foreground USB writer: "+e.getMessage()); }
            dialog.dismiss();
            refreshControls();
        }));
        dialog.show();
    }

    private boolean canWrite() {
        String typed=checksumInput==null?"":checksumInput.getText().toString().trim();
        return !WriteService.running && !inspecting && isoUri!=null && isoBytes>0 &&
            isoHash.matches("[0-9a-f]{64}") && typed.matches("(?i)[0-9a-f]{64}") &&
            typed.equalsIgnoreCase(isoHash) && selectedUsb!=null && usbBytes>=((isoBytes+511)/512)*512 &&
            (monitorConsent==null || !monitorConsent.isChecked() ||
             LiveMonitorClient.isValidCode(monitorPairCode==null?"":monitorPairCode.getText().toString()));
    }

    private void refreshControls() {
        if(createButton==null)return;
        boolean validIso=isoHash.matches("[0-9a-f]{64}");
        String typed=checksumInput==null?"":checksumInput.getText().toString().trim();
        if(validIso && typed.length()==64)
            hashState.setText(typed.equalsIgnoreCase(isoHash)?"Official checksum matches the inspected ISO.":"Checksum mismatch — USB writing is locked.");
        else if(validIso)
            hashState.setText("Paste the official SHA-256 value to unlock USB writing.");
        createButton.setEnabled(canWrite());
        createButton.setAlpha(createButton.isEnabled()?1f:.42f);
        selectIsoButton.setEnabled(!WriteService.running && !inspecting);
        selectUsbButton.setEnabled(!WriteService.running && !inspecting);
        if(monitorConsent!=null) monitorConsent.setEnabled(!WriteService.running);
        if(monitorPairCode!=null) monitorPairCode.setEnabled(!WriteService.running && monitorConsent!=null && monitorConsent.isChecked());
    }

    private static String deviceName(UsbDevice d) {
        String name=d.getProductName();
        if(name==null || name.trim().isEmpty())name="USB mass storage";
        return name+String.format(Locale.ROOT," · %04X:%04X",d.getVendorId(),d.getProductId());
    }
    private static String formatBytes(long bytes) {
        return String.format(Locale.ROOT,"%.2f GiB",bytes/1073741824.0);
    }
    private void toast(String text){Toast.makeText(this,text,Toast.LENGTH_LONG).show();}

    @Override protected void onDestroy() {
        handler.removeCallbacksAndMessages(null);
        if(monitorPairCode!=null) monitorPairCode.setText("");
        if(receiverRegistered)try{unregisterReceiver(usbReceiver);}catch(Exception ignored){}
        super.onDestroy();
    }
}
