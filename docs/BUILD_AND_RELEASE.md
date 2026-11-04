# First real live ISO build — operating rules

## Verified upstream
- Official source: https://cdimage.ubuntu.com/cdimage/kubuntu/releases/26.04.1/release/kubuntu-26.04.1-desktop-amd64.iso
- SHA-256: `831e4d4bb85098339ba43d3502cd6619b27e76daf37246a084cd68a6413090b8`
- Official signer fingerprint: `843938DF228D22F7B3742BC0D94AA3F0EFE21092` (Ubuntu CD Image Automatic Signing Key 2012)

The script verifies a signed checksum plus this exact fingerprint; HTTPS alone is not considered sufficient. Verify any updated upstream image through a new source decision.

## Fast first version
`build/build-live.sh` uses a second squashfs layer in `/casper/zz-orez.squashfs`, leaving the official 5 GB base root and signed boot components intact. This reduces RAM/disk requirements versus decompression/recompression and makes a first real **live** build possible on some GitHub runners. It is an implementation hypothesis until the exact initramfs recognizes the second squashfs in a VM test.

The original Kubuntu installer still exists. A layered live filesystem may **not** carry OREZ changes into an installed OS. Do not use the installer on the user's PC until the installation path is explicitly developed and tested.

The ISO must pass both static `build/check-iso.sh` and real UEFI VM boot with the OREZ application visible before calling it a verified live candidate. Additional physical target tests are needed before hardware support is claimed.

## GitHub CI, storage and data safety
- Pull requests run only small source tests and packaging.
- Full ISO build runs only after manual `workflow_dispatch` or an intentionally created one-shot `build/live-*` branch. Ordinary PRs and pushes never download the ISO. This avoids draining the GitHub Actions allocation.
- GitHub-hosted runners have limited free disk space. The script refuses to download the 5.1 GB image when available space is below 11 GiB.
- The 5+ GB ISO is *not* uploaded by default. No download link will be claimed until a compliant, quota-safe delivery route exists.
- Workflows have read-only GitHub permissions and receive no secrets.
- No build steps access physical block devices, flash USB drives, modify PC firmware, or install operating systems.

## Licensing gate
Ubuntu/Kubuntu, kernel, KDE, NVIDIA, fonts, codecs and trademarks each have obligations. A public derived image requires review of Canonical image/mark policy and all included components. Do not publish an OREZ ISO until clearance and attribution are recorded.

## Source status
Built native package is a real `.deb`, but the ISO is an *unverified construction pipeline* until a successful run is recorded. Successful CI does not certify NVIDIA, Secure Boot, disk safety, phone integration or recovery.
