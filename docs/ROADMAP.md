# OREZ OS — evidence-based engineering roadmap

Connectivity follow-up: native Wi-Fi/internet/Bluetooth controls, Realme hotspot/
USB tethering, consented phone mirroring, LAN/Bluetooth/USB file transfer and
safe eject are required. See [CONNECTIVITY.md](CONNECTIVITY.md) for providers,
visible controls and the still-pending physical test matrix.

## New owner priorities and next implementation sequence

1. Publish/qualify the documented QA environment with actual KVM, usable graphics,
   enforced resource limits and a supported browser sandbox. Native successful
   component tests do not close the graphical ISO boot milestone.
2. Qualify visible upstream and OREZ ISO boot, then disposable-disk installation,
   reboot, encrypted recovery and preservation of non-target disks.
3. Measure 6/16 GiB full-system workloads and energy/thermals; optimize from
   profiles, preserving security and responsiveness. See PERFORMANCE.md.
4. Complete consumer Android/Play provider licensing and isolation review, then
   actual YouTube/free casual-game install/play/restart/remove tests. Current
   Android manager source is not a working consumer Play Store.
5. Complete target MSI/NVIDIA/Realme tests and owner-only access audit. After all
   agreed PC-readiness gates pass, apply and verify the requested private repo
   visibility; keep public until then. No install release is approved now.

## 5 November implementation checkpoint

The full master blueprint exists. Expanded QA now verifies a visible native KWin/Plasma desktop in a disposable software-rendered Ubuntu container, actual application windows, launcher input, window management and workspaces. This advances component testing, while ISO/UEFI graphical boot remains open. A separate responsive browser preview passes all 60 local desktop/mobile cases; it does not qualify phone hardware or the installer.

Source checks pass 52 cases. Ten APT transition/failure cases and eleven native capability scenarios have successful evidence, including C++ compilation, Git, SQLite, Blender CPU rendering, video processing and software OpenGL. See [QA scenarios](QA_SCENARIOS.md) for exact limits and failed attempts. Screenshot infrastructure retains failures and distinguishes source reports, browser views and native desktops. Source/preview CI is automatic; expensive native checks remain manual-only.

Next: qualify a booted Plasma desktop on a suitable VM; validate real Calamares installation and dpkg registration on disposable virtual disks; test reboot, encryption, rollback and independent data restoration. Hardware and signed distribution follow those gates. Local fixture package upgrades/downgrades are now tested; signed production updates and whole-system recovery are separate gates.

## Original milestone ledger and historical evidence

| Milestone | Planned outcome | Current status |
|---|---|---|
| M0 | Source, requirements, repository rules, handoff | Partial |
| M1 | Verified bootable live image and KDE session | **In progress**; ISO and direct-kernel casper VM test pass |
| M2 | Safe installer, Btrfs/Snapper, LUKS2, recovery and backup | Not implemented |
| M3 | Exact MSI/NVIDIA/Realme hardware qualification | Not tested |
| M4 | Functional 0.1 alpha with installation and Connect | Blocked by M2/M3 |
| M5 | Integrated beta, branded Android companion, optional advisory AI | Not implemented |
| M6 | Stable desktop 1.0 and maintenance pilot | Not implemented |

**Verified milestones:** GitHub ISO build https://github.com/RezoxNemesis/OREZ-OS/actions/runs/41809241570 ; direct-kernel VM boot proof https://github.com/RezoxNemesis/OREZ-OS/actions/runs/41810060479 . These are not UEFI, graphical desktop, Secure Boot or installer validation.

**Next gates:** OVMF UEFI graphical boot, OREZ desktop witness, boot options and NVIDIA qualification, safe disposable-disk installer and recovery, legally compliant signed image distribution. Do not format the user's SSD or overwrite their Windows 11 recovery USB.

- M2 preparation: read-only installed-root qualification code added; the M2 installer itself and full installed-system recovery remain **not implemented**. The two 26.04.1 upstream reports LP #2172113 and LP #2172138 are explicit release blockers pending proof.

**M1 blocker confirmed:** run 41816102051 passed ISO/live root and failed graphical-process readiness. OREZ user desktop is not yet qualified. Source diagnostics have been improved, but must be tested in a new controlled run. Do not advance M1 or M2 installation milestones from structural-only results.

**Verified detailed M1/M2 findings:** [run 41817833118](https://github.com/RezoxNemesis/OREZ-OS/actions/runs/41817833118) passed ISO construction and casper OREZ-layer boot but failed Plasma graphical readiness; UEFI screenshots still show the Kubuntu splash. Actual Calamares source copies only `filesystem.squashfs`, so installed OREZ persistence is NOT implemented. The live AppArmor override is confirmed and must be omitted from qualified installs. A live-only installer-warning stub is source/package-tested (41818841716) but not yet verified in a new full ISO. **M1 remains in progress, M2 release-blocked**. Preserve evidence; do not release installation media.

**M2 implementation progress (not installer readiness):** an install-safe, explicitly allowlisted OREZ SquashFS is generated alongside the live ISO; a two-source Calamares candidate and AppArmor-exclusion rule are staged but **inactive**, with the visible experimental installer block retained. Same allowlist controls host `.deb`. Source validation passed #41830349537 and ISO/static candidate validation passed its step in run #41830767974. Full graphical VM gate and actual installed-system tests remain outstanding. M1/M2 release gates are not closed.

**M1 further gate:** 41854833186 proved process startup but FAILED the new nonblack-frame requirement (both std-VGA delayed captures 0.01% lit). Do not declare graphical desktop usable until a manually inspected framebuffer confirms it. VirtIO comparison 41859076291 is an experimental VM test, not hardware qualification.

**Latest M1 verdict (2026-11-04):** Full QPainter [run 41882928635](https://github.com/RezoxNemesis/OREZ-OS/actions/runs/41882928635) FAILED a real visible-desktop test: zero lit framebuffer pixels despite running Plasma. M1 live-root pass is NOT equivalent to graphical release. Prefer an A/B control with pristine Kubuntu or accelerated GPU-backed VM before further CPU-only renderer changes. M2 synthetic installer checks passed (41883465838) but the real SSD installation and rollback gates remain blocked.

**Verification strategy:** Following QPainter's still-black VirtIO result, run a once-only, checksum-pinned pristine Kubuntu baseline under identical software-only VirtIO conditions to isolate upstream from OREZ changes. Source tests passed #41887319606; control #41887435151 was in progress at last verification. M1 release remains blocked until actual desktop can be visually confirmed.

**Latest Nov 5, 2026 evidence:** pristine Kubuntu also produced a black software-only VirtIO desktop [run 41889832695](https://github.com/RezoxNemesis/OREZ-OS/actions/runs/41889832695), which establishes an inadequate graphical control environment rather than an OREZ-specific KWin fault. M1 still requires a real visible GPU-backed/physical desktop proof. M2 installation payload passed actual signed Kubuntu collision check with 16/16 files and zero conflicts [run 41937702881](https://github.com/RezoxNemesis/OREZ-OS/actions/runs/41937702881), and native Debian package audit passed 16/16 files with no maintainer scripts [run 41938238699](https://github.com/RezoxNemesis/OREZ-OS/actions/runs/41938238699). These are static gates; installer remains disabled pending real installed-disk and recovery tests.
