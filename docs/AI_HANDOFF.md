# OREZ OS — Verified Development Handoff

Date: 2026-11-04 (source creation; GitHub commit will be captured separately)
Repository: https://github.com/RezoxNemesis/OREZ-OS
Foundation: Kubuntu 26.04.1 LTS amd64, KDE Plasma 6
Target: AMD Ryzen 5 5600 / MSI B550M PRO-VDH WIFI / NVIDIA RTX 3050 6 GB / 16 GB DDR4 / 500 GB NVMe

## Current milestone
M1 — Real bootable live foundation (candidate source, **not yet built or boot tested**).

## Implemented source
- `build/build-live.sh`: authenticates official Ubuntu ISO SHA256SUMS with pinned CD image signing key, validates the locked upstream SHA-256, creates an original OREZ layer, and preserves upstream BIOS/UEFI boot metadata with xorriso replay.
- `build/check-iso.sh`: checks ISO structure; explicitly not boot verification.
- `build/package-shell.sh`: builds small native OREZ Debian package for qualified Kubuntu hosts.
- `overlay/`: sumi-e wallpaper, KDE first-login autostart, welcome screen, read-only diagnostic tool. No privileged or remote services.
- `tests/`: source/unit tests.

## Unverified, blocking user installation
- Live ISO actual construction and boot on OVMF and physical PC.
- Whether casper on exactly Kubuntu 26.04.1 loads `zz-orez.squashfs` as a new top layer. Confirm with mount info inside VM; if not, change approach.
- Calamares installed-system support: **not integrated**; therefore first candidate is LIVE-ONLY, not an installer.
- NVIDIA 3050 driver, Secure Boot, Wi-Fi, Bluetooth, audio, installer/recovery and safety certification.
- Signed release distribution, cloud storage, trademark/licence obligations and full physical compatibility.

## Next actions (in order)
1. Verify branch/commit and workflow results on GitHub; do not infer success from this document.
2. Run `python3 -m unittest discover -s tests -v` and `bash build/package-shell.sh` on source.
3. Build manually on a sufficiently sized Linux runner by invoking the GitHub Actions `workflow_dispatch` for `OREZ Live Candidate`, or use a trusted Linux host.
4. Verify static boot metadata and confirm actual **OVMF live boot** in a disposable VM. Capture screenshots and mounted overlay evidence.
5. Refuse installation until the OREZ layer's installed-system persistence, disk safeguards, NVIDIA/Secure Boot and recovery are verified.
6. Add legal-release approval and a financially safe large-file delivery route, then provide a real verified ISO download.

## Persistent safety rules
Never format the user's NVMe or overwrite the Windows recovery USB. Do not silently disable Secure Boot, elevate AI permissions, enable remote access, or install proprietary NVIDIA drivers without appropriate user control and tests. Do not claim built, booted, installed, or released status without recorded evidence.

## 2026-11-04: First actual ISO build (new evidence)
- GitHub run: https://github.com/RezoxNemesis/OREZ-OS/actions/runs/41809241570
- Source commit: `fa7c59f63e03f97a418be7d1fa4725c382209c0e`
- CI source validation: **PASS**; full 5.1 GB upstream authenticated, OREZ live image constructed, ISO structure: **PASS**.
- ISO SHA-256 in ephemeral runner: `9cc63144be546d7fcc1b1c3edd091f70b404e7c1c7e080bd4fa4287234bc0137`
- **NOT** retained as download. VM boot and hardware boot at that commit: **NOT TESTED**.

### Next verification change
- Add only-if-explicitly-enabled unprivileged live-boot witness and a read-only/diskless QEMU casper smoke test. Source is implemented and locally unit tested; run success must be independently verified before claiming anything else.
