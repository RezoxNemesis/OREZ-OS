# OREZ OS target hardware — qualification required

## Performance and test-host distinction — 5 November 2026

The 6 GiB RAM requirement is a release qualification profile; the real target
remains 16 GiB / Ryzen 5600 / RTX 3050 6 GB. This test host has no usable KVM,
GPU render node or NVIDIA device. Rootless Docker reports no enforced cgroups;
configured 2/4/6 GiB test values were not actual memory ceilings. No physical
compatibility, power-saving, CUDA, VRAM expansion or low-RAM certification follows
from successful component tests. See PERFORMANCE.md and environment/README.md.

- MSI B550M PRO-VDH WIFI (AMD B550/AM4) motherboard.
- AMD Ryzen 5 5600 processor **without integrated graphics**.
- Gigabyte NVIDIA RTX 3050 6 GB dedicated graphics.
- 16 GB DDR4, WD Blue SN5000 500 GB NVMe SSD.
- Lenovo 27-inch monitor (exact model not verified).
- Realme P1 Speed Android phone, USB 2.0 data; no assumed USB-C HDMI alt mode.

Connect the monitor to the graphics card's output. Do not flash BIOS or format SSD. Actual PCI/USB IDs, BIOS version, UEFI state and storage layout are unverified. Hardware tests must check NVIDIA packaged Wayland driver, Vulkan, CUDA, monitor sleep/wake, Wi-Fi/Bluetooth/Ethernet, audio, USB ports, Android KDE Connect and MTP. Use `orezctl hardware` read-only and redact serials/user identifiers from published logs. VM tests do not certify physical boot.

## RAM channels and firmware qualification

Linux uses the channel configuration established by the Ryzen memory controller
and motherboard firmware; OREZ does not enable dual-channel through an OS tweak.
The owner's 16 GiB capacity is known, but module count, capacity per module,
rank, speed and slot placement are not verified. Record those before testing.
With two matching modules, follow the exact MSI manual's recommended paired
slots. One module cannot provide dual-channel bandwidth. Do not infer active
channel mode from total capacity or a DIMM inventory alone.

Use firmware information plus read-only SMBIOS inventory where available, then
repeat a documented sustained memory bandwidth/stability workload. SMBIOS may be
incomplete; report unknown instead of certifying channel mode from a guess.
XMP/A-XMP frequency profiles are separate from dual-channel operation. No OS
service changes memory clocks, voltage, firmware or slot configuration. Physical
module placement and optional firmware changes remain owner-controlled.
