# OREZ OS — Real Linux Build (0.1 Live Candidate)

**State: source implemented, boot compatibility NOT YET VERIFIED.** This repository builds a *real* Ubuntu/Kubuntu-based bootable ISO by adding an OREZ desktop filesystem layer to the official, signed Kubuntu 26.04.1 LTS image. This is not the earlier HTML simulation and it does not run Android directly.

## What works in the source

- Existing real KDE Plasma Linux environment, native apps, terminal, files, network and settings from the Kubuntu base.
- Original OREZ sumi-e wallpaper and a first-login branding setup with no root privileges.
- OREZ Welcome and read-only hardware/status commands (`orezctl status`, `orezctl hardware`).
- Official ISO SHA-256 verification **and** GPG signature validation against pinned Ubuntu CD Image Signing Key.
- Build process retains the upstream EFI/BIOS boot artifacts using `xorriso -boot_image any replay`, without building an unsigned bootloader.
- No disk formatting, remote listeners, AI privilege broker, hidden settings or automatic installer actions.

## Important limitation

This is a **live-USB boot engineering candidate only**. We have not proved that the squashfs layer is mounted by the exact upstream casper, that NVIDIA acceleration works, or that the installed OS incorporates the OREZ layer. **Do not use its installation option**. Keep your Windows 11 USB and all SSD data untouched. An installable OREZ ISO will require its own tested and documented installation/rollback release gate.

## Build on Linux (x86-64; 8 GB RAM and 12+ GiB available disk)

You can run this from an appropriately provisioned Linux environment (not from your phone itself):

```bash
sudo apt-get update
sudo apt-get install --yes curl gnupg xorriso squashfs-tools ca-certificates
bash build/build-live.sh
bash build/check-iso.sh dist/OREZ-OS-0.1-live-amd64.iso
```

The build script can use a previously downloaded official image via `OREZ_UPSTREAM_ISO=/path/to/kubuntu-26.04.1-desktop-amd64.iso` but still verifies its signature-backed checksum. No privileged access is required for building (except installing build tools).

## Mobile-first workflow

The repo contains one controlled GitHub Actions workflow for manual dispatch or explicit one-shot `build/live-*` branches. Hosted runner disk space is an explicit risk, and complete 5 GB ISO artifacts **are not uploaded** by default because GitHub's free storage quotas are much smaller. Build checks publish a lightweight SHA and result summary, not an imaginary download link. An authorized distribution path must be set up before users can download a full ISO.

### Project handoff

See [`docs/AI_HANDOFF.md`](docs/AI_HANDOFF.md) for verified progress and the next steps. Never treat this candidate as a released or safe-to-install operating system until boot and recovery tests are recorded.

**Licensing:** OREZ-authored source and wallpaper reserved to the project owner; no blanket public reuse license has been granted. The upstream Kubuntu, Linux, KDE and other components keep their own licenses and attribution/redistribution obligations. Do not publish a modified binary image without confirming those obligations.
