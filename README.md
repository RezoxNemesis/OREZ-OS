# OREZ OS — Real Linux Build (0.1 Live Candidate)

Latest Store work: [native Store and actual Android direction](docs/OREZ_STORE.md).
Official Linux apps are preferred unchanged. Android consumer runtime and app
compatibility remain pending; no browser shortcut substitutes for YouTube.
Read [the latest verified handoff](docs/AI_HANDOFF.md) before continuing.

Latest boot work: [offline cache correction and actual initrd audit](docs/OFFLINE_BOOT_QA.md). The new VM run reaches systemd but still has no usable desktop; owner authentication remains a release blocker.

Latest component validation: [native controls, real-version upgrades and gameplay](docs/CONTINUED_QA.md). OREZ remains pre-alpha; no physical installation is approved.

**Start here:** [single master blueprint](docs/MASTER_BLUEPRINT.md), [latest verified handoff](docs/AI_HANDOFF.md), [test screenshots and evidence rules](docs/TESTING_AND_SCREENSHOTS.md).

The separate [phone-friendly interactive preview](preview/README.md) now has working navigation, appearance controls and demo device permissions. `npm run preview:build` exports a portable `dist/OREZ-Preview.html` and an HTTPS-hostable PWA. It is labelled as a browser preview and cannot install or control an OS. The native Linux project remains a distinct, unqualified live candidate.

**State: initial ISO constructed and casper direct-kernel VM live-root boot verified. Native Plasma now renders in an isolated container; graphical ISO/UEFI boot, hardware and installation remain unqualified.** [Expanded QA](docs/QA_SCENARIOS.md) records real desktop/capability checks and 60 passing browser-preview scenarios, with screenshots and failed attempts preserved. This repository builds a real Ubuntu/Kubuntu-based bootable ISO by adding an OREZ desktop filesystem layer to the official, signed Kubuntu 26.04.1 LTS image. The native project is separate from the browser preview and does not replace Android.

## What works in the source

- Existing real KDE Plasma Linux environment, native apps, terminal, files, network and settings from the Kubuntu base.
- Original OREZ sumi-e wallpaper and a first-login branding setup with no root privileges.
- OREZ Welcome and read-only hardware/status commands (`orezctl status`, `orezctl hardware`).
- Official ISO SHA-256 verification **and** GPG signature validation against pinned Ubuntu CD Image Signing Key.
- Build process retains the upstream EFI/BIOS boot artifacts using `xorriso -boot_image any replay`, without building an unsigned bootloader.
- No disk formatting, remote listeners, AI privilege broker, hidden settings or automatic installer actions.

## Important limitation

This is a **live-USB boot engineering candidate only**. We have proved the squashfs layer is mounted by upstream casper in a disposable, headless VM (see run 41810060479), but NOT UEFI/Plasma login, NVIDIA acceleration or that the installed OS incorporates the OREZ layer. **Do not use its installation option**. Keep your Windows 11 USB and all SSD data untouched. An installable OREZ ISO will require its own tested and documented installation/rollback release gate.

## Build on Linux (x86-64; 8 GB RAM and 12+ GiB available disk)

You can run this from an appropriately provisioned Linux environment (not from your phone itself):

```bash
sudo apt-get update
sudo apt-get install --yes curl gnupg xorriso squashfs-tools zstd python3 ca-certificates
bash build/build-live.sh
bash build/check-iso.sh dist/OREZ-OS-0.1-live-amd64.iso
```

The build script can use a previously downloaded official image via `OREZ_UPSTREAM_ISO=/path/to/kubuntu-26.04.1-desktop-amd64.iso` but still verifies its signature-backed checksum. No privileged access is required for building (except installing build tools).

## Mobile-first workflow

The repo contains one controlled GitHub Actions workflow for manual dispatch or explicit one-shot `build/live-*` branches. Hosted runner disk space is an explicit risk, and complete 5 GB ISO artifacts **are not uploaded** by default because GitHub's free storage quotas are much smaller. Build checks publish a lightweight SHA and result summary, not an imaginary download link. An authorized distribution path must be set up before users can download a full ISO.

### Project handoff

See [`docs/AI_HANDOFF.md`](docs/AI_HANDOFF.md) for verified progress and the next steps. Never treat this candidate as a released or safe-to-install operating system until boot and recovery tests are recorded.

**Licensing:** The modified casper hook and its retained original are GPL-2.0-or-later; see [source and notices](third_party/casper/README.md). Original OREZ-authored source and wallpaper reserved to the project owner; no blanket public reuse license has been granted. The upstream Kubuntu, Linux, KDE and other components keep their own licenses and attribution/redistribution obligations. Do not publish a modified binary image without confirming those obligations.

## First full-image construction result
An explicit one-shot GitHub build [run #41809241570](https://github.com/RezoxNemesis/OREZ-OS/actions/runs/41809241570) successfully authenticated Kubuntu 26.04.1 and constructed a live ISO from commit `fa7c59f`, with digest `9cc63144be546d7fcc1b1c3edd091f70b404e7c1c7e080bd4fa4287234bc0137`. This ISO was **not uploaded** and has **not** passed boot tests. A subsequent development change adds a VM-only direct-kernel casper witness to prove that the OREZ overlay is actually accessible at boot, without changing any installed disks or allowing network access.

## Native settings entrypoints
OREZ Welcome, Settings, and Phone Connect desktop app entries appear in KDE launcher. Standard KDE System Settings exposes real system preferences. `orezctl appearance disable` is a per-user, reversible off switch for OREZ first-login wallpaper. `orezctl ai` reports all AI automation disabled. KDE Connect requires upstream package installation and secure, explicit user pairing.

## UEFI virtual-firmware evidence
The [UEFI VM build/test run 41811624570](https://github.com/RezoxNemesis/OREZ-OS/actions/runs/41811624570) passed. Inspection of its OVMF screenshot shows TianoCore/GRUB loading the remixed ISO and Kubuntu splash, **not** the OREZ graphical desktop. GRUB logged `can't find command grub_platform`; this requires qualification. The captured test is not an installer, Secure Boot or physical-PC validation.

## Latest release gate results (2026-11-04)
The [full diagnostic run 41817833118](https://github.com/RezoxNemesis/OREZ-OS/actions/runs/41817833118) built a real ISO and started Linux with the OREZ live layer, but **failed** the required Plasma graphical session test. Two OVMF screenshots still show the upstream Kubuntu boot splash. Read-only installer inspection confirmed that the stock Calamares source only copies the original `filesystem.squashfs` (not OREZ), and its live AppArmor configuration disables a user-namespace restriction. **This is not a safe, installable release.**

The new live-only Calamares warning stub is source/package-tested ([run 41818841716](https://github.com/RezoxNemesis/OREZ-OS/actions/runs/41818841716)) but must still be checked in a freshly built ISO. The separate native Debian package intentionally excludes that installer override. Development remains on [Draft PR #1](https://github.com/RezoxNemesis/OREZ-OS/pull/1), not merged to main.

## Latest evidence checkpoint
The test-only QPainter fallback did **not** resolve CPU-only QEMU's black KDE screen: [41882928635](https://github.com/RezoxNemesis/OREZ-OS/actions/runs/41882928635) has an overall FAIL result. Its live root, KDE process witnesses and guarded Try action passed, but both desktop frames were solid black; UEFI mode still did not reach a visually working desktop. This is not proof of RTX 3050 incompatibility. Read the CURRENT VERIFIED STATE section at the beginning of `docs/AI_HANDOFF.md` before attempting more work. No ISO is released for installation.

## November 5 verified snapshot
The **original pristine Kubuntu** also displays a black virtual desktop in the same software-only QEMU after Try: [run 41889832695](https://github.com/RezoxNemesis/OREZ-OS/actions/runs/41889832695). A better graphics test environment or physical Try-only verification is needed; this is not proof about the RTX 3050. The real installed-file payload and native Debian package now each pass matching 16-file allowlist checks: [collision run 41937702881](https://github.com/RezoxNemesis/OREZ-OS/actions/runs/41937702881), [package audit 41938238699](https://github.com/RezoxNemesis/OREZ-OS/actions/runs/41938238699). **No OREZ installation is yet qualified.** See `docs/AI_HANDOFF.md` for the evidence ledger and remaining gates.
