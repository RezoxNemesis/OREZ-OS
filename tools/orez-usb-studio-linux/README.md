# OREZ USB Studio Linux 0.3.0

A phone-first Android writer for x86_64 Ubuntu-family hybrid installation ISOs, including Kubuntu desktop images. This build is Linux-only; the old Windows extraction/FAT32/WIM workflow is not included.

## Writing model

Ubuntu/Kubuntu desktop ISOs are hybrid disk images. The app writes the original image to the USB device from byte zero, preserving its embedded partition map, ISO9660 data and boot structures. It does not extract the ISO, reformat it as FAT32, create a new partition table, or split files.

Before erasing, it checks the ISO9660 volume descriptor, El Torito catalogue checksum, hybrid MBR/GPT evidence, the casper kernel/filesystem files and the x86_64 EFI loader. It calculates SHA-256 and requires the user to provide the matching value from the official distribution checksum file. It confirms USB capacity and requires typing ERASE.

The writer uses Android USB Host API with USB Mass Storage Bulk-Only Transport and SCSI READ(10)/WRITE(10), in bounded 16 KiB transfers. It flushes the device and performs a complete sector-by-sector read-back comparison, calculating SHA-256 again. A failed or interrupted write is reported as incomplete; no write retry or automatic resume occurs.

## Device compatibility

- Android 9+ with USB Host / OTG.
- USB Mass Storage BOT, SCSI transparent, LUN 0.
- 512-byte logical sectors and capacity under 2 TiB.
- x86_64 / amd64 UEFI Ubuntu-family desktop hybrid ISO.
- Target USB must be at least as large as the padded image.

UAS-only devices, 4K logical-sector devices, non-hybrid images, ARM images and netboot archives are not supported by this release. Some Android kernels/adapters may not expose BOT endpoints even when a file manager can browse the drive.

## Safety

The selected USB is completely overwritten from LBA 0 through the end of the ISO image. Verify its product name and capacity before typing ERASE. Back up all data first. Disconnecting or cancelling during writing leaves incomplete media. The app has no Internet permission and does not upload the ISO or its contents. Checksum authenticity depends on obtaining the expected SHA-256 from the official distribution source.

## Build

Requires JDK 17, Android SDK platform 35, Android Gradle Plugin 8.7.3 and Gradle 8.9. The GitHub Actions workflow builds, runs unit tests, signs the debug APK with the ephemeral Android debug key, and uploads an APK artifact. Users uninstall the prior v0.2.x app before installing this build because it is signed with a different key.
