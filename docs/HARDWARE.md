# OREZ OS target hardware — qualification required

- MSI B550M PRO-VDH WIFI (AMD B550/AM4) motherboard.
- AMD Ryzen 5 5600 processor **without integrated graphics**.
- Gigabyte NVIDIA RTX 3050 6 GB dedicated graphics.
- 16 GB DDR4, WD Blue SN5000 500 GB NVMe SSD.
- Lenovo 27-inch monitor (exact model not verified).
- Realme P1 Speed Android phone, USB 2.0 data; no assumed USB-C HDMI alt mode.

Connect the monitor to the graphics card's output. Do not flash BIOS or format SSD. Actual PCI/USB IDs, BIOS version, UEFI state and storage layout are unverified. Hardware tests must check NVIDIA packaged Wayland driver, Vulkan, CUDA, monitor sleep/wake, Wi-Fi/Bluetooth/Ethernet, audio, USB ports, Android KDE Connect and MTP. Use `orezctl hardware` read-only and redact serials/user identifiers from published logs. VM tests do not certify physical boot.
