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

## 2026-11-05: First-run harness correction
The original control run 41887435151 failed to select Try, NOT because Kubuntu's display was shown broken, but because the test waited for an OREZ-only serial diagnostic string. The fixed controller samples actual QEMU framebuffer pixels every ten seconds and will only click the left-hand Try button when the known 1280x800 welcome layout matches. Otherwise it retains the most recent screenshot as evidence and exits without input. Still no disk or network.
