# OREZ OS — Verified Development Handoff

Date: 2026-11-04 (source creation; GitHub commit will be captured separately)
Repository: https://github.com/RezoxNemesis/OREZ-OS
Foundation: Kubuntu 26.04.1 LTS amd64, KDE Plasma 6
Target: AMD Ryzen 5 5600 / MSI B550M PRO-VDH WIFI / NVIDIA RTX 3050 6 GB / 16 GB DDR4 / 500 GB NVMe

## Current milestone
M1 — Real ISO generated and casper guest boot verified; graphical desktop validation FAILED; installation remains NOT QUALIFIED. Read the latest evidence below.

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

## 2026-11-04 readiness follow-up (source only)
- The UEFI emulator captures the original ~90-second screen and a later (~235-second) screen; human review is mandatory before marking KDE visually correct. A separate opt-in guest process witness now checks a live Plasma Shell and display manager without network or disk access. Verify the latest one-shot ISO build before promoting any milestone.

## 2026-11-04: stricter graphical VM test failed; must fix before M1 closure
- [GitHub run 41816102051](https://github.com/RezoxNemesis/OREZ-OS/actions/runs/41816102051): source/package **PASS**, full ISO **BUILT**, OREZ casper live-root marker **PASS**, but the new mandatory Plasma/display-manager process witness **FAIL** after the allotted QEMU run. This is a **real graphical readiness blocker**, not an overall boot success. OVMF screenshot step skipped because the separate GUI gate failed. No ISO was uploaded or installed.
- Read actual retained guest serial log and framebuffer: serial reaches `getty.target` and `Ubuntu 26.04.1 LTS kubuntu ttyS0`, but no confirmed `graphical.target` / display-manager / plasmashell. QEMU framebuffer is **black with visible pointer**. Networkless casper live boot also logged DNS failures during a background update attempt; do not confuse that with a verified desktop failure cause.
- Source improvement: test-only unprivileged GUI witness now starts at `multi-user.target` and reports display-manager, graphical and multi-user target states to isolated VM serial, even if graphical.target never starts. The workflow now captures OVMF screenshots even after a failed independent GUI process gate, provided the ISO was built. **These fixes are source-only until the next full test**.
- Temporary branch `build/live-orez-20261104-gui-gate-1` was used for the failed full CI run and is not a released or installable system. Current feature PR remains Draft. Do not merge or expose SSD installation.
- Next step: diagnose whether the direct-kernel `console=ttyS0` test causes a text-target-only boot or a genuine Plasma failure; inspect multi-user diagnostic markers and later OVMF screenshot in the next controlled build before changing the production boot path. Then implement and test Calamares installed-layer persistence and recovery solely on disposable virtual drives.

## 2026-11-04 live-only installer guard (source change)
- Added an explicit visible Calamares block for the **experimental ISO only**, returning 78 without launching the unqualified installer; added an `OREZ Installer — Unavailable` launcher and documentation. The native `orez-shell` Debian package intentionally **excludes** this override to preserve an existing host's Calamares program. Source tests and CI must pass before treating the guard as verified in a built ISO. This is not a disk-writing sandbox.

## 2026-11-04: Latest complete multi-gate VM results (authoritative)
- **Full controlled run:** [GitHub Actions #41817833118](https://github.com/RezoxNemesis/OREZ-OS/actions/runs/41817833118), source commit `ffea0796ad68315c175969db5d7469b172eeabea`, scratch branch `build/live-orez-20261104-diagnostics-2`.
- Native Debian package/source validation: **PASS**. Locked signed upstream Kubuntu 26.04.1 ISO, constructed OREZ overlay and ISO: **PASS**. Direct-kernel, offline/diskless casper OREZ filesystem witness: **PASS**. **Strict GUI gate: FAIL** — no verified Plasma shell process, and UEFI early/later screenshots both show only Kubuntu's splash. The overall full ISO job correctly returned FAILURE. No ISO published.
- Guest `OREZ_GUI_DIAG` at attempts 15 and 30: `display=active graphical=inactive multiuser=inactive`. Serial log contains a long `snapd.service` startup job, but **root cause of graphical failure remains unknown**; QEMU TCG, no network, virtual VGA and software rendering may contribute. Do not silently mask security/services just to get green CI.
- **Actual read-only Calamares source inspection:** `/etc/calamares/modules/unpackfs.conf` contains only `/cdrom/casper/filesystem.squashfs`, NOT OREZ `zz-orez.squashfs`: an install is **not** proven to retain OREZ. The upstream live image contains `/etc/sysctl.d/20-apparmor.conf` with `kernel.apparmor_restrict_unprivileged_userns = 0`. This is a reported live-only hardening override and must not silently persist in any installed system. Both were flagged **BLOCKED**.
- OVMF serial additionally logs `error: can't find command grub_platform`; firmware boots past menu to splash but must not be certified. UEFI screenshots captured around 90 and 235 seconds; **no graphical login** shown.
- Small boot evidence is GitHub Actions artifact `orez-casper-boot-evidence`, artifact ID `13315134427` (short retention). The findings above are preserved beyond artifact expiry.
- **Later feature source:** `b61f379bd5287c2dcc3ffcafefbf6d2897044ee2` adds a clearly visible *live-only* Calamares safety stub and excludes it from standalone `orez-shell` Debian package. First source run failed due an unmatched shell quote; fixed and [run #41818841716](https://github.com/RezoxNemesis/OREZ-OS/actions/runs/41818841716) **PASSED** tests/package. **The guard has not yet been ISO/VM validated.**
- Current development branch: `feature/orez-live-foundation-20261104`, [Draft PR #1](https://github.com/RezoxNemesis/OREZ-OS/pull/1). Keep **unmerged**, don't publish a user-installable ISO, don't touch owner's SSD or Windows 11 USB.
- **Next engineering actions:** investigate guest systemd/snapd/Wayland/virtual graphics and compare original Kubuntu behavior, qualify active Plasma/OVMF GUI without bypassing security, devise Calamares source layers that explicitly install OREZ and remove only live-only overrides, then disposable-virtual-disk installation/restore tests; only after those, MSI/RTX hardware Try mode and release distribution.

## 2026-11-04: Install-safe filesystem payload and next M1 diagnostic — verified source
- Source branch `feature/orez-live-foundation-20261104`, most recent implementation commit `a566ed8dfcf95e38295401082f4e37d62893b073` (verify HEAD). [Source checks #41830349537](https://github.com/RezoxNemesis/OREZ-OS/actions/runs/41830349537): **PASS** native package, test suite, shell scripts.
- Implemented `image/installer/installed-files.txt`, `build/build-install-payload.sh`, `image/installer/orez-unpackfs-candidate.conf` (inactive), and `image/installer/README.md`. The ISO builder includes a separate `orez-install.squashfs`; `build/check-iso.sh` checks its identity and that it excludes live-only services/installer guards. The standalone `orez-shell.deb` uses the identical allowlist.
- Calamares supports two ordered filesystem sources. However the two-layer config is deliberately NOT ACTIVE; the live-only `/usr/bin/calamares` warning continues to block unqualified SSD installation. The candidate excludes the reported live-only AppArmor user namespace override during base extraction. Future real disposable-VM installs must prove actual persistence and effective security; an inactive candidate is not a fix by itself.
- Added read-only `orez-gui-verify` diagnostics for systemd jobs, failed services and KDE processes, plus dynamic KVM/TCG selection for the isolated VM. These are test-only; no host disk or network attached.
- [One-shot full ISO run #41830767974](https://github.com/RezoxNemesis/OREZ-OS/actions/runs/41830767974) started from `build/live-orez-20261104-install-payload-3`: source/package and updated ISO/payload static checks **passed**; guest graphical test was **in progress at last observation**, so DO NOT claim it succeeded or failed until checking current GitHub evidence.
- **Next actions:** fetch full-run result and serial/UEFI evidence; if GUI fails, inspect new OREZ_GUI_JOBS / OREZ_GUI_FAILED_UNITS diagnostics and compare to upstream Kubuntu behavior before changing defaults. Then qualify inactive Calamares 2-layer candidate only on disposable virtual disks with LUKS2/Btrfs, recovery and non-target disk preservation. Preserve Windows USB and SSD; no ISO distribution.

## 2026-11-04: Immediate Try/Plasma CI crash diagnosed
- [Full run 41834799223](https://github.com/RezoxNemesis/OREZ-OS/actions/runs/41834799223) **FAILED** within seconds in QEMU setup, before guest Linux even started: `qemu-system-x86_64: -device usb-tablet: No 'usb-bus' bus found for device 'usb-tablet'`. It does NOT prove an OS regression. ISO and install-safe overlay were built and verified structurally.
- The earlier confirmed 1280x800 frame has "Try Kubuntu" button on the LEFT (center x≈350, y≈638), "Install Kubuntu" on right. Only the disposable, diskless and networkless QEMU guest may receive test inputs.
- Source changes add explicit `qemu-xhci` USB controller and `usb-tablet,bus=orez-xhci.0`, plus fail-closed frame layout verification (two button areas and adjacent background) before any left-button QMP click. The guest log must also include `kubuntu-installer-prompt`. Tests check both accepted and rejected PPM frames.
- New source is NOT a boot success claim. Need next source CI result and a single controlled full live VM verification. Do not publish installation ISO or touch SSD/Windows recovery USB.

## 2026-11-04: visual framebuffer evidence and virtual GPU comparison
- [Full image run 41854833186](https://github.com/RezoxNemesis/OREZ-OS/actions/runs/41854833186) at implementation `0783f969f6d415458918f4fc9ea649af537f608d`: upstream signature/ISO build/static OREZ installation payload checks PASS, guest casper OREZ live filesystem PASS, Try-selection PASS, and KDE display-manager + plasmashell process PASS. **Visual M1 gate correctly FAILED:** captured framebuffer remained virtually black with mouse pointer even after 22 and 46 seconds, both with lit_pixels=0.01% and five quantized color bins. Full workflow therefore **FAILED**. UEFI firmware output still did not establish a usable desktop. No ISO was published.
- Added `build/check-graphical-frame.py` to reject black/pointer-only frames. Unit and package validation [41854379824](https://github.com/RezoxNemesis/OREZ-OS/actions/runs/41854379824) PASS.
- The next experiment is a **test-VM-only** `OREZ_VM_VGA=virtio` backend instead of standard VGA, grounded in QEMU's documented 2D VirtIO device. Fail-closed guard refuses to click unexpected Try-screen layout and preserves rejected screenshot. Source validation [41858934338](https://github.com/RezoxNemesis/OREZ-OS/actions/runs/41858934338) PASS.
- [One-shot full run 41859076291](https://github.com/RezoxNemesis/OREZ-OS/actions/runs/41859076291) was **in progress** at handoff writing. DO NOT infer any VirtIO result until CI completes and artifact screenshots are visually inspected.
- **Release blockers persist:** Calamares still ignores the separate installed OREZ payload until an actually qualified two-source installer is implemented; live AppArmor sysctl disablement is present; encryption, snapshots, rollback, target PC/NVIDIA, security and distribution certification are untested. Live-only Calamares guard remains enabled; PR remains Draft and unmerged.

## 2026-11-04 final VirtIO retry diagnosis (run 41874348585)
- [GitHub full run 41874348585](https://github.com/RezoxNemesis/OREZ-OS/actions/runs/41874348585), source `b057a96400e53500fc40c2107184323649991d50`: signed upstream ISO and OREZ install-only SquashFS construction **PASS**; initial Kubuntu Try screen recognized **PASS**; isolated QMP Try click acknowledged **PASS**; guest OREZ live-root and Plasma/display-manager process markers **PASS**; **visual display FAILED**. Two delayed VirtIO 2D frames (22/46 secs) both entirely black (`lit_pixels=0.00%`, one color bin). The full job correctly concluded FAILURE; OVMF still no verified graphical login, no ISO published.
- The visual failure is within CPU-only QEMU/KWin Wayland, not proof of NVIDIA 3050 incompatibility. The guest serial reports long `snapd.seeded.service` startup and `kwin_wayland`, but not a demonstrated cause. KDE has public reports of Wayland/llvmpipe issues on non-accelerated QEMU; avoid equating one unsupported video adapter with physical hardware.
- Source-only follow-up: add explicitly documented `KWIN_COMPOSE=Q` experiment in `/etc/xdg/plasma-workspace/env/90-orez-vm-software.sh` **guarded** by `orez.verify=1`, which only the disposable VM test supplies. It must never enter install-only OREZ SquashFS or standalone .deb, and never change normal boot settings. The QPainter test has NOT yet been built or verified in an ISO. No unlimited retries or GPU paid infrastructure.
- Additional **live-only Calamares guard verification** in `build/check-iso.sh` briefly failed shell syntax on commit `d0003c5`; corrected and source CI **passed** at [run 41875624369](https://github.com/RezoxNemesis/OREZ-OS/actions/runs/41875624369). This changed image check was NOT part of 418743's older source snapshot.
- Latest next action: source validation for compositor experiment, one controlled full build, inspect guest framebuffer. Installer remains disabled and PR remains Draft. M1 graphical is NOT closed, M2 installer/rollback and NVIDIA/Secure Boot remain unverified.
