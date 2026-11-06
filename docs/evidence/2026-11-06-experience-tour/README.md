# Actual OREZ experience tour — 6 November 2026

The owner requested a full screen tour, boot/login/storage explanations and five
ideas in each of nine categories. Latest direction: official native Linux Brave;
YouTube optional; prioritize consented scrcpy phone mirroring. No existing online
account is needed: installer/first setup must create the local owner account
before normal sign-in. That complete installation-to-session path is unfinished.

**31 final scoped native component scenarios pass; native Brave is blocked.**
The count uses final evidence once per scenario: desktop 5, network settings 4,
Calendar/Reuz 8, Store 9, VLC 1, login-theme/installer-guard/Connect 3, game 1.
Some Store cancellation checks instrument the launch boundary; they are not
Android or external-provider tests. Login is SDDM test mode, not authentication.
A passing installer guard means installation was refused, not performed.

- qa10-16: actual nested Plasma wallpaper/palettes, app search, Dolphin copy,
  rename, Trash/Undo with byte equality, tabs/split, KWin workspaces and a
  controlled panel restart preserving Dolphin/Konsole. Tabs/search/captures
  visually reviewed; nested F2/F3 keyboard delivery is not qualified.
- qa10-09: real native Network/Bluetooth opening and closing, Settings search,
  dummy Wi-Fi password mask/reveal/remask/clear/cancel. No saved connection,
  physical radios, real credentials or Internet authentication.
- qa10-06: native Calendar/Reuz and Store UI; actual VLC playback progression,
  Space/mouse pause/resume, F fullscreen, Ctrl+Q. Brave 1.98.63 from the older
  QA image cannot create required sandbox namespaces. Its shell wrapper returns
  zero despite a fatal browser exit; the scenario correctly records BLOCKED.
  This version differs from staged image-layer Brave 1.99.55. No sandbox bypass.
- qa10-15: actual SDDM theme with masked dummy input, actual live installer
  guard exits 78, actual KDE Connect empty-device window. No phone paired.
- qa10-17: SuperTux actual fullscreen 1440x900, native Right/Space/Escape input.
  Visually reviewed position changes about x=96 → x=482 and a visible pause
  menu. Software rendering only; audio disabled, no RTX/FPS qualification.
- qa10-14: actual shipped welcome HTML rendered in memory by host Chromium at
  desktop and phone widths; no file-URL navigation or native Brave launch claim.
- qa10-18: **172 source tests pass**; no runtime/product source changed this
  turn. qa10-19: gallery works at 1440/390 widths, 29 tour stops, 45 proposals,
  every selected image served and all then-present 293 image references hashed.

All 11 failed local attempts remain: 02 (overstrict Xauth discovery), 03/04/08
(nested rename input), 05 (copied QA script read permissions), 07 (Connect
window-title assumption), 10/13 (Dolphin menu label/accessibility visibility),
11 (Playwright executable lookup), 12 (file-URL policy), 15 (SDL key tap missed
before playable scene). Final fixes use the existing owned display, readable
fixture scripts, inspected real menu positions, PID-based window discovery,
existing host Chromium document rendering and held game input. No authentication,
browser sandbox, host policy or container privilege was weakened. Run 07 proves
fullscreen rendering but its before frame is the introduction; final 17 is the
usable before/after gameplay evidence. Repeated failed attempts are not hidden.

The container used UID 1500 for UI tests, software Mesa/Xvfb/KWin, no KVM/DRI,
no physical devices, no host bind mounts and no effective cgroup memory limit.
Only a private system bus/NetworkManager fixture was started; all interfaces
were unmanaged. Outbound networking was disconnected after signed package setup.
KWin's realtime capability was dropped in this private fixture, with executable
bytes checked unchanged; no production file capability was altered.

## Reproduction

Use the current `environment/orez-qa.Dockerfile` dependencies (the retained compact
image predates Qt Widgets/Qt Test/SDDM additions). Build the current `.deb` first.
For a new isolated desktop run:

```
OREZ_SCENARIO=tour python3 build/run-with-evidence.py \
  --name native-tour --kind package-container --output dist/evidence/new-tour \
  --timeout 240 -- bash build/run-desktop-container.sh dist/evidence/new-tour/native-details
```

Use a fresh evidence directory. `OREZ_SCENARIO=connectivity` runs the existing
network-settings fixture. Container creation/removal is handled by that runner.
Do not run these scripts on the owner's real desktop. Default network is none;
missing packages must be prepared separately through authenticated sources.

`tour-components.py` runs as UID 1500 in a fresh Xvfb + D-Bus session, with an
owned `/evidence` directory. Copy the repository SDDM theme to
`/input/orez-theme`, the live-only installer guard to `/input/orez-installer-guard`,
and the script to `/input/tour-components.py`; make copied inputs readable to
UID 1500. The installed package supplies the wallpaper. Each invocation requires
a fresh `/evidence/tour-components`; `OREZ_TOUR_COMPONENT_FILTER=fullscreen-game`
selects only the game. Never install the live-only guard into an existing OS.

The existing daily-apps.py, store.py and store-app-input.py fixtures require
separate ordinary-user Xvfb/D-Bus sessions and fresh output paths; they exercise
real installed native components. Only dummy data is used.

`build/create-experience-tour.py --output <fresh-directory>` builds the gallery
from retained qa10 evidence and `docs/experience/tour.json`. This dated manifest
is evidence selection, not a general promise that future runs have identical
filenames. `tour-gallery.mjs` checks a preview served at 127.0.0.1:4183; its web
screenshots are gallery screenshots, not OS screenshots. All 45 future acceptance
criteria are proposals and were not represented as completed tests.

No new full ISO or installed-size measurement was produced. Original unsafe ISO
and separately packed app layer remain unchanged. Installation/owner-login,
recovery, NVIDIA/Secure Boot, real radio/phone/audio/USB and 6-GiB acceptance gates
remain open. See FIRST_BOOT_AND_TOUR.md and AI_HANDOFF.md for the latest state.


## Published tour

[Browse all 29 screens on GitHub](https://github.com/RezoxNemesis/OREZ-OS/blob/8fabdcc81cb4e67aa98c6925a9ad8829c3d4ac1f/TOUR.md).
[Direct ZIP download: 245 original PNGs plus the offline HTML tour and ideas](https://github.com/RezoxNemesis/OREZ-OS/archive/8fabdcc81cb4e67aa98c6925a9ad8829c3d4ac1f.zip).
The ZIP is 105,851,922 bytes (about 105.9 MB). Every archived PNG hash was checked
against its manifest after downloading the actual GitHub ZIP. All 19 original
runs and 11 failures remain in the gallery; one boot frame is historical.
The subsequent download-integrity check has its own [report screenshot](download-verification.png)
and [machine-readable result](github-download.json), separate from that frozen
archive. CI screenshots are in the workflow artifact, not silently added to it.

Extract and open index.html on desktop or Android; images/ contains ordinary PNG
files. The direct GitHub TOUR.md page also displays every selected screen.
No ISO or installation permission is included in this download.


Exact implementation CI [42149300734](https://github.com/RezoxNemesis/OREZ-OS/actions/runs/42149300734)
passed on f3e88c0c56485830d82f9ad09a69b7047a5cf197. The full ISO job was skipped.
[Separate CI screenshot/report artifact](https://github.com/RezoxNemesis/OREZ-OS/actions/runs/42149300734/artifacts/13471862095)
(about 211.2 MB; GitHub may require sign-in). Native Vulkan/NVIDIA or hardware
qualification is not implied by source/browser CI.
