# OREZ OS — Verified Development Handoff

## Latest verified live-boot follow-up — 5 November 2026

- Last confirmed implementation: **`d8193b7ef1c45b088e96241745776d68484768da`**,
  branch `feature/orez-live-foundation-20261104`, PR #1 draft/open/unmerged.
  Main remains `fb0661d6cfb8850104d86b3377eef12a7ecd68ed`; repository is public
  per the owner's instruction until all PC-readiness gates pass. This final
  checkpoint is documentation/evidence only with `[skip ci]`; read actual HEAD.
- Exact implementation [CI 42027937005](https://github.com/RezoxNemesis/OREZ-OS/actions/runs/42027937005)
  **passed**. Decoded job `127246748045` confirms **87 source tests**, the
  **23-path package audit at 0.1.0-2**, preview production build and **60 browser
  tests**. Full ISO job skipped; actual ISO/VM work below was local.
  [CI screenshots artifact](https://github.com/RezoxNemesis/OREZ-OS/actions/runs/42027937005/artifacts/13415300743)
  is 200,884,515 bytes, GitHub digest
  `1b2d79ee01373b563d927c9d571c038988d08086bc73dbd62a1dcfa272d3741d`,
  expires **19 November 2026, 12:34:46 UTC**. Metadata/logs verified; artifact
  ZIP not independently downloaded here. The earlier implementation `82183ea`
  also passed CI 42026148407; it is not the final harness revision.
- **New screenshot ZIP: 80 original PNGs / 200 captures / 19 local attempts**:
  https://github.com/RezoxNemesis/OREZ-OS/archive/a98c92f105bb00a7b4ecc6ffce2bf5a9db0bdbd6.zip
  Orphan branch `downloads/screenshots-2026-11-05-live-boot`; includes all six
  failed executions. Repeated identical frames are stored once. Gallery/manifest
  distinguish reports and actual VM windows. The public ZIP omits raw logs;
  local evidence retains logs and frozen fixture inputs. Delivery verification
  metadata is `docs/evidence/2026-11-05-vm-followup/github-download.json`.
- **New real development ISO built and retained locally**:
  `dist/vm-candidate/OREZ-OS-0.1-live-amd64.iso`, **5,073,338,368 bytes**
  (5.073 GB / 4.725 GiB), SHA-256
  `8ec11599942f871759d7a2950b26430c8cb51a35d068283d09f348c2771e40e9`.
  Built from **`82183ea8fbc5c1a759576a5ff0b814b936402bed`**; later changes affect
  diagnostics/docs, not ISO payload. Official signing-key/digest verification,
  static ISO structure, installation payload and disabled installer guard pass
  (qa5-08). Exported ISO checksum passes again (qa5-19). No public ISO release,
  no usable live-desktop qualification and **no installation approval**.
- Implemented normal-user, offline, diskless software OpenGL VM diagnostics,
  real QMP/SDL captures, private controls, input/digest/root rejection and bounded
  cleanup. Added QEMU GUI/OpenGL dependencies to the QA recipe. Added safe HTTP
  download resume and disk preflight credit for existing allocated input bytes;
  full signature/digest checks remain mandatory. Two interrupted downloads were
  retained as failures and successfully resumed before building.
- **Live desktop remains blocked.** Initial qa5-09/10 stopped at QMP's
  `no surface` during graphics modesetting. Corrected qa5-12 completed a
  600-second pristine control with no recognized Try screen or usable desktop;
  serial logs show offline APT/DNS retries during startup. Its successful exit
  means capture completed, not a desktop pass. OREZ UEFI qa5-13 reached
  OVMF/GRUB, then black frames; SDL capture timed out around 390 seconds.
  qa5-15 moved only host SDL windows to (0,0), fixing clipped captures; later
  frames are full 1280×800. No guest input or security setting changed by that
  correction. The final harness automates this tested host-window adjustment.
- **New owner-control blocker:** qa5-18 reads the actual upstream base's casper
  `25adduser` hook, which writes passwordless full sudo for the live account.
  Effective initrd/runtime/installed behavior remains untested. Audit/harden
  live sudo and Polkit with owner authentication before sensitive live use.
  No such rule was added or executed by this work. The installer blocker does
  not certify administrator isolation. See OWNER_CONTROL.md.
- GRUB warning attribution is now verified: qa5-14 extracts byte-identical
  configs from both actual ISOs, each containing bare `grub_platform` at line 23.
  It is inherited upstream; missing-desktop causation is not established.
- The normal-user host GL preflight passes with **software llvmpipe**, not a GPU.
  No KVM, `/dev/dri`, NVIDIA or enforced Docker resource budgets exist here.
  QA recipe was edited but no new dependency image/environment was published.
  The old compact image still needs rebuilding to include the new GUI modules.
  Temporary rootless lab was removed after preserving evidence/ISO; approximately
  16 GiB workspace space remains. Only its regenerable original-ISO cache was
  removed. No PC disk, Windows USB, firmware, credentials or access policy changed.
- Durable report: VM_GRAPHICS_QA.md and
  `docs/evidence/2026-11-05-vm-followup/` (19-attempt ledger, VM outcomes,
  image provenance, CI metadata, boot-config comparison and live-policy finding).
  Local bundle `dist/OREZ-live-boot-followup-screenshots.zip` is 5,495,085 bytes,
  SHA-256 `ae8e87d64742f5964125bd53f26c69b40ef52ad67082fbb0bd4e54df8494a94b`.
  The previous 534- and 340-image downloads remain below.

Exact next actions:
1. Verify branch/PR/HEAD and the exact passing implementation above. Read the
   latest evidence before changing boot/graphics settings. Preserve all failures.
2. Diagnose offline live startup from qa5-12's serial log and audit the actual
   initrd/live auth rules. Avoid treating its unfinished startup as a confirmed
   Plasma/VirGL failure or enabling network/security bypasses to hide the issue.
3. Publish the updated QA recipe on a supported host with actual KVM, usable
   graphics, enforced resource controls and sufficient disk. Recheck pristine
   and OREZ UEFI/desktop behavior there; no identical blind TCG reruns.
4. Qualify owner-authenticated live elevation, then actual installation only on
   disposable virtual disks: dpkg registration, non-target disk preservation,
   AppArmor, LUKS boot, signed updates, independent backup and restore.
5. Test MSI/RTX/Realme hardware, 6/16 GiB workloads and power; complete native
   identity, phone integration and consumer Android licensing/runtime gates.
   None is established by screenshots of the separate browser preview.

Next-chat prompt: "Continue RezoxNemesis/OREZ-OS. Read AGENTS.md and the latest
docs/AI_HANDOFF.md, verify GitHub branch/PR/CI and actual workspace artifacts,
then work on the next unclosed release gate. Preserve owner-only control,
public-until-PC-ready visibility, SSD/Windows USB and every failed test capture.
Do not claim a working live desktop, safe installer or Android Play Store from
processes, previews, static audits or this session's software-GL preflight."

## VERIFIED implementation, CI and 534-image download — 5 November 2026

- Last confirmed implementation commit: **`bcbaae4e88b56a3d3fd3ea10031bbde7c5ca62c3`**,
  branch `feature/orez-live-foundation-20261104`, draft/unmerged PR #1.
- Exact-commit CI **SUCCESS**: [42021318734](https://github.com/RezoxNemesis/OREZ-OS/actions/runs/42021318734),
  source job `127224513638`. Decoded logs confirm **78 source cases**, the
  expected-version **23-file package audit**, preview production build and
  **60/60 browser tests**. Full ISO job skipped. Native container checks were local.
- [Additional CI preview/screenshots artifact](https://github.com/RezoxNemesis/OREZ-OS/actions/runs/42021318734/artifacts/13411507944):
  `13411507944`, 200,821,799 bytes; GitHub reports SHA-256
  `a175a79d929703adf1b72b3e827dd14ce67bfeddd71c1683cc9a4c3ccabff20e`.
  Expires 19 November 2026 at 11:46 UTC (17:16 IST). This artifact was not
  independently downloaded locally; its metadata and job logs were verified.
- **Direct new PNG ZIP (534 images, about 124 MB):**
  https://github.com/RezoxNemesis/OREZ-OS/archive/62575c4655607163e67abefebbe5025ccd575865.zip
  Isolated orphan evidence branch `downloads/screenshots-2026-11-05-followup`.
  Downloaded successfully: 124,263,582 bytes, archive SHA-256
  `971937d5c9a436b18da280d4becedc4e6faf6366a9b5b2b167ea892f94d28102`.
  All **534 original PNG hashes** match the local bundle. GitHub may regenerate
  archive bytes; image hashes are the stable integrity evidence. Gallery and
  manifest cover 557 captures / 31 local attempts, including failures. The public
  download omits raw logs; the local workspace bundle retains them. CI captures
  are in the separate artifact above. The older 340-image download remains below.
- Bulk publication used normal authenticated Git transport after a dry run,
  avoiding hundreds of per-image API writes and the per-file ZIP size limit.
  No release upload, credential/policy bypass, merge or visibility change.
- This handoff follow-up changes documentation/evidence metadata only and uses
  `[skip ci]`. Verify its implementation diff against `bcbaae4` is empty; do not
  claim a second CI run for this documentation checkpoint.
- Source of truth: CONTINUED_QA.md, environment/README.md and the adjacent
  `docs/evidence/2026-11-05-native-followup/` ledger. Completed checks, failure
  qualifications, remaining release blockers and exact next actions are below.


## Native upgrade and controls checkpoint — 5 November 2026

- Starting confirmed source HEAD: `cb8db4e8337fd0b19e8126de2a023b942aff000d`,
  branch `feature/orez-live-foundation-20261104`; PR #1 remains draft/unmerged.
  Main is `fb0661d6cfb8850104d86b3377eef12a7ecd68ed`; repository remains public.
  This checkpoint precedes the new implementation commit. Its exact SHA and CI
  are added in the verified follow-up above this section; recheck actual GitHub HEAD.
- Native component revision is `0.1.0-2`, with one version source, exact artifact
  selection/stale-package rejection, and installed-version diagnostics. Actual
  previous-artifact upgrade passes 5 checks, preserving project data, appearance
  opt-out and private Android settings. All 10 synthetic APT recovery/error cases pass.
- Final local source: 78 tests passed (qa4-30); all 18 Python helpers and build
  shell scripts parse (qa4-31). Package audit passes all 23 paths and expected revision.
- All 4 native controls scenarios pass (qa4-29): network/Bluetooth open-close,
  Settings search/clear, dummy password mask/reveal/re-mask/clear/cancel. No
  connection is saved. No radio, pairing, password authentication or encryption
  of a saved credential was tested. Bluetooth explicitly reports no adapter.
- VLC playback/pause/seek/resume and virtual audio pass again (qa4-16). Reviewed
  qa4-27 captures establish a real SuperTux level, movement/scrolling and death
  response; no Android game, physical GPU or sustained FPS qualification.
- Expanded actual Kubuntu collision audit passes all 23 paths: run 42014023573,
  job 127199879972 on 4bb77b1, manifest identical to this revision. Original ISO
  checksum passes in CI. Report recovered from logs; artifact download was HTTP
  403. This closes static path collision only, not installation/recovery.
- Compact QA image built: `orez-qa:20261105-compact`,
  `sha256:e6427926838b638347acca36ea9ba9a168f4f0e95059391c17c1f94d4e73da3d`,
  4,173,178,310 logical bytes. Old disposable VFS images were removed after a
  verified 31-blob desktop-image backup to temporary RAM storage; source and
  screenshots remain. Environment is not published. Canonical build instructions
  and host requirements are in environment/README.md.
- New local bundle: `dist/OREZ-native-followup-screenshots.zip`, 122,584,231 bytes,
  SHA-256 `b2cc7660b7c9315916b559891d7a6f8518c7730e99008f51b0cbddaf2c7601c9`.
  Contains 534 original PNGs, 557 capture references and 31 attempt records,
  including failures. Native desktop screenshots are separate from report pages.
  The older 340-image download remains available below.
- Read-only collaborator/invitation/key/workflow-permission audit remains
  unverified (qa4-24). Available credentials cannot read those settings. No
  admin/visibility policy changed; no access-control workaround was used.
- Durable results: CONTINUED_QA.md and docs/evidence/2026-11-05-native-followup/.
  Important failed attempts and manual visual qualifications are recorded there;
  do not count qa4-16's earlier intro screen or qa4-24's audit-script exit as
  gameplay/security proof. Failed test runs were not overwritten.
- No safe installation release; approximately 5.1 GB is the historical development
  ISO size, not a newly qualified build. No SSD/USB/firmware changes.

Exact next actions:
1. Verify actual branch/PR/CI and read the latest verified checkpoint above.
2. Publish the supplied QA environment on a supported host with actual KVM,
   graphics, enforced cgroups and enough disk; do not weaken sandbox/proxy policy.
3. Reproduce visible pristine-Kubuntu and OREZ UEFI/live desktop boot on that host.
4. Qualify installation only on disposable virtual disks: registered native package,
   non-target disk preservation, effective AppArmor, LUKS boot/unlock, updates,
   independent backup and restore. Installer remains disabled until these pass.
5. Test actual MSI/RTX/Realme hardware, 6/16 GiB workloads and power behavior;
   finish consumer Android provider/licensing, browser/YouTube and phone-transfer
   gates. Signed OREZ update infrastructure and local security monitoring remain
   planned, not implemented. Keep owner-only control and public-until-PC-ready policy.


## Direct GitHub screenshot download — 5 November 2026

- Owner requested a direct GitHub ZIP containing all 340 PNG screenshots.
- Published an isolated evidence branch `downloads/screenshots-2026-11-05`,
  snapshot `7dbd3dbd9ded644c644b1af7bce0a8835a2c94a9`, containing 340 original
  PNGs, gallery, manifest and README. This is not an OS or installer release.
- Download: https://github.com/RezoxNemesis/OREZ-OS/archive/7dbd3dbd9ded644c644b1af7bce0a8835a2c94a9.zip
- Downloaded that URL successfully and verified all 340 PNG SHA-256 hashes
  against the original local bundle. Archive details: the adjacent evidence
  github-download.json. GitHub may regenerate ZIP bytes; image hashes are the
  stable proof. This ZIP omits raw log files; the original local ZIP retains them.
- The release-asset endpoint rejected upload authentication (401); no release
  was visible afterward. Used the supported Git data API and standard GitHub
  source archive instead. No credentials, security settings or policy bypasses.
- Main and implementation are unchanged; this source-branch follow-up changes
  documentation only and uses [skip ci]. Prior implementation CI remains
  42001391558 on 4bb77b1. PR #1 remains draft/unmerged.

## VERIFIED DAILY-USE COMMIT AND CI — 5 November 2026

- Tested implementation: **`4bb77b1149461b3dc1a72b29432970d91f92324b`**, branch
  `feature/orez-live-foundation-20261104`, draft/unmerged PR #1. Main remains
  `fb0661d6cfb8850104d86b3377eef12a7ecd68ed`; repository remains public.
- GitHub CI **SUCCESS**: [42001391558](https://github.com/RezoxNemesis/OREZ-OS/actions/runs/42001391558),
  job `127157215150`. Actual logs confirm **74 source tests**, **23-file package
  audit**, production preview build and **60/60 browser tests**. ISO job skipped.
  Native container tests were local, not in this GitHub job.
- [CI preview/screenshots artifact](https://github.com/RezoxNemesis/OREZ-OS/actions/runs/42001391558/artifacts/13402323459):
  `13402323459`, 200,784,515 bytes, SHA-256
  `59c70ed821e5ee17f9a07b96aec664abeb4725f9e727d04eba56ed4452c76156`.
  Expires 19 November 2026 (14:51 IST / 09:21 UTC); recheck after expiry.
- All local captures including failures: `dist/OREZ-daily-use-QA-screenshots.zip`,
  **105,857,301 bytes**, SHA-256
  `dff73929ec712251d79c6dd93215c28f1493472520d4e693cf1ffb750468b6a9`.
  Extract and open index.html: **340 unique original PNGs covering 551 capture
  references and 25 attempt records**. Hash-set comparison verifies all unique
  PNG captures were included. Local ZIP is a supplied workspace artifact, not a
  permanent GitHub release. Two native frames and the ledger are committed.
- qa3-21's report screenshots initially failed at full disk. After reclaiming
  duplicated PNG storage without changing bytes/paths, the preserved result/log
  were rendered into 41 report screenshots. The failed build was not rerun or
  relabelled successful. qa3-25 independently verified final image export.
- New owner requirements after implementation commit are documented in
  UPDATES_AND_GUARD.md: signed upgrade path, no silent security-policy weakening,
  owner-authorized privilege grants, local bounded monitoring, uncertain alerts
  without work interruption, no perfect identity/zero-false-positive promise.
  This monitoring/update infrastructure is **not implemented**. No extra root
  service or security setting change was made to satisfy a promise on paper.
- Three proposed differentiators are in FUTURE_DIFFERENTIATORS.md; no untested
  superiority claim or automatic additional implementation is implied.
- This is a documentation/evidence-only follow-up, marked `[skip ci]`; verify
  actual HEAD and that its implementation diff from the tested SHA is empty.
  Do not claim this follow-up ran a second CI suite.
- Status: pre-alpha, no safe install release. Last reported development ISO is
  approximately 5.1 GB; latest changes are not in a newly qualified ISO and final
  installed size is unknown. The 4.22 GB QA dependency image is **not** the OS.

## DAILY-USE IMPLEMENTATION CHECKPOINT — 5 November 2026

This section supersedes older counts/resource-profile wording below.

- Starting verified HEAD: `3aef3fe12965cf11bb3b5895afc5ac228eac9124`, branch
  `feature/orez-live-foundation-20261104`; PR #1 draft/unmerged; main unchanged.
  This checkpoint is prepared before the new implementation commit. Exact
  committed-source CI and final commit are recorded in the follow-up above it.
- Implemented: original owner wallpaper packs (Rest default/Horizon optional),
  experimental normal-user Android development manager, bounded guest settings,
  memory admission check, one-shot performance diagnostics, native power/network/
  Bluetooth/files shortcuts and read-only connection status. No privileged helper,
  automatic Android/AI load or consumer Play certification claim.
- Local source checks: 74 passed (qa3-23); package 23-file audit passed (qa3-24);
  preview 60/60 passed with owner wallpaper (qa3-08). Native Settings and actual
  VLC play/pause/seek/decoded virtual audio passed (qa3-09). See DAILY_USE_QA.md
  for failures and the limited SuperTux process/input result (intro frames only).
- Working Play Store/Android games are **not delivered**. Google SDK use is for
  permitted development/testing; no SDK or guest installed, KVM absent, consumer
  provider/licensing/isolation still unresolved. Free casual games are the first
  requested Android targets. Google never gains a host administrator identity.
- QA image built: `orez-qa:20261105`, ID
  `sha256:3d500a65817e2d44d70a90d63ffab2db8fb0d3688a7c0bb66eae7af4c5215308`.
  Native apps, Java, QEMU/OVMF and network/Bluetooth tools installed; normal-user
  preflight/QEMU/Java ran. Environment not published. Its documentation gives
  exact build steps and provider requirements. Final build qa3-25 passed after
  failed trust/mode/storage attempts, all retained.
- Rootless Docker does **not enforce** configured RAM/CPU profiles. Historical
  2/4 GiB and new 6 GiB labels are not performance certification. New runner
  enforcement guard passes its rejection test. No KVM/GPU; Brave sandbox and
  YouTube proxy blocks remain. Test storage is nearly full; no blind retries.
- Network/phone requirement: standard visible Wi-Fi, internet, Bluetooth,
  Realme hotspot/USB tethering, LAN/Bluetooth/USB transfers and scrcpy mirroring.
  Native page open/close/search/dummy-password screenshots still pending due
  disk-limited container startup. CONNECTIVITY.md specifies actual hardware tests
  and safe controls; latest protocol versions depend on the radio hardware.
- RAM channels: CPU/firmware configure dual-channel, Linux uses it. Owner DIMM
  count/placement remains unknown; do not claim verified mode or silently tune
  XMP/voltage. See HARDWARE.md.
- Ownership: owner admin verified, full collaborator/app/key audit incomplete;
  no access settings changed. Public now; private only after PC-readiness gates.
- No new ISO, physical-device access, installer approval or recovery proof.
  The expanded 23-path payload needs a fresh signed-base collision audit.

### Exact next actions

1. Verify new branch head and source CI, then preserve final evidence metadata.
2. Publish documented QA environment on ≥80 GiB host with supported KVM, graphics,
   cgroup enforcement and browser sandbox. No policy bypass or fake devices.
3. Capture real NetworkManager/Bluetooth Settings open/close/search/password-mask
   dialogs with dummy data. Test SuperTux's active starting level, not just intro.
   Then qualify visible upstream/OREZ ISO boot and disposable-disk installation.
4. Test actual Realme/MSI radio/tethering/mirroring/file-transfer matrix and target
   NVIDIA/Secure Boot, 6/16 GiB performance, energy/stability and RAM layout.
5. Complete consumer Android provider review and real Play Store/game validation.
   Preserve owner-only administration and finish actual GitHub access audit.
6. Keep PR draft, main/physical disks untouched. Update this handoff with evidence,
   not inferred successes; private repository transition waits for PC readiness.

> Correction, 5 November 2026: Docker reports `MemoryLimit=false` and
> `CgroupDriver=none`. Earlier 2/4 GiB and current 6 GiB profiles were requested
> configurations, not enforced limits. Native successes remain component
> evidence; no low-RAM full-OS performance was established.


## FINAL VERIFIED EXPANDED-QA COMMIT / CI — 2026-11-05

- Implementation commit: **`ba8b86adf979e553ad3bfefae6ff6856dd4afa0f`**, branch `feature/orez-live-foundation-20261104`, [draft PR #1](https://github.com/RezoxNemesis/OREZ-OS/pull/1), still unmerged. Main remains `fb0661d6cfb8850104d86b3377eef12a7ecd68ed`.
- **GitHub CI SUCCESS:** [41988662713](https://github.com/RezoxNemesis/OREZ-OS/actions/runs/41988662713), source job `127115379957`. Verified logs: **52 source tests**, package build and **16-file audit**, production preview build, **60/60 browser cases in one run**. Full ISO job skipped as intended. Native container checks ran locally, not in this GitHub job.
- [Download the CI preview and screenshots](https://github.com/RezoxNemesis/OREZ-OS/actions/runs/41988662713/artifacts/13397520627): artifact `13397520627`, 139,649,053 bytes, SHA-256 `2c9372dde9e5bc092a1e5973b9b171ad36be104844818265727a5da53780ca38`, expires **19 November 2026 at 07:41 UTC**. Do not claim continued download availability after expiry without checking.
- **All local test screenshots, including failures:** `dist/OREZ-expanded-QA-screenshots.zip`, 46,186,436 bytes, SHA-256 `bb542c3eab9c51a058e36b4b2cec845449a0503637e65270a06ec497b48d84cb`. Extract and open `index.html`. It contains **152 unique unedited PNGs covering 381 original capture references**, all 16 local attempt records and raw logs/results. Exact duplicates are stored once, with original paths mapped in `manifest.json`; hash-set comparison confirmed every unique saved PNG is included. Local gallery: `dist/expanded-QA-gallery/index.html`. Full Playwright viewers/traces remain in `dist/evidence/qa2-*` and are omitted from the compact screenshot bundle.
- Durable local-run ledger, four images and scenario assertions: `docs/evidence/2026-11-05-expanded-qa/`. The ZIP is a supplied workspace artifact, not a permanent GitHub release/download. The CI artifact covers GitHub source/browser checks, not local native screenshots; distinguish them.
- This checkpoint is a **documentation-only follow-up**, marked `[skip ci]`, to the tested implementation above. Verify actual HEAD and its code diff at the next session. No second source/ISO run is needed merely for recording these results.
- **Still not an installable release:** native container graphics do not prove ISO/UEFI boot, target NVIDIA/Secure Boot, Android pairing, Calamares, encrypted installation or full-system recovery. All physical disks/USB/firmware remain untouched.


## EXPANDED QA CHECKPOINT — 2026-11-05

This section supersedes earlier component-testing claims. The whole OS remains incomplete.

- Starting verified HEAD: `e4846c0babafcdfd9081519a76bd2db7e892faad`; branch `feature/orez-live-foundation-20261104`; [PR #1](https://github.com/RezoxNemesis/OREZ-OS/pull/1) remains draft/unmerged; main `fb0661d6cfb8850104d86b3377eef12a7ecd68ed`. The final implementation/CI annotation above is now verified; local native results remain separate from CI.
- **Real native desktop achieved in the workspace:** KWin Wayland/Plasma 6.6.6 nested in Xvfb on isolated Ubuntu 26.04.1, actual OREZ wallpaper, Settings, Dolphin, Konsole and launcher. Five native interaction/restart scenarios passed in both 4 GiB/2 CPU (`qa2-15`) and 2 GiB/1 CPU (`qa2-16`) profiles. Frames manually reviewed. Window tests use the KWin API; launcher uses actual mouse input. Desktop/panel/wallpaper state and open application windows survive Plasma restart.
- Fixture constraints: software Mesa llvmpipe, no KVM/DRI/GPU, host devices, bind mounts, privileged container or runtime network. KWin's scheduling file capability was **removed only inside the disposable test layer**, code hash unchanged, no-new-privileges enabled. Full system bus, audio, portals, authentication/login and hardware behavior are not tested. This is **not an ISO boot**, and does not close M1.
- **60/60 preview cases passed locally** (`qa2-12`): two viewport profiles; malformed/blocked/full storage, offline/reload, real consented worker update, navigation/search, demonstrative permission reset, sensitive browser API non-use, responsive layouts and eight automated WCAG scans. Fixed genuine sessionStorage update bug using in-memory consent. Physical Android remains untested.
- **10/10 real APT scenarios passed** (`qa2-04`): synthetic version fixture upgrades, rejected unattended downgrade, explicit package downgrade, corrupt/unresolvable packages, ordinary-user denial, purge/reinstall and preserved user files/opt-out. No signed repository or whole-system rollback proof.
- **11 native capability scenarios have passing evidence:** ten in `qa2-06` (overall failed because the GL selector was wrong), corrected OpenGL scenario in `qa2-10`. Real C++ build/run, Git, SQLite, Unicode files/archive restore, privilege denial, private-filesystem ENOSPC/recovery, process memory-allocation failure, FFmpeg H.264/AAC encode/decode and Blender CPU render. OpenGL is software only; no game/CUDA/model benchmark.
- **52 source regressions and shell/Python syntax passed** (`qa2-13`); npm audit reported zero known vulnerabilities (`qa2-14`). Changed shell syntax is included recursively. PR CI will rerun on the exact implementation commit.
- Complete evidence and limits: [QA_SCENARIOS.md](QA_SCENARIOS.md). Durable ledger (all 16 local attempts, hashes, exit statuses), scenario JSON and four real images: [expanded QA evidence](evidence/2026-11-05-expanded-qa/README.md). Local full bundle/gallery are generated under `dist`; never claim they are permanent GitHub artifacts.
- Failures retained: initial capability execution denial, unnecessary compositor dependency, worker-storage bug, ineffective browser interception, wrong GL selector and empty Plasma response parsing. Successful follow-ups are explicit; no failed result was overwritten.
- Manual integration workflow now includes package transition checks and optional `desktop_capabilities` (default false); seven-day artifacts. Do not run an expensive ISO job just for these changes. No installation media has been released, and no user's NVMe/USB/firmware was accessed.

### Exact next actions

1. Verify actual PR HEAD against the final checkpoint above. CI `41988662713` passed for implementation `ba8b86adf979e553ad3bfefae6ff6856dd4afa0f`; preserve/download its evidence before expiry. Repeat checks only after relevant changes or a new unresolved concern.
2. Obtain an environment capable of a real UEFI boot and usable guest graphics; compare upstream and the rebuilt OREZ image with identical firmware/device settings. The successful nested container is a useful component control, not a replacement for that gate. Avoid blind repeats of the known all-black CPU-only QEMU setup.
3. Test the inactive Calamares candidate only on disposable virtual disks: installed dpkg registration and OREZ persistence, reboot, correct AppArmor policy, LUKS2/Btrfs, cancellation, non-target disk preservation, snapshots and independent restore. Keep the public installer blocked until demonstrated.
4. Fix/qualify remaining native visual details (wallpaper SVG texture warning, contrast/blur fallback, launcher/session assets), full desktop audio/portals/authentication, and move runtime welcome HTML out of documentation with a renewed upstream collision audit.
5. Only after those gates, perform MSI/RTX/Realme/Secure Boot live-hardware qualification, signed update infrastructure, redistribution review and release. Keep physical data and Windows recovery media untouched.


## ARCHIVED PREVIOUS COMMIT / CI CHECKPOINT — 2026-11-05

- Published implementation: **`d496601e443ed3a525ac22b7d9736391b3e256f2`**, branch `feature/orez-live-foundation-20261104`, [draft PR #1](https://github.com/RezoxNemesis/OREZ-OS/pull/1), unmerged. Main remains `fb0661d6cfb8850104d86b3377eef12a7ecd68ed`.
- **GitHub CI SUCCESS:** [41982877782](https://github.com/RezoxNemesis/OREZ-OS/actions/runs/41982877782), source job `127096789431`. Verified logs report **52 source tests passed**, package build and 16-file path/mode/owner audit passed, production preview build passed, and **all 14 desktop/mobile browser tests passed in one run**. The expensive ISO job was skipped as intended.
- [Download the verified preview and screenshots](https://github.com/RezoxNemesis/OREZ-OS/actions/runs/41982877782/artifacts/13395230363): artifact `orez-source-and-preview-evidence`, 30,745,743 bytes, SHA-256 `322fd2210d85ada3aa83a18d5a164808543a4e2f21f4ad0c61b438646166cc10`, 14-day retention. It includes `OREZ-Preview.html`, production assets and all CI test screenshots/logs. Download before expiration.
- All local attempts, including failures: `dist/OREZ-test-evidence.zip`; gallery `dist/evidence/index.html`. This is a workspace artifact, not committed Git data. The durable ledger and four representative genuine captures are committed under `docs/evidence/2026-11-05-session/`. The portable file is `dist/OREZ-Preview.html`; it is a browser design preview, not an APK or OS.
- This final checkpoint is a **documentation-only follow-up** to the tested implementation, marked `[skip ci]` to avoid repeating expensive setup for a result annotation. Do not claim the follow-up itself ran CI. Always inspect actual HEAD, the code diff and the run's head SHA before continuing.
- Native package lifecycle passed locally (run 19); it was not rerun in GitHub. Its manual workflow is defined on the development branch; GitHub's dispatch UI may require that workflow to exist on the default branch. Use the documented local command while the PR remains draft; do not merge merely to expose a dispatch button.
- **OS release remains incomplete:** no new ISO after the builder fix, no visible booted Plasma qualification, no safe installer/recovery or physical NVIDIA/Secure Boot/Android validation. Next actions below remain binding. No user's disk, USB or firmware was touched.

## CURRENT SESSION CHECKPOINT — 2026-11-05, implementation resumed

### Repository and mode
- Implementation is authorized; work resumed in Default mode. Repository verified accessible; branch `feature/orez-live-foundation-20261104`, draft/unmerged [PR #1](https://github.com/RezoxNemesis/OREZ-OS/pull/1), main unchanged.
- Starting verified commit: `27aeece85b8057259ccbaba8abfc455b3bc7c286`. Its source CI [41938523642](https://github.com/RezoxNemesis/OREZ-OS/actions/runs/41938523642) succeeded. This checkpoint is prepared before the new implementation commit; see the final commit/CI checkpoint above the archived history after publication. Verify actual HEAD before editing.
- The consolidated blueprint is `docs/MASTER_BLUEPRINT.md`. It now describes the real repository state and reconciles the original-code licensing policy. Original OREZ code/artwork remains owner-reserved, third-party obligations remain intact.

### Implemented and locally verified
- Responsive React/TypeScript/Vite design preview: workspace, searchable appearance settings, preference reset/persistence, demonstrative phone consent/revocation, blocked installation status, reduced motion, keyboard access, offline cache, and portable single-file HTML. This has **no native system, clipboard, device, shell or pairing access**. Android remains installed on the Realme.
- Desktop/mobile browser checks: 12 cases passed in run 10; offline cases failed, were corrected, then both passed in run 13. Preserve the failed results. The subsequent GitHub job must establish the full suite on committed source.
- New evidence runner captures actual output/status/source digest and screenshots for every run, including failures. Playwright captures every test and full-page views. Unique per-run directories prevent overwriting screenshots; a gallery links reports and frames. CI artifacts retain source/preview evidence 14 days. Package integration has a separate manual-only workflow.
- Native package now declares `systemsettings` and `kdeconnect` dependencies. Real APT tests exposed a **permission bug**: restrictive checkout modes became inaccessible installed paths. Package, install payload and live-overlay builders now copy to fresh staging with 0755 directories/commands and 0644 data. The archive audit rejects bad modes/owners. **52 source/regression tests and the 16-file archive audit passed** in run 18.
- **Real package lifecycle passed** in run 19: dependency-satisfied APT install, all 16 dpkg-owned files, ordinary-user status and appearance controls, same-version reinstall, a real native KDE System Settings window, purge, unchanged unrelated user-data hash, retained KDE applications and clean dpkg audit. Package SHA-256: `a4ee08847f949da4b9a1a71832e580991469580cc5d06ac6d53f8cece9c9fce7`.
- Native window screenshot is from Ubuntu 26.04.1 in Docker/Xvfb, **not a booted OREZ ISO, Plasma session or GPU test**. Container runtime had no network, host block devices, privileged mode or bind mounts. Dependency image: `sha256:ae418b365bc1ab63493a48bbe600430daf1e5999db6de655aa63ba437fac1985`; exact test inputs have separate hashes. Its older embedded scripts are unused: current scripts are copied into `/input` and explicitly invoked by the orchestrator.
- `npm audit --audit-level=high` reported zero known vulnerabilities in run 14; this is not a security certification. Dependencies are locked; grouped Dependabot configuration is added.

### Failures preserved and material limits
- Run 01 tests passed but its first screenshot render hit managed-browser file URL restrictions; rendering the preserved escaped report via `setContent` fixed capture without changing browser policies or rerunning tests.
- Preview failures: CSS import in run 02; generated-worker syntax in run 04/diagnostics 05–06; public-asset `Vary: Origin` cache mismatch in run 10. Corrected with build-time syntax validation and scoped caching of explicit public assets; offline acceptance passed run 13.
- Package failures: APT `--no-download` pathname error in run 11; minimized-container documentation omission in runs 15–16; ordinary-user permission denial in run 17. Ordinary APT still runs with networking disabled. The fixture explicitly includes only OREZ docs to represent a non-minimized desktop. Permissions are fixed in the builder rather than bypassing the ordinary-user assertion.
- Runtime welcome HTML under `/usr/share/doc` needs relocation before supporting minimized hosts, with a new upstream path-collision check. Version upgrade/downgrade, signed updates and package recovery are not established by reinstall.
- No new ISO was built this session. Changed staging requires a future ISO build/boot test. Earlier black VM frames are not attributed to the new permission finding; their checkout environment differed. No `/dev/kvm` or `/dev/dri` was exposed locally. A suitable graphics environment is still needed.
- Calamares guard remains active; installed-root package registration, Btrfs/LUKS2, backup/restore, dual boot, Secure Boot/NVIDIA/MSI/Realme tests and release signing/distribution remain unqualified. **No safe installer ISO or completed OS is claimed.**

### Evidence and next actions
1. Read `docs/evidence/2026-11-05-session/ledger.json` and the representative screenshots. Full local run folders are `dist/evidence/01-*` through `20-*`; failed attempts are included. User receives a downloadable full gallery bundle. GitHub artifacts expire; do not invent access after expiry.
2. Verify the new PR head and complete source/package/browser CI results. Fetch screenshots from `orez-source-and-preview-evidence`; failures are uploaded too. Do not dispatch a full ISO simply to validate docs or the browser preview.
3. Qualify a real visible upstream Plasma desktop on a suitable graphics-capable VM, then test OREZ with identical firmware/devices. Capture actual frames and KWin/session logs. Xvfb Settings does not close M1.
4. Execute Calamares in a disposable virtual-disk fixture: prove OREZ package registration and persistence through reboot; remediate installed AppArmor policy; validate unencrypted and LUKS2/Btrfs paths, cancellation, non-target disks and independent restores. Keep the real-user installer blocked until these pass.
5. Add package version-upgrade/downgrade tests and a signed maintained package source. Then qualify live-only MSI/RTX/Realme hardware using separate, verified media and explicit installation safeguards.
6. At session end update this checkpoint with verified commit, branch, PR, CI outcomes, artifact locations, known risks and exact next steps. Preserve the NVMe, Windows USB, authentication boundaries and user-visible controls.

## ARCHIVED CHECKPOINT — earlier on 2026-11-05

- Development branch `feature/orez-live-foundation-20261104`; current implementation head before this documentation commit: `04bbec81577db61f3204026618f527bef47520ed`. PR #1 is still **Draft / unmerged**, main unchanged. Verify the live HEAD before modifications.
- **M1:** Real Kubuntu 26.04.1 remixed OREZ ISO built and Linux casper live-root/OREZ overlay verified. After Try, SDDM/Plasma processes start in QEMU but the visible desktop is black. **The same zero-lit-pixel black desktop occurs on untouched original Kubuntu** in the same software-only VirtIO 2D QEMU: see [original-control run 41889832695](https://github.com/RezoxNemesis/OREZ-OS/actions/runs/41889832695), official source checksum PASS and welcome screen visibly rendered before clicking Try. This is a shared VM display limitation, not a diagnosis of real NVIDIA hardware; GUI and physical/UEFI acceptance remain UNVERIFIED.
- **M2:** [Authentic base vs OREZ filesystem collision audit 41937702881](https://github.com/RezoxNemesis/OREZ-OS/actions/runs/41937702881) **SUCCESS**. All 16 allowlisted OREZ paths were present; no existing Kubuntu path collisions, missing files or unexpected payload files. The report explicitly states `installation_approved=false`. Only file paths were checked, not installed filesystem semantics, package ownership or rollback.
- **Debian package preflight:** [Source CI 41938238699](https://github.com/RezoxNemesis/OREZ-OS/actions/runs/41938238699) **SUCCESS**. Built native `orez-shell_0.1.0-1_all.deb` contains exactly the 16 allowlisted files, no symlinks/extras or maintainer scripts. The package has **NOT** been installed or dependency-tested in a real installed OS. Treat it as a development artifact, not a signed update.
- **Unresolved:** stock Calamares still unpacks only base Kubuntu and does not install the OREZ layer; inactive 2-source candidate, AppArmor user namespace live override, LUKS2 crypttab, Btrfs/Snapper/Restic backups, dual boot, EFI/Secure Boot, target MSI/Ryzen/RTX 3050/Android physical compatibility, verified signed distribution. The development live media keeps Calamares disabled; NO downloadable installer ISO or SSD installation authorization.
- **Next M2 work:** qualify actual Calamares file copying and `.deb` ownership on a disposable virtual disk, then encryption/snapshot restore. **Next M1 work:** obtain a KVM/GPU-backed graphical VM or documented physical *Try-only* boot evidence, not endless headless CPU-only QEMU renders.

### Historical logs and decisions follow; older headings may describe superseded states.
## ARCHIVED VERIFIED STATE — 2026-11-04
- Repository: RezoxNemesis/OREZ-OS; development head before this handoff update: `fc6fc258bbde0d8dc1104a3d230de81275feb220`, branch `feature/orez-live-foundation-20261104`. Draft PR #1 **UNMERGED**; main remains initial-only. Verify remote HEAD again before editing.
- [Source CI 41883465838](https://github.com/RezoxNemesis/OREZ-OS/actions/runs/41883465838): **SUCCESS**, native Debian package and synthetic installation safety tests. [CI 41883769134](https://github.com/RezoxNemesis/OREZ-OS/actions/runs/41883769134) also passed handoff source status.
- [Full-image QPainter VM run 41882928635](https://github.com/RezoxNemesis/OREZ-OS/actions/runs/41882928635): **FAILURE** overall. Signed-checksum-authenticated upstream ISO, OREZ live SquashFS and OREZ install-only SquashFS built correctly. Headless diskless QEMU VirtIO: exact Kubuntu welcome recognized, user-safe `Try` action succeeded, OREZ casper live-root present, KDE Plasma/display-manager processes present, but both delayed desktop screenshots were **solid BLACK** (0% lit, one color) despite test-only `KWIN_COMPOSE=Q` experiment. Thus M1 visually usable desktop NOT qualified. The separate UEFI test reached only TianoCore/Kubuntu splash, not desktop.
- [Boot evidence artifact 13350953532](https://github.com/RezoxNemesis/OREZ-OS/actions/runs/41882928635/artifacts/13350953532) contains guest serial logs and screenshots (short retention). Guest log had delayed `snapd.apparmor`, `snapd.seeded`, and `gpu-manager`; these are **observations, not proven causes**.
- Installed-system release **BLOCKED**: stock Calamares source copies only base `filesystem.squashfs`, not installed OREZ payload; live-only `kernel.apparmor_restrict_unprivileged_userns=0` exists; inactive two-layer candidate and disabled Calamares warning are not approved installation support. LUKS2/Btrfs/Snapper/Restic restore, EFI/Secure Boot, RTX 3050/MSI/Realme interoperability and signed distribution remain untested.
- New work should **avoid another costly full-ISO build without a distinct test hypothesis**. Efficient next choice: establish a controlled upstream Kubuntu-vs-OREZ graphics baseline (or test a different, genuinely accelerated VM), collect exact KWin logs, then validate real hardware only via a separately verified *live/try-only* distribution path. Do not disable AppArmor or force changes to real NVIDIA hardware to make a VM test green.
- No 5GB installation ISO is published. Do not erase the user's NVMe, overwrite the Windows USB, merge PR #1, or mark M1/M2 complete. See historical evidence below.

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

## 2026-11-04: Local compositor guard verification; GitHub runner queued
- Development head before this test change: 6ca8878db6d50bcb5e168387f8a55ac52354756b; PR #1 remains draft/unmerged.
- Source run https://github.com/RezoxNemesis/OREZ-OS/actions/runs/41878113197 was queued on inspection. No CI pass or full ISO/Plasma visual success is claimed.
- KDE Plasma 6 startup source supports scripts in system XDG config locations/plasma-workspace/env/*.sh (normal system directory /etc/xdg). KDE documents KWIN_COMPOSE=Q as a Wayland-only QPainter option; guest behavior on this Kubuntu build still needs a real test.
- Relevant sources: https://sources.debian.org/src/plasma-workspace/4%3A6.3.6-2/startkde/startplasma.cpp/ ; https://community.kde.org/KWin/Environment_Variables
- Local shell syntax and mock cmdline tests passed: the exact orez.verify=1 test flag selects Q; normal boots preserve an inherited backend. Permanent unit tests now cover both paths and nonmatching orez.verify=10.
- This is test-only. The installer, physical RTX 3050 boot, security and encrypted recovery remain unqualified. Do not publish an installation ISO or merge PR.

## 2026-11-04: synthetic Calamares payload rehearsal (source change)
- Added tests/test_install_manifest_replay.py with an exact candidate two-source configuration check, a real source allowlist copied to a disposable TemporaryDirectory, and positive/negative AppArmor policy fixture checks using the existing read-only offline auditor. The test explicitly asserts safe_to_install=false and excludes all VM-only services and compositor overrides. Does not execute Calamares, mount filesystems or touch actual block devices.
- See docs/INSTALLER_SYNTHETIC_TEST.md. This is a source-test addition, NOT installed-system qualification. The full-image QPainter CI run #41882466089 was **in progress** when this note was drafted; verify its final status and retained visual artifact before claiming a result.

## 2026-11-04: Verified synthetic installer suite and CI scheduling caveat
- Commit 4efe44a173fdcb3ac2d6dbc9a6cdde23e65f8731 (tests/test_install_manifest_replay.py and docs): [GitHub source CI 41883465838](https://github.com/RezoxNemesis/OREZ-OS/actions/runs/41883465838) COMPLETED SUCCESSFULLY. This verifies only code, package and synthetic TemporaryDirectory fixtures, not a real installed OS.
- QPainter full-image experiment sources and tests passed at [41880060009](https://github.com/RezoxNemesis/OREZ-OS/actions/runs/41880060009). Full ISO run [41882466089](https://github.com/RezoxNemesis/OREZ-OS/actions/runs/41882466089) constructed the ISO but its direct-kernel QEMU step was canceled during a GitHub concurrency collision after a delayed duplicate event, not a QPainter pass/failure; UEFI capture was still in progress at observation.
- Delayed duplicate run [41882928635](https://github.com/RezoxNemesis/OREZ-OS/actions/runs/41882928635) was pending with no jobs at observation. Verify both live statuses and actual artifacts before deciding whether QPainter renders. Do not start another 5 GB test based solely on stale status.
- Release gate stays BLOCKED: no visually verified OREZ desktop in full firmware test, Calamares two-layer candidate inactive, live-only AppArmor override, LUKS/Btrfs/Snapper/Restic and actual MSI/RTX/phone tests unqualified. Keep PR #1 draft and unmerged; no ISO release, SSD/Windows USB untouched.

## 2026-11-04 — QPainter full run final proof
- [Run #41882928635](https://github.com/RezoxNemesis/OREZ-OS/actions/runs/41882928635) concluded **FAILURE**. The guest saw OREZ and launched KDE after the guarded Try action, but both actual delayed QEMU desktop captures were all-black RGB images. The QPainter environment toggle is test-only and does not constitute a fix. The UEFI frame remained at TianoCore+Kubuntu splash. Artifact id 13350953532, short retention. This result supersedes any earlier 'queued/pending' QPainter note in this history.

## 2026-11-04 — Pristine upstream graphics A/B control implemented
- After QPainter full-image failure #41882928635, added a dedicated isolated baseline script `build/test-upstream-baseline.sh` and workflow `.github/workflows/orez-upstream-control.yml` to compare **unchanged original Kubuntu 26.04.1** on the same CPU-only VirtIO 2D QEMU hardware. No OREZ overlay, test-only compositor script, writable disk, network, installer or host input.
- The control verifies the immutable official ISO SHA-256, recognizes the known Try-screen pixels before a safe guest-only click, and retains two delayed screenshots + serial logs. The image itself is never uploaded. This test helps distinguish an upstream VM/KWin rendering limitation from OREZ-specific effects but is not a physical graphics test.
- Source CI: [#41887319606](https://github.com/RezoxNemesis/OREZ-OS/actions/runs/41887319606) SUCCESS (Bash syntax, native package, new no-disk/network negative tests); previous baseline source CI [#41887232244](https://github.com/RezoxNemesis/OREZ-OS/actions/runs/41887232244) SUCCESS.
- **One-shot original-Kubuntu control run** [#41887435151](https://github.com/RezoxNemesis/OREZ-OS/actions/runs/41887435151) started from `build/upstream-control-kubuntu-20261104-1` and was **IN PROGRESS** at handoff writing. It is not an OREZ build and must not be interpreted as a graphical pass until its retained framebuffer is manually inspected.
- M1/M2 are still not certified; keep PR #1 Draft/unmerged. Windows USB and NVMe remain untouched. Before another costly graphics test, inspect this A/B control and form a specific new hypothesis.

## 2026-11-05: First pristine control concluded INCONCLUSIVE, harness bug verified
- [Upstream Kubuntu A/B control 41887435151](https://github.com/RezoxNemesis/OREZ-OS/actions/runs/41887435151) finished FAILURE. Official Kubuntu ISO SHA-256 verification PASS; guest Linux reached serial login and snapd services. BUT the controller never clicked Try and collected no framebuffer because it erroneously required a `kubuntu-installer-prompt` string in the guest serial log. That string was only present in prior OREZ runs as part of `OREZ_GUI_PROCESSES` output from OREZ's own diagnostic unit, which pristine Kubuntu does not contain.
- **Therefore this run is NOT evidence whether pristine Kubuntu has working or broken graphical rendering.** Only `BASELINE NOT QUALIFIED: safe Try transition was never completed` was obtained; there was no graphical comparison.
- Follow-up source fix: use the same pinned visible 1280x800 Try-screen pixel matcher independent of OREZ logging, sampling QEMU screenshots every 10 seconds. Still refuse any QMP input for unexpected frames. Save `last-screen.ppm.gz` for failed matches. No disk/network/host input, no installer invocation. Run source CI first, then one controlled upstream VM only if source checks pass.
- M1 desktop release and M2 installer still BLOCKED; keep Draft PR #1 unmerged and do not distribute an ISO.

## 2026-11-05: Original Kubuntu control result and next installer validation
- [Pristine control 41889832695](https://github.com/RezoxNemesis/OREZ-OS/actions/runs/41889832695): official Kubuntu ISO SHA256 **PASS**, graphical Try welcome visible and guest-only Try click **PASS**, then two delayed QEMU VirtIO desktop frames **COMPLETELY BLACK** (0% lit, one color), same as OREZ. Thus CPU-only VirtIO QEMU is a **shared graphics limitation** in this test; OREZ-specific root cause NOT established, physical RTX 3050/UEFI still untested. No more blind software-only QEMU rebuilds without a new hypothesis.
- Next implementation adds `build/check-install-collisions.py` and `tests/test_install_collisions.py`, checking the **actual signed-base vs allowlisted OREZ install SquashFS file paths** at image-build time. It blocks any existing Kubuntu file overwrite, missing OREZ file or unexpected OREZ file; permits only shared directory ancestors. This is a read-only static gate and **does NOT qualify Calamares, file ownership, installed AppArmor, LUKS2, Btrfs or disk safety.** GitHub CI validation pending at the time of the commit.

## 2026-11-05: Real-image collision source gate and one-shot audit
- New OREZ filesystem file-collision analyzer and fixtures at commit `8882c70d596d66deedd36b23b6da2580da4fdb91` PASSED [source CI 41937486367](https://github.com/RezoxNemesis/OREZ-OS/actions/runs/41937486367). It detects file conflicts between the allowlisted OREZ install payload and original Kubuntu, missing files, unexpected payload files, duplicate/traversal manifest entries; static reports always say `installation_approved=false`.
- Added `.github/workflows/orez-install-collision.yml`, designed for a single explicit `build/audit-collision-*` branch. It verifies the pinned 5GB original ISO SHA256, extracts only the real base SquashFS, assembles the allowlisted OREZ install payload, compares file lists, and uploads only a tiny JSON report. No normal full-ISO remix, QEMU, installation, partitioning, or hardware access. Source CI still must be verified before any one-shot audit run.
- Pristine original Kubuntu A/B graphics control [41889832695](https://github.com/RezoxNemesis/OREZ-OS/actions/runs/41889832695) reached the Try welcome, clicked safely, and both delayed VirtIO guest frames were truly all black (0% lit). That is a shared CPU-only software VM limitation, **not** proof that physical NVIDIA graphics works; no more blind QEMU rendering reruns.
- The two-layer Calamares candidate remains inactive. Even a 0-collision report cannot certify installer file ownership, effective AppArmor, LUKS2/Btrfs, rollback, boot or SSD safety; the user-visible Calamares guard stays enabled and PR #1 remains Draft/unmerged.

## 2026-11-05: Debian package ownership preflight (source-only)
- Real-image path collision audit completed successfully: [41937702881](https://github.com/RezoxNemesis/OREZ-OS/actions/runs/41937702881) verified authentic original Kubuntu 26.04.1 ISO SHA256 and compared the actual base SquashFS against the real allowlisted OREZ installed-file SquashFS. All **16 expected OREZ file paths present, zero base-file overwrites, zero unexpected payload paths**, `installation_approved=false`. Full Calamares and dpkg-owned installation are still untested.
- Added read-only `build/verify-deb-files.py` to compare every regular file inside the built `orez-shell` Debian package to the same 16-path manifest and reject unexpected files, symlinks, maintainer scripts, malformed metadata, wrong package/architecture. Integrated it into the inexpensive source CI job after package build. Status must be checked from GitHub before claiming a pass.
- Debian file ownership will only be established after a *future actual qualified dpkg installation* on a disposable VM. Building and verifying `.deb` contents does not make the inactive Calamares candidate safe to run. Maintainer placeholder and offline repository design are pending release blockers.
