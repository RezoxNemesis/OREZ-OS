# Expanded QA — 5 November 2026

> Correction, 5 November 2026: Docker reports `MemoryLimit=false` and
> `CgroupDriver=none`. Earlier 2/4 GiB and current 6 GiB profiles were requested
> configurations, not enforced limits. Native successes remain component
> evidence; no low-RAM full-OS performance was established.


This records executed checks, not the full release acceptance matrix. Read the
latest handoff for the exact published commit and CI result. All local attempts
use fresh `dist/evidence/qa2-*` folders; earlier failed attempts remain intact.

## What this environment can prove

The workspace has Docker, Chromium and CPU rendering, but no `/dev/kvm`,
`/dev/dri`, NVIDIA GPU or physical Android device. A real Ubuntu 26.04.1 container
now runs KWin Wayland nested in Xvfb, Plasma 6.6.6, the installed OREZ package,
System Settings, Dolphin and Konsole. Actual desktop frames show the OREZ
wallpaper and normal Linux application windows. This is meaningful native
desktop evidence; **it is not a booted OREZ ISO, systemd login, hardware test,
or safe-installation approval**. The graphical ISO boot gate remains open.

Native test isolation: no host bind mounts, devices, privileged mode or runtime
network; ordinary user UID 1500; 2 CPU/4 GiB limit for the desktop, private
16 MiB scratch tmpfs, bounded process count, disposable writable container
layer. The package upgrade fixture uses 2 GiB. Provisioning images uses the
distribution's package repositories before isolation.

The packaged KWin executable has `cap_sys_nice=ep`; the container correctly
denied executing it under its default capability boundary. The test fixture
removes that file capability **inside its private layer only**, records the
before/after state, verifies executable SHA-256 is unchanged, and launches
with no-new-privileges. No additional capability is granted. This deliberate
fixture difference must accompany any desktop result; it must not be copied
into OREZ production images or used to claim production session qualification.

Image identities:

- Base test image: `sha256:ae418b365bc1ab63493a48bbe600430daf1e5999db6de655aa63ba437fac1985`.
- Extended desktop image: `sha256:c98a583d332bf694d03ca956a112c2b11488f819b77a5510e927b12eeacfb5ab`.
- Ubuntu base is digest-pinned in the Dockerfile. APT packages are captured by
  version/image identity, not frozen in a snapshot repository; rebuilding later
  may produce different versions. This fixture is not a reproducible ISO.

## Executed scenario matrix

| Group | Checks and evidence | Result / practical boundary |
|---|---|---|
| Native desktop | `qa2-09`: actual KWin/Plasma desktop, branded wallpaper, Settings, Dolphin, Konsole; frames manually inspected | Passed visible native-container smoke check; ISO boot unqualified |
| Window management | `qa2-15` and `qa2-16`: real window inventory, minimize/restore/resize, workspace switch, launcher pointer input, Plasma restart | **Five scenarios passed in both 4 GiB/2 CPU and 2 GiB/1 CPU profiles**; launcher/restart frames visually reviewed; not a full-session performance benchmark |
| Package transitions | `qa2-04`: initial install, ordinary-user install denial, preference opt-out, corrupt archive, missing dependency, upgrade, rejected implicit downgrade, explicit downgrade, purge, reinstall | **10 passed** using real APT and three deliberately synthetic local package versions; not signed repository/system rollback |
| File handling | `qa2-06`: Unicode/space paths, copy/hash, rename, symlink; tar archive/restore | Passed; file archive restore is not bare-metal recovery |
| Programming | `qa2-06`: compile/run C++20, temporary Git commit/restore, SQLite commit/rollback | Passed actual tools |
| Privilege denial | `qa2-06`: ordinary-user `/etc` write and unattended sudo fail | Passed specific boundaries; not a penetration test or security certification |
| Resource failure | `qa2-06`: fill private 16 MiB scratch tmpfs to actual ENOSPC, retain sentinel, recover writing after cleanup; Python address-space limit catches allocation failure | Passed; not whole-desktop OOM, physical disk failure or power-loss recovery |
| Creative work | `qa2-06`: FFmpeg H.264/AAC encode/probe/decode; Blender 5.0.1 Cycles CPU render, 320×180/4 samples | Passed actual render and decoded-frame artifacts; no GPU performance claim |
| OpenGL | `qa2-10`: actual glxgears window and captured rendering; Mesa llvmpipe | Passed software OpenGL only; no Vulkan/game/NVIDIA qualification |
| Preview functional/resilience | `qa2-12`: existing 14 plus 46 expanded cases across desktop/mobile Chromium profiles | **60 passed in one run**; Android browser/device itself is not tested |
| Automated accessibility | Within `qa2-12`: four screens × two viewport profiles, axe WCAG 2 A/AA and 2.1 A/AA | Automated checks only; manual screen-reader/accessibility acceptance remains required |
| Source and dependencies | `qa2-13`: 52 regressions plus shell/Python syntax; `qa2-14`: npm audit of the expanded lockfile | **52 passed; syntax passed; zero reported vulnerabilities**; not a security certification |

The preview scenarios cover five malformed preference inputs, blocked storage,
quota exhaustion, injected worker-registration failure, an actual worker update
with explicit user consent, literal hostile-looking search input, repeated
toggle/navigation, consent reset on reload, no calls to sensitive browser APIs,
offline preference persistence, solid panels with no blur, four accessibility
screens, and layouts at 320×568, 915×412, 1920×1080 and 2560×1440. Base profiles
are 1440×960 and 412×915. These test a separate design preview, not Linux or
Android APIs. The update test changes/restores a generated worker file only;
workers are serialized to avoid concurrent modification.

Native window-management assertions use KWin's scripting API, with actual
window geometry/state checks and screenshots. The launcher uses pointer input;
its popup additionally requires visual review. Session recovery restarts
Plasma and compares desktop/panel/wallpaper state while confirming application
windows survive. Neither test represents reboot or crash-consistent recovery.

## Defects and unsuccessful attempts retained

- `qa2-01`, `qa2-05`: KWin capability execution denied. No-new-privileges
  alone did not fix the fixture. Explicit private capability removal resolved
  execution; its scope is documented above.
- `qa2-02`: independent capability tests unnecessarily depended on KWin startup.
  The harness now runs them directly under Xvfb.
- `qa2-03`: 40/44 preview cases passed. Two genuine blocked-storage failures
  exposed unsafe sessionStorage access during worker update handling. Consent
  is now held in a React ref, with no storage dependency. The other two failures
  were a test's ineffective worker-request interception; deterministic injected
  registration rejection now exercises that path accurately.
- `qa2-07` production rebuild passed; `qa2-08` passed all six focused desktop/
  mobile cases, including a real waiting-worker update and consented reload.
- `qa2-06`: ten native capability cases passed, but the OpenGL window selector
  expected a WM_CLASS the application did not expose. Matching its actual
  visible window title corrected the harness; `qa2-10` independently passed.
- `qa2-11`: native window/launcher/workspace checks passed, but restart testing
  stopped before restart because the harness did not print Plasma scripting
  results. It now explicitly prints/validates state; `qa2-15` and `qa2-16`
  pass the complete set, including actual restart, in both resource profiles.
  The initial desktop-count wait had the same empty-response issue; it now
  asserts a positive returned count instead of merely waiting for a process.

Do not hide an overall failed run because some cases passed. Counts in this
report identify successful scenarios and their exact follow-up runs.

## Repeat the checks without touching user disks

Prerequisites: Linux Docker engine, Node 24, Python 3, npm dependencies and
Playwright Chromium. Use fresh output directories on every invocation.

```bash
npm ci --ignore-scripts
npx playwright install chromium
python3 build/run-with-evidence.py --name 'Preview build' --kind browser-preview --output dist/evidence/new-preview-build -- npm run preview:build
python3 build/run-with-evidence.py --name 'Preview scenarios' --kind browser-preview --output dist/evidence/new-browser --timeout 600 -- npm run preview:test
python3 build/run-with-evidence.py --name 'Package build' --kind source --output dist/evidence/new-package-build -- bash build/package-shell.sh
docker build --secret id=qa_ca_bundle,src=/etc/ssl/certs/ca-certificates.crt -f environment/orez-qa.Dockerfile -t orez-qa:20261105-compact .
python3 build/run-with-evidence.py --name 'Package transitions' --kind package-container --output dist/evidence/new-package --timeout 420 -- bash build/test-package-scenarios.sh dist/evidence/new-package-details
python3 build/run-with-evidence.py --name 'Native desktop' --kind package-container --output dist/evidence/new-desktop --timeout 420 -- bash build/run-desktop-container.sh dist/evidence/new-native-details
OREZ_SCENARIO=capabilities python3 build/run-with-evidence.py --name 'Native capabilities' --kind package-container --output dist/evidence/new-capabilities --timeout 420 -- bash build/run-desktop-container.sh dist/evidence/new-capabilities-native-details
python3 build/collect-evidence.py dist/evidence
```

For an enforced constrained profile, set `OREZ_REQUIRE_RESOURCE_LIMITS=1` plus
`OREZ_TEST_MEMORY` and `OREZ_TEST_CPUS`. This workspace correctly rejects that
qualification: its rootless Docker cannot enforce cgroup limits. Historical
qa2-16 passed component checks but did not establish a 2 GiB memory ceiling.
`OREZ_CAPABILITY_FILTER` can select a scenario substring for a targeted rerun.
All images/scripts/package input hashes, renderer details, container exit
state and test results are retained. Source report screenshots are actual
browser captures of escaped logs, not fabricated desktop screens.

PR CI runs source/package/browser checks once per source change. Heavy native
testing remains in the manual package workflow; `desktop_capabilities` defaults
to false to control minutes/storage. Native artifacts there retain seven days.
The draft-branch workflow may require the file on the default branch before
GitHub exposes dispatch; use local commands instead of merging prematurely.

## Unexecuted release gates

Next environment must support actual UEFI boot and a usable guest graphics
path. Rebuild after the package staging fix; test upstream and OREZ under the
same configuration. Then qualify the inactive installer candidate using only
disposable virtual disks, installed dpkg registration, reboot, encryption,
AppArmor policy, snapshots, independent restore, cancellation, and preservation
of a second non-target disk.

Physical MSI/RTX/Secure Boot, Wi-Fi/Bluetooth/audio/USB, Realme pairing/transfer,
multi-monitor and suspend/resume, power-loss recovery, Steam/Proton/anti-cheat,
CUDA/VRAM/model workloads, VM acceleration, signed updates, malicious USB and
AI broker abuse tests remain **not run or not implemented**. No AI broker is
enabled. No installed-system or public-release readiness follows from this QA.

## Continue native controls and real-version upgrade checks

Build the current package first. Use the compact image above, fresh evidence
paths, and one UI scenario at a time on a small VFS host. Container creation
copies gigabytes before the desktop starts; allow for that in the timeout.

```bash
OREZ_SCENARIO=connectivity python3 build/run-with-evidence.py --name 'Native network controls' --kind package-container --timeout 600 --output dist/evidence/new-network -- bash build/run-desktop-container.sh dist/evidence/new-network-native-details
OREZ_SCENARIO=native-upgrade OREZ_PREVIOUS_PACKAGE=/absolute/path/to/previous-verified.deb python3 build/run-with-evidence.py --name 'Actual component upgrade' --kind package-container --timeout 600 --output dist/evidence/new-upgrade -- bash build/run-desktop-container.sh dist/evidence/new-upgrade-details
OREZ_SCENARIO=everyday OREZ_EVERYDAY_FILTER=vlc-playback-audio-pause-seek,native-game-input python3 build/run-with-evidence.py --name 'VLC and game' --kind package-container --timeout 600 --output dist/evidence/new-media -- bash build/run-desktop-container.sh dist/evidence/new-media-native-details
```

The connectivity fixture creates a private system bus and NetworkManager with
all interfaces unmanaged and connectivity checking disabled. No policy grants,
physical radios, connection saves, pairing or real credentials are needed.
Only deliberate dummy password text may appear in its screenshots. The game
check rejects the black introduction before accepting a playable scene; review
the before/after player position, not just its process status.
