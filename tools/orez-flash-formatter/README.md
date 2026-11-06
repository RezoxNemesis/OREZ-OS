# OREZ Flash Formatter 1.0.0

A standalone Android USB OTG flash-drive formatter. It uses Android USB Host and USB Mass Storage Bulk-Only Transport (BOT), performs a read-only capacity/preflight check, then on explicit user confirmation writes an MBR + FAT32 layout and reads back key structures.

## Safety

- Select a device by product name and VID/PID; inspect capacity before formatting.
- Formatting is destructive and erases the selected drive.
- Requires USB Mass Storage BOT/SCSI with 512-byte sectors and Android USB permission.
- Does not support USB devices exposed only through MTP, UAS, hubs that block BOT, or unsupported sector sizes.
- A successful metadata check is not a full media surface test and cannot repair failing flash memory.
- Keep OTG connected and screen awake during formatting; do not unplug until completion.

## Build

Use JDK 17, Android SDK platform 35, and Gradle 8.9. Run `:app:assembleDebug`.
