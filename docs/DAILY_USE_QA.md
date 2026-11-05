# Daily-use implementation and QA — 5 November 2026

These results are from source checks, a browser preview and real native desktop
applications in a disposable Ubuntu/KWin container. They are **not** a booted
OREZ ISO, PC installation, Android guest or target-GPU qualification.

## Verified results

| Scenario | Evidence and interpretation |
|---|---|
| Owner wallpapers | qa3-09: Rest visible, Horizon selected, Rest restored using real Plasma controls |
| Native Settings | qa3-09: native window, effective BreezeDark apply and BreezeLight restoration verified |
| VLC | qa3-09: real software H.264/AAC playback, advancing position, stable pause, 10-second seek and resume; virtual audio peak 4217; physical sound/accelerated decode untested |
| Android manager | qa3-09: actual native controls displayed; missing KVM start correctly denied; no guest/image installed and no Play Store downloads |
| Loaded desktop API | qa3-09: 2 GiB allocation; 12 real D-Bus calls, maximum 105.01 ms; not graphical latency/FPS or enforced 6 GiB proof |
| SuperTux | qa3-15: real game process/window and key delivery; manual review shows level-introduction frames only. Gameplay progress is NOT qualified despite harness success |
| Brave/YouTube | qa3-09: Brave sandbox namespace creation denied; separate YouTube request denied by proxy 403. No browsing/download/playback pass |
| Source | qa3-11 and qa3-23: 74 tests passed, including Android boundaries/resource admission and wallpaper checks |
| Preview | qa3-08: 60/60 desktop/mobile browser tests passed with the owner wallpaper; separate design preview, not real mobile OS |
| Package | qa3-16 and qa3-24: 23-path owner/mode/content audit passed. New paths still need the signed-base collision audit |

## Environment corrections and remaining work

Rootless Docker reports `MemoryLimit=false`, `CgroupDriver=none`. Historical
2/4 GiB and current 6 GiB requests were not enforced. Captured root cgroup values
represent a shared 16 GiB environment. The runner now records actual daemon
support and can refuse resource qualification with
`OREZ_REQUIRE_RESOURCE_LIMITS=1`. CPU-profile claims also require verification.

The environment definition installs the native apps, Java and QEMU/OVMF/tools.
No package can create missing host KVM/GPU access or override provider sandbox/
network policy. See ../environment/README.md for publication requirements. The
32 GiB VFS-backed workspace needed removal/rebuild of its own temporary QA image
and cleanup of its own build cache to complete testing; test evidence was kept.

Next game check must explicitly select `levels/world1/welcome_antarctica.stl`,
wait for active level rendering, then verify position change/jump and sustained
frame pacing. Current images only prove application rendering and delivered
input; do not call this successful gameplay or an Android game test.

## Failures preserved

- qa3-01: Brave download lacked the managed CA trust bundle.
- qa3-02: APT `_apt` could not read the default 0400 build-secret CA file.
- qa3-04: corrected 0444 existing trusted CA secret; TLS/signature checks kept.
- qa3-07: Settings default empty-key interpretation and unsupported VLC/SuperTux
  CLI options failed. Corrected using effective defaults and installed help.
- qa3-09: VLC/settings passed; incorrect game-level lookup failed; browser blocked.
- qa3-15: harness passed process/input checks, but visual review did not establish
  gameplay. This limitation is retained alongside the unmodified raw result.
- qa3-10: tool image built, but APT warned about the Brave index CA. Final recipe
  uses the same trusted CA secret and strict update error handling; its new run
  must be verified independently.

All attempts retain `result.json`, logs and report screenshots. Native frames
remain separate from rendered log pages. The compact screenshot bundle includes
failed captures with original references and hashes; no image is a generated OS
mock-up. Google account login is never captured. The durable ledger under
evidence/2026-11-05-daily-use/ records final artifact details.

## Final environment and later checks

- qa3-17 failed because the read-only source mount inherited mode 0600. The
  recipe now installs a 0644 copy before invoking preflight as UID 1500.
- qa3-21 installed all tools and ran normal-user preflight, QEMU and Java, but
  failed while WORKDIR made another full VFS filesystem copy. This failure is
  retained, not rewritten into a successful image export.
- qa3-25 reused that verified tool layer without the redundant WORKDIR mutation
  and **exported successfully**: `orez-qa:20261105`, image
  `sha256:3d500a65817e2d44d70a90d63ffab2db8fb0d3688a7c0bb66eae7af4c5215308`,
  about 4.22 GB logical image size. Default runtime user is `orez-test`.
- QEMU 10.2.1 and OpenJDK 21.0.12.1 ran; normal-user preflight confirmed tools
  available but no KVM or render device. This is not an Android/VM boot.
- qa3-19 correctly refused resource qualification before container creation;
  qa3-20 compiled 14 Python source files; qa3-22 checked the read-only network
  status command, reporting unavailable hardware/services without changing them.
- Native network/Bluetooth UI pages, dummy-password masking, search and open/
  close screenshots are still outstanding. The installed QA modules need a
  runnable desktop container; this workspace has under 1 GiB free after retaining
  the image and cannot copy its 4.22 GB VFS root for another container. Publish
  on the documented larger supported host. Hardware connections remain untested.
- Exact duplicate PNG files were hardlinked locally to reclaim space. Every
  original filename and every image byte was preserved; the bundle verifies
  all unique capture hashes. No failure screenshots were removed.
