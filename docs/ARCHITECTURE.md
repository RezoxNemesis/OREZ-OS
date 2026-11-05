# OREZ OS architecture — implemented vs planned

**Foundation:** official Kubuntu 26.04.1 LTS / KDE Plasma 6 / amd64 Linux, Ubuntu packaging, normal desktop apps, UEFI-capable image. No new kernel fork.

**Implemented 0.1:** `build/build-live.sh` signature-checks upstream and remixes an original SquashFS overlay; `build/check-iso.sh` validates media structure; `build/test-casper-vm.sh` tests live overlay presence in a diskless VM. `overlay/` includes KDE styling and original ink wallpaper, welcome/diagnostics, visible `orezctl` and normal KDE Settings/KDE Connect bridges. GitHub CI verifies small packages and source.

**Not implemented:** installed-system OREZ integration, dedicated Settings KCM, Btrfs/LUKS/Restic recovery, full Android companion, sandboxed AI services/permission broker, signing and maintained update channel. Users retain standard Linux install, development and file access where supported by the Kubuntu base. OREZ never silently becomes root, enables remote shell or installs AI without permission.

Boot evidence must distinguish source built, image built, casper VM tested, UEFI tested, actual hardware, installer, and release.

**New development tooling:** React/TypeScript/Vite browser preview under `preview/`, independently tested at desktop and phone viewport sizes; generated offline cache and a portable single-file HTML export. It has no backend or host bridge. Native `.deb` now explicitly depends on System Settings and KDE Connect, matching its launcher commands. Docker-based APT lifecycle and Xvfb-native-window checks are isolated test infrastructure, never part of the deployed OS.

Every test uses a fresh evidence directory with source/log hashes and screenshots. The small PR job includes source, packaging and browser checks; the larger Ubuntu package integration job is manual-only. Neither advances ISO or hardware gates automatically.
