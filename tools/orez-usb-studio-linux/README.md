# OREZ USB Studio Linux 0.4.0

A phone-first Android USB recovery and writer for x86_64 Ubuntu-family hybrid installation ISOs, including Kubuntu desktop images. This build is Linux-only; the old Windows extraction/FAT32/WIM workflow is not included.

## USB recovery\n\nThe separate **OREZ USB Recovery** launcher entry detects USB Mass Storage BOT devices even when Android Files cannot mount their damaged partition layout. After explicit device selection and typing `FORMAT`, it replaces the previous hybrid/partition metadata with a conventional MBR + FAT32 volume, initializes both FAT copies and verifies the MBR, FAT32 boot sector and FAT table by reading them back. This is a destructive operation and is not a physical flash-memory repair. It requires a 512-byte-sector BOT device and USB OTG permission.\n\n## Writing model

Ubuntu/Kubuntu desktop ISOs are hybrid disk images. The app writes the original image to the USB device from byte zero, preserving its embedded partition map, ISO9660 data and boot structures. It does not extract the ISO, reformat it as FAT32, create a new partition table, or split files.

Before erasing, it checks the ISO9660 volume descriptor, El Torito catalogue checksum, hybrid MBR/GPT evidence, the casper kernel/filesystem files and the x86_64 EFI loader. It calculates SHA-256 and requires the user to provide the matching value from the official distribution checksum file. It confirms USB capacity and requires typing ERASE.

The writer uses Android USB Host API with USB Mass Storage Bulk-Only Transport and SCSI READ(10)/WRITE(10), in bounded 16 KiB transfers. It flushes the device and performs a complete sector-by-sector read-back comparison, calculating SHA-256 again. A failed or interrupted write is reported as incomplete; no write retry or automatic resume occurs. Android bulk data stages are now drained across short `bulkTransfer` completions instead of assuming one call transfers the entire SCSI stage.

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

## Safety

The selected USB is completely overwritten from LBA 0 through the end of the ISO image. Verify its product name and capacity before typing ERASE. Back up all data first. Disconnecting or cancelling during writing leaves incomplete media. Internet permission is used only when Live Monitor is explicitly enabled. The app does not upload the ISO or its contents. Checksum authenticity depends on obtaining the expected SHA-256 from the official distribution source.

## Build

Requires JDK 17, Android SDK platform 35, Android Gradle Plugin 8.7.3 and Gradle 8.9. The GitHub Actions workflow builds, runs unit tests, signs the debug APK with the ephemeral Android debug key, and uploads an APK artifact. Users uninstall a prior differently signed build before installing this build.
