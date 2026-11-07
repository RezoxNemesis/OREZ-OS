# OREZ USB Studio Linux 0.4.4

A phone-first Android USB recovery and writer for x86_64 Ubuntu-family hybrid installation ISOs, including Kubuntu desktop images. This build is Linux-only; the old Windows extraction/FAT32/WIM workflow is not included.

## USB recovery

The separate **OREZ USB Recovery** launcher entry detects USB Mass Storage BOT devices even when Android Files cannot mount their damaged partition layout. After explicit device selection and typing `FORMAT`, it replaces the previous hybrid/partition metadata with a conventional MBR + FAT32 volume, initializes both FAT copies and verifies the MBR, FAT32 boot sector and FAT tables by reading them back. This is a destructive operation and is not a physical flash-memory repair. It requires a 512-byte-sector BOT device and USB OTG permission.

## Writing model

Ubuntu/Kubuntu desktop ISOs are hybrid disk images. The app writes the original image to the USB device from byte zero, preserving its embedded partition map, ISO9660 data and boot structures. It does not extract the ISO, reformat it as FAT32, create a new partition table, or split files.

Before erasing, it checks the ISO9660 volume descriptor, El Torito catalogue checksum, hybrid MBR/GPT evidence, the casper kernel/filesystem files and the x86_64 EFI loader. It calculates SHA-256 and requires the user to provide the matching value from the official distribution checksum file. It confirms USB capacity and requires typing `ERASE`.

The writer uses Android USB Host API with USB Mass Storage Bulk-Only Transport and SCSI READ(10)/WRITE(10), in bounded 16 KiB transfers. It requests SCSI SYNCHRONIZE CACHE when supported. Some USB flash controllers reject that optional command; 0.4.1 identifies this response, continues to a complete sector-by-sector read-back comparison, and instructs the user to safely eject and reconnect before booting. Rejected data writes and transport errors still stop the job. It calculates SHA-256 again over the read-back data. A failed or interrupted write is reported as incomplete; no write retry or automatic resume occurs. Android bulk data stages are drained across short `bulkTransfer` completions instead of assuming one call transfers the entire SCSI stage. SCSI REQUEST SENSE details identify the rejected command and, where available, its sense key and ASC/ASCQ.

## Optional OREZ Live Monitor

Live reporting is disabled by default. The owner must explicitly enable it for each write and paste a fresh private pairing code supplied in the active ChatGPT conversation. The app uses the existing `orez-usb-studio` Cloudflare relay and its short-lived D1 session format from Windows Studio 0.2.1. It sends a bounded status snapshot over HTTPS every 10 seconds and one final snapshot when the job stops.

Reported fields are the app version, current phase/detail, running/success flags, ISO SHA-256 and byte size, x86_64 target architecture, USB product name/VID/PID/capacity, byte progress and whether the source checksum matched the user-entered reference value (which should be copied from the official SHA256SUMS file). The USB serial number, Android file URI/path, ISO bytes, USB contents, photos, unrelated files and account credentials are not sent.

The Linux client is reporting-only. It discards the relay response and never processes the legacy Windows command field, so it cannot remotely start, cancel, re-arm or change a USB write. Network loss does not pause or restart local writing. The relay retains the latest status snapshot for the paired session (not a complete event-history log). During an active ChatGPT conversation, the assistant can retrieve that latest snapshot through the connected Cloudflare account; the relay does not push messages into the chat or provide unattended monitoring after the conversation ends. A local **Share diagnostic report** action exports the current phase, details, byte progress, ISO hash, USB model/capacity, checksum result and monitor state without the pairing token or USB serial number; the local notification and final screen remain available if reporting fails. Pairing credentials are held in memory for that one session and the input is cleared when the activity closes.

## Device compatibility

- Android 9+ with USB Host / OTG.
- USB Mass Storage BOT, SCSI transparent, LUN 0.
- 512-byte logical sectors and capacity under 2 TiB.
- x86_64 / amd64 UEFI Ubuntu-family desktop hybrid ISO.
- Target USB must be at least as large as the padded image.

UAS-only devices, 4K logical-sector devices, non-hybrid images, ARM images and netboot archives are not supported by this release. Some Android kernels/adapters may not expose BOT endpoints even when a file manager can browse the drive.

## Post-reconnect verification

After a successful same-session read-back, safely eject and physically disconnect/reconnect the USB. Select the same ISO, enter its official SHA-256, select the reconnected USB and run **Read-only verify USB after reconnect**. This reads the complete ISO-sized region directly from the reconnected device and compares its SHA-256 with the inspected ISO. A pass confirms the data persisted across power removal. A failure means the USB must not be booted and may indicate a media/controller/OTG issue.

Android may display a generic **Damaged USB storage** warning after a PC Linux hybrid ISO is written. That warning means Android could not mount the resulting partition/filesystem layout as ordinary phone storage; it is not, by itself, proof that the boot image is corrupt. Do not accept Android's format prompt after writing a PC installer. The post-reconnect full-image verification is the phone-side persistence check; final bootability must still be tested on the target PC.

## Safety

The selected USB is overwritten from LBA 0 through the end of the ISO image. Verify its product name and capacity before typing ERASE. Back up all data first. Disconnecting or cancelling during writing leaves incomplete media. Internet permission is used only when Live Monitor is explicitly enabled. The app does not upload the ISO or its contents. Checksum authenticity depends on obtaining the expected SHA-256 from the official distribution source.

## Build

Requires JDK 17, Android SDK platform 35, Android Gradle Plugin 8.7.3 and Gradle 8.9. The GitHub Actions workflow runs unit tests, builds the debug APK, verifies its signature, and uploads the APK artifact. Debug APKs use the CI debug signing key; uninstall a differently signed prior build before installing this APK.


### 0.4.4 diagnostic accuracy

Read-only post-reconnect verification records its own explicit pass/fail result, verified image size and SHA-256, and the reconnected USB's VID/PID/product/capacity. The report distinguishes write success from persistence verification.
