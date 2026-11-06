# Native controls and upgrade follow-up — 5 November 2026

OREZ remains pre-alpha. These are component tests in a rootless Ubuntu container,
not a booted installation, hardware certification or an authorization to install.
The previous 340-image collection remains available separately. [New 534-PNG download](https://github.com/RezoxNemesis/OREZ-OS/archive/62575c4655607163e67abefebbe5025ccd575865.zip)
is published and every downloaded PNG hash verified. Implementation `bcbaae4`
passed [CI 42021318734](https://github.com/RezoxNemesis/OREZ-OS/actions/runs/42021318734):
78 source tests, 23-file package audit, preview build and 60 browser tests.
Exact commit/artifact details and expiry are recorded in AI_HANDOFF.md.

## Implemented in this follow-up

- One native package version source, revision `0.1.0-2`, exact artifact selection,
  stale-version rejection and `orezctl version` reading installed dpkg state.
- Reusable native connection UI tests with dummy-only password handling. The
  private NetworkManager fixture leaves every interface unmanaged, has no network
  access and grants no extra Polkit/container capability. It ships only as QA code.
- A real previous-artifact upgrade scenario in addition to ten synthetic APT
  transitions/failures. No signed update service or privileged helper was added.
- Compact QA dependency image from the pinned Ubuntu base, replacing the local
  VFS image chain that exhausted storage. Image is 4,173,178,310 logical bytes;
  this is **not the size of OREZ OS**. Normal UI user is UID 1500.
- Game test now requires the actual outdoor scene and sustained key presses.
  A successful process launch or introduction screen cannot qualify gameplay.

## Verified evidence and its limits

| Check | Result / scope |
|---|---|
| Source regression | 78 passed in final local qa4-30; final committed-source CI recorded in handoff |
| Current package | Exactly 23 allowed files, expected revision, modes/owners and no maintainer scripts; qa4-10 |
| Stale artifact | Previous revision correctly rejected by the expected-version audit; qa4-06 |
| Actual package upgrade | 5 checks passed: previous artifact, user state, non-admin denial, changed payload/version with state intact, repeat installation; qa4-13 |
| APT error/recovery scenarios | All 10 passed: corrupt archive, missing dependency, unauthorized install, upgrade, implicit downgrade refusal, explicit package rollback, purge/reinstall and retained opt-out/project data; qa4-15 |
| Actual Kubuntu collision audit | All 23 paths passed, no missing/extra/overwritten paths; GitHub run 42014023573, job 127199879972, manifest matching this revision |
| Native window controls | Network and Bluetooth open/close verified with actual compositor input; final qa4-29. Bluetooth correctly displays no adapter |
| Settings search/password | All 4 native control scenarios passed in qa4-29: open/close, search/clear, dummy masking/reveal/re-mask/clear/cancel; zero connection saved |
| VLC | Real H.264/AAC playback progressed 2.650312 → 5.152121 seconds; pause held position, seek reached 15.152121 seconds, resume passed; virtual decoded-audio peak 4217; qa4-16 |
| SuperTux | qa4-27 shows actual outdoor level, movement/scrolling and death response. Reviewed HUD position changes from about X96/Y577 to X587/Y1653. Software renderer; no Android, RTX, sustained-FPS or game-compatibility certification |
| Repository access audit | Four settings endpoints remain unreadable with available credentials; qa4-24 is execution/report evidence, **not** a passed exclusivity audit. No access settings changed |

The Kubuntu audit downloaded the actual pinned ISO and verified its SHA-256 in CI.
The report is preserved from decoded successful job logs. The tiny artifact ZIP
was blocked by the workspace's HTTP 403, so its contents were not independently
downloaded/hash-verified locally. Static path safety does not establish Calamares,
symlink targets, ownership, encrypted boot, effective AppArmor or recovery.

## Failure history is part of the result

- qa4-09 built the package but used incomplete audit CLI arguments; qa4-10 used
  the required package/manifest/report options and passed.
- qa4-12 sent Alt+F4 to Xwayland instead of the outer compositor. Later runs
  exercise the actual window close successfully.
- qa4-14/26 exposed UI automation issues: readiness, hidden cached Qt sidebar
  controls, and a combo box named by its current value. Do not relabel them green.
- qa4-18 hit a stale transient accessibility object. Actual pointer selection
  subsequently opened the real Wi-Fi editor; qa4-20/21 captured its controls.
- qa4-16's initial game harness returned success, but visual review still showed
  the introduction. qa4-27 uses sustained input and an explicit scene gate;
  only that later run qualifies the observed playable session.
- qa4-22/23 stopped before desktop launch because the running shell wrapper was
  edited. Static syntax passed; immutable reruns retained separate evidence.
- Dummy password masking was captured in exploration. Later reveal/cancel frames
  raced the inspection session shutdown and were not retained; no success is
  inferred from those missing frames. The final automated lifecycle qa4-29 passes with all required frames retained.

## Remaining release gates

No physical Wi-Fi/Bluetooth, Realme pairing/tethering, USB storage/eject, NVIDIA,
Secure Boot, disk installation or recovery was tested here. No KVM/GPU exists;
rootless Docker cannot enforce memory/CPU budgets. A 6 GiB profile is unqualified.
Brave's sandbox and YouTube's proxy restrictions remain; they were not disabled.
Consumer Play Store runtime/licensing and Android app/game execution remain open.

The earlier approximately 5.1 GB development ISO has not been rebuilt/qualified
with this revision. There is no safe public installation ISO. The target SSD,
Windows USB, firmware and main branch remain untouched. Full supported-host
requirements and the publishable dependency recipe are in environment/README.md.
