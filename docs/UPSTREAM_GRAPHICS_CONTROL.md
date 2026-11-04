# OREZ OS — pristine Kubuntu graphical control

This test uses the original, pinned Kubuntu 26.04.1 ISO, not the OREZ remix.
It isolates whether the black screen after selecting Try is an upstream
CPU-only QEMU VirtIO problem or something introduced in OREZ.

- A checksum-verified upstream image is booted in software-only QEMU.
- No writable disk, network, port forwarding, host input, installer or root access.
- The pinned Try-screen matcher must pass before the only guest mouse click.
- Two later frames are retained and must be inspected before any conclusion.
- A nonblack frame is not by itself proof of a correct KDE desktop.
- The upstream ISO is never uploaded as a GitHub Actions artifact.

To launch, use a single one-shot build/upstream-control-* branch or manual
workflow dispatch. This is NOT an OREZ release or a physical PC test.
Do not disable system security or modify real graphics drivers for this control.
