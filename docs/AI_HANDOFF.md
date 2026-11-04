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

## 2026-11-04 verified ISO & real casper boot results
- Source `fa7c59f63e03f97a418be7d1fa4725c382209c0e`, [CI run 41809241570](https://github.com/RezoxNemesis/OREZ-OS/actions/runs/41809241570): exact Kubuntu image signed-checksum + SHA verification **PASS**; new ~5 GB OREZ live ISO construction and ISO structure **PASS**. ISO SHA-256: `9cc63144be546d7fcc1b1c3edd091f70b404e7c1c7e080bd4fa4287234bc0137`; not retained as download.
- Source `cd24b3063d9d5361265ea1b1b88ed10163ed401a`, [CI run 41810060479](https://github.com/RezoxNemesis/OREZ-OS/actions/runs/41810060479): full ISO construction and disposable QEMU direct-kernel casper boot witness **PASS**. Local serial marker `OREZ_BOOT_PROOF=CASPER_AND_OREZ_LAYER_PRESENT` confirmed; boot log stored as small workflow artifact. QEMU was intentionally stopped by test timeout after witnessing startup (exit 124).
- **No** UEFI/OVMF firmware boot, graphical Plasma proof, physical boot, Secure Boot, NVIDIA/Wi-Fi/phone hardware certification, safe installer or released ISO is claimed by these runs.
- Current source adds read-only `orezctl security`, KDE Connect integration entrypoints, standard Settings, reversible wallpaper opt-out; verify against latest PR source CI before claiming them as tested.
- Highest priorities: UEFI smoke proof, graphical login, Calamares installer persistence and recovery in disposable VM, hardware Try mode, legally compliant ISO download. Do not touch SSD or Windows installer USB.

## 2026-11-04 UEFI VM firmware evidence and current head
- Source commit `eca6329f6408d033ec134abb806d4c704c6edfed`, [successful GitHub run 41811624570](https://github.com/RezoxNemesis/OREZ-OS/actions/runs/41811624570): package source validation, signed upstream ISO rebuild, casper QEMU boot witness, and OVMF UEFI screenshot capture all **PASS** as executed checks.
- Captured `uefi-screen.ppm.gz` from `orez-casper-boot-evidence` artifact. **Human inspection:** TianoCore UEFI firmware and Kubuntu boot splash visible; **OREZ Plasma graphical desktop NOT seen**. EFI serial text shows `GNU GRUB version 2.14` and warning `error: can't find command grub_platform`; assess warning before calling firmware path qualified. Secure Boot is not proven. No installer tested.
- New source adds launcher entries OREZ Connect, Settings and read-only Hardware Preflight. Source CI at commit `dd3d53dc1be1b658ccba76caf285c3df43c75e30` [run 41812228159](https://github.com/RezoxNemesis/OREZ-OS/actions/runs/41812228159) passed. Do not equate CI source checks with physical PC compatibility.
- Current branch: `feature/orez-live-foundation-20261104`; draft [PR #1](https://github.com/RezoxNemesis/OREZ-OS/pull/1), deliberately **not merged**.
- **Next:** fix/assess boot warning, obtain explicit KDE GUI proof, then separate OVMF Secure Boot and hardware compatibility checks. Build safe Calamares/Orez installer and Btrfs/LUKS/recovery exclusively in disposable VMs before real PC release.
- No multi-GB ISO download published; last artifact is only tiny VM boot logs/screenshot. The user's Windows recovery USB and NVMe remain untouched.

## 2026-11-04 ongoing work — installer audit source
- Added proposed `build/audit-installed-root.py` and `tests/test_installed_audit.py`, with 7 deterministic fixtures covering OREZ-installed identity, reported AppArmor issue, missing LUKS crypttab option, missing Btrfs root and escaping symlinks.
- These are **static read-only tests, not an installer or a security certification**; no user disk or USB is accessed. Run full CI on this commit before treating them as integrated. Do not claim LUKS2, snapshots, Secure Boot, NVIDIA or physical PC are qualified.
