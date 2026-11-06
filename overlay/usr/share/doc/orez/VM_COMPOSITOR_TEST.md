# OREZ VM-only software compositor test

This *explicit and removable* file lives at:
`/etc/xdg/plasma-workspace/env/90-orez-vm-software.sh`.

It can set `KWIN_COMPOSE=Q` (KWin's documented Wayland QPainter compositor) **only if the Linux boot command line includes `orez.verify=1`**. The flag exists solely in the isolated QEMU test command; it is not in the normal OREZ boot menu.

Purpose: determine whether a software compositor can render on QEMU's unaccelerated VirtIO 2D GPU, where the default rendering path has left a black screen after selecting Try. This is NOT a change to your RTX 3050/NVIDIA configuration and is NOT a production fix.

- State: source experiment, NOT yet guest-verified
- Scope: test live overlay only
- Installed OS: not included in `image/installer/installed-files.txt` or the `.deb` package
- User control: remove the script, or omit the `orez.verify=1` flag, to disable it
- Security: no privileged access, disk operations, outbound networking, user credentials, or AI capabilities
- Acceptance: a real non-black, visually inspected Plasma desktop screenshot from QEMU; process-only status is insufficient

Source reference: KDE's KWin environment variables documentation. QPainter may be incompatible with some effects or unavailable in future KWin releases, so any failure must remain an explicit test result.
