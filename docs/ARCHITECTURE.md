# OREZ OS architecture — implemented vs planned

Latest owner scope (5 November 2026): **finish the first PC release before Android emulation.** Native Brave/VLC/Linux games, explicitly authorized web YouTube, owner login, OREZ Calendar/Reuz, themes, AI permissions and connectivity take priority. See [FIRST_PC_RELEASE.md](FIRST_PC_RELEASE.md) for implementation, test limits and blocking gates. No installable release is approved. This supersedes older Android-first and web-YouTube-prohibited statements for the first release only.

Connectivity follow-up: native Wi-Fi/internet/Bluetooth controls, Realme hotspot/
USB tethering, consented phone mirroring, LAN/Bluetooth/USB file transfer and
safe eject are required. See [CONNECTIVITY.md](CONNECTIVITY.md) for providers,
visible controls and the still-pending physical test matrix.

## Daily-use additions — 5 November 2026

The native package now includes the owner's Rest/Horizon wallpaper packs and an
unprivileged Android development/testing manager. Guest state is private to the
user, with explicit setup/start/stop/resource controls/reset/remove and no
startup daemon. Google SDK/image software is not bundled. Consumer Play Store
licensing/runtime qualification is unresolved; see ANDROID_APPS.md.

Performance policy is demand-driven: no resident OREZ performance service,
automatic AI load or automatic Android guest. `orezctl performance` reads memory
and pressure once; `orezctl power` opens native KDE controls. Resource admission
checks guard Android starts. Budgets and unverified targets: PERFORMANCE.md.

The daily QA fixture tests native wallpaper changes, KDE settings, VLC and a
Linux game independently from the browser preview. Resource enforcement must
be checked: this workspace's rootless daemon does not enforce requested limits.
The publishable test-tool image and provider requirements are in
../environment/README.md. These dependencies are never the desktop release.

**Foundation:** official Kubuntu 26.04.1 LTS / KDE Plasma 6 / amd64 Linux, Ubuntu packaging, normal desktop apps, UEFI-capable image. No new kernel fork.

**Implemented 0.1:** `build/build-live.sh` signature-checks upstream and remixes an original SquashFS overlay; `build/check-iso.sh` validates media structure; `build/test-casper-vm.sh` tests live overlay presence in a diskless VM. `overlay/` includes KDE styling and original ink wallpaper, welcome/diagnostics, visible `orezctl` and normal KDE Settings/KDE Connect bridges. GitHub CI verifies small packages and source.

**Not implemented:** installed-system OREZ integration, dedicated Settings KCM, Btrfs/LUKS/Restic recovery, full Android companion, sandboxed AI services/permission broker, signing and maintained update channel. Users retain standard Linux install, development and file access where supported by the Kubuntu base. OREZ never silently becomes root, enables remote shell or installs AI without permission.

Boot evidence must distinguish source built, image built, casper VM tested, UEFI tested, actual hardware, installer, and release.

**New development tooling:** React/TypeScript/Vite browser preview under `preview/`, independently tested at desktop and phone viewport sizes; generated offline cache and a portable single-file HTML export. It has no backend or host bridge. Native `.deb` now explicitly depends on System Settings and KDE Connect, matching its launcher commands. Docker-based APT lifecycle and Xvfb-native-window checks are isolated test infrastructure, never part of the deployed OS.

Every test uses a fresh evidence directory with source/log hashes and screenshots. The small PR job includes source, packaging and browser checks; the larger Ubuntu package integration job is manual-only. Neither advances ISO or hardware gates automatically.
