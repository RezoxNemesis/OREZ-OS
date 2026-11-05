# First real live ISO build — operating rules

## Current source/preview tooling

Use Node 24 with the committed npm lockfile. The small PR job builds the native package and the independent responsive preview, runs source and desktop/mobile browser acceptance, and captures every test's evidence, including failures. New artifacts are retained for 14 days. See `TESTING_AND_SCREENSHOTS.md` for exact local commands and evidence limits; `preview/README.md` covers the single-file phone download and optional HTTPS PWA.

Actual APT ownership/reinstall/purge and an Xvfb-native KDE window are exercised in a separate manual-only Docker workflow. Provisioning the Ubuntu dependency image is relatively expensive; do not run it on every docs or preview change. Its base image digest is pinned, but APT versions float until a repository snapshot is adopted. No byte-identical-reproducibility claim follows from this fixture.

No new ISO is built or released by this work. Existing live/installer blockers remain below. The consolidated plan is `MASTER_BLUEPRINT.md`; the current verified implementation is in `AI_HANDOFF.md`.

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

## Explicit VM live-root verification
After construction, the `live-image` GitHub job frees the upstream ISO and installs `qemu-system-x86` and OVMF (the latter is reserved for a separate future UEFI acceptance test). It then boots the **actual OREZ ISO's own kernel and initrd** in a disposable, headless QEMU guest, with no hard disk and no network. Only the guest receives `orez.verify=1`, which activates the documented unprivileged `orez-live-verify.service`. A passing boot requires the guest to read OREZ identity assets and verify its overlay root, and then print an exact witness string to the local VM serial log. The job fails if that witness is absent. Small serial logs and results are retained for two days; no copyrighted multi-gigabyte ISO is uploaded.

**Limit of proof:** this direct-kernel boot bypasses UEFI/GRUB and does not prove KDE graphical login. Full UEFI, secure-boot, installer, and hardware tests remain mandatory and independent.

## First UEFI screenshot gate
`build/test-uefi-vm.sh` launches **the unmodified ISO** through QEMU/OVMF with disposable NVRAM, no writable hard disk and no network, and captures a PPM screenshot for human visual inspection. This does not by itself prove UEFI reached KDE, Secure Boot is enforced, or the actual PC works. Those claims require reviewed screenshots and separate actual-hardware tests. The earlier direct-kernel test is a different gate and is now stopped as soon as it produces its verifiable marker.

## M2: Inspect live ISO installation inputs
The full-image workflow reads Kubuntu's actual `filesystem.squashfs`, `unpackfs.conf` and reported live-only AppArmor sysctl setting, without touching disks. The report explicitly blocks SSD installation until OREZ's installed-system persistence, encryption and recovery are qualified. Expected blockers are displayed, not hidden by the green ISO construction status. No release is authorized by this diagnostic.

## Graphical VM bottleneck diagnostics
The source-visible, opt-in `orez-gui-verify` now reports job blockers, failed units and KDE/SDDM processes at bounded intervals when no Plasma session appears. This is only within a disposable test guest; it runs as `nobody`, has no network, and makes no system modifications. The QEMU test selects hardware KVM acceleration only if the hosted runner exposes it; otherwise it uses slower software emulation. A failing GUI gate stays a failure rather than being bypassed.

## Separate OREZ installed-system payload
`build/build-install-payload.sh` reads `image/installer/installed-files.txt` and composes `/casper/orez-install.squashfs` for the ISO. The exact same allowlist is used to assemble the native `orez-shell.deb`. Live-only test services, the Calamares disabled warning, and unsafe root overrides must not enter either installed payload. `build/check-iso.sh` inspects extracted SquashFS content and rejects forbidden files. An inactive Calamares two-source configuration is at `image/installer/orez-unpackfs-candidate.conf`, documented in `image/installer/README.md`; it is NOT used in an install and MUST be tested on isolated disposable disks before activation. Upstream Calamares supports multiple ordered unpack sources.
