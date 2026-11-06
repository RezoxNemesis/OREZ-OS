# Integrated live image — 6 November 2026

**A new development ISO is assembled and passes static checks. Installation is
disabled. This is not a released OS download.** Actual UEFI observations are
recorded in the latest handoff and evidence ledger; a successful build never
proves login, desktop usability, installation or target hardware support.

| Artifact | Verified identity |
| --- | --- |
| Integrated ISO | `dist/assembly-lab/direct-session/OREZ-OS-0.1-live-amd64.iso` |
| ISO size | 5,455,347,712 bytes; 5.46 decimal GB / 5.08 GiB |
| ISO SHA-256 | `6ca85cf37d48beeb8ac0fd6ffa99e94cc9806949584a970916024ddf30d80ac6` |
| Parent development ISO | `8ec11599942f871759d7a2950b26430c8cb51a35d068283d09f348c2771e40e9` |
| Unchanged original filesystem | 4,381,224,960 bytes; `a03245935d78ef2fe755d504e6a4000d14100193dd4724150d8bdf340d0d05f7` |
| Native application layer | 383,488,000 bytes; `22e04836b2e2d0570f248f42306e0a86654202fd5f37561b0d6a0e9d8fbdfd51` |
| Dpkg-owned OREZ layer | 1,224,704 bytes; `e5ae0294aea3f3ee37f3ad853df52e9a5746fc3d1aa98d46281b95c78e35048b` |
| Final package inventory | 2,301 installed records; `orez-shell` 0.1.0-4 |

The table identifies image source `56af0a24133985d225ac22c2e85a6f3cb050f483`.
Its normal default-menu UEFI run completed concealed owner enrollment, rendered
OREZ SDDM and accepted the correct password, but the selected session exited 64
and returned to the greeter. The cause remains unqualified. In a later separate
ordinary-owner tty3 diagnostic, `startplasma-wayland` eventually rendered KDE
Welcome, the approved wallpaper, panel/system tray and native Quick Settings.
Mouse input closed Welcome and opened Settings. No root, compositor override,
authentication bypass or sandbox relaxation was applied. This is evidence of
some working native desktop behavior, not a repaired normal login, workload,
performance, installation or physical-hardware pass. See the
[final run record](evidence/2026-11-06-installer-graphics/qa12-17-vm-result.json)
and [actual screenshots](https://github.com/RezoxNemesis/OREZ-OS/blob/090a5014051e3d230a4a04300d3395f58dedf7a4/TOUR.md).

All test containers and disposable credentials were destroyed after the
bounded observation. Sections below preserve earlier-image history; those
results do not automatically qualify the current bytes. Later source commit
`02acdac` changes the offline audit and documentation, not this ISO.

This build reuses the exact recorded local development parent. It does not claim
a fresh verification of the official upstream signature. The original lower
filesystem is independently hashed inside both input and output images. The
canonical outer builder still verifies the official Ubuntu CD signature and
pinned complete ISO hash before invoking the same assembler.

## First actual boot and security failure

The first integrated image (`82f5b470426776e1443755aba03de9b092c1a58619efc6d1181a5b882a4c56eb`,
same size) reached the UEFI menu, owner enrollment and the actual OREZ SDDM
screen with a real desktop-session choice. The newly created credential worked
at tty2: UID 1000, passwordless sudo refused, SDDM service active. These are
actual ISO/guest checks, not container/theme demonstrations. Graphical
sign-in and desktop workloads were not yet exercised in that run.

**The first password entry was visibly echoed; confirmation was hidden.**
Account creation succeeded but the security acceptance check failed. The
console-password entry must not be certified on this image. Its random dummy
credential existed only in the diskless/offline test guest, which was stopped;
the helper's private password file was destroyed with its test container.
Unaltered failure frames are retained as evidence, not real owner credentials.

The first attempted correction orders console/keymap/splash startup
before enrollment, moves splash teardown into the same enrollment process
instead of a separate TTY-resetting ExecStartPre, and refuses Python's
password-echo fallback before input. This addresses suspected console-reset
ordering; the first run alone does not establish which process reset echo.
183 source tests passed, including a real pseudoterminal no-echo check, but
**the second actual boot still exposed the first password**. Its image identity
is `4425b475c5f2081e7ce0b06b73b002825d27214475eb78a1d92489cb61eff72d`.
The second run also proves that the real SDDM interface rejects an incorrect
password and masks graphical password input; this does not resolve the console
flaw. Correct-password desktop startup is separately observed.

The current image in the table now waits for the original Plymouth daemon to
exit and checks that it no longer answers before prompting. The process identity
includes its start time, and the helper never kills a PID. New source checks pass
(185 total). The third actual UEFI boot shows both password entries concealed,
completion of setup, a successful owner tty2 login and refusal of passwordless
sudo. This is one observed boot, not broad timing-race qualification. Its SDDM
log records one greeter exit/restart before reaching the real login screen.
SDDM/PAM graphical authentication also succeeded at 04:09:25 UTC after the
test driver switched from repeating timed keys to immediate down/up events.
Plasma started but the observed desktop stayed black; logs show software graphics
issues and a splash timeout. A later QMP capture conflict stopped the test
harness, not a proved guest crash. No usable-desktop pass is inferred.

Fourth boot of the same bytes used virtio-vga-gl with SDL on private Xvfb and
host llvmpipe (software rendering, not hardware acceleration). Enrollment was
concealed and the tty2 owner login reached a shell; no usable desktop was
qualified. After 1,627 seconds a scrot timeout stopped the harness, which sent
SIGTERM to QEMU. All 74 decodable guest PNGs are retained. One truncated capture
is recorded and excluded from the PNG gallery. The final harness change handles
this timeout and removes partial frames; 187 local source tests pass, but this
capture-only change has not had another boot. All VM containers/credentials
were destroyed after evidence collection. No current booted app/game/browser,
installation, physical GPU/radio or performance pass follows from these results.

## What the image now includes

The original kernel/base, native Brave 1.99.55, VLC 3.0.23, SuperTux 0.6.3,
PySide6 6.10.2, Calendar, Reuz, Store components, OREZ wallpapers/colors and
the current live-owner policy are together in one image. Existing base packages
include Plasma, NetworkManager, KDE Connect, BlueZ and Bluedevil. Package
presence does not qualify Internet browsing, sound, physical radios, screen
mirroring or game performance. OREZ AI remains disabled; Android consumer
emulation is deferred. The inherited Plymouth splash still says Kubuntu.

Casper's actual pinned `/scripts/casper` glob-mount path prepends each sorted
filesystem. Thus precedence from lowest to highest must be:

1. `filesystem.squashfs`: untouched original, including capabilities/xattrs.
2. `orez-apps.squashfs`: previously authenticated native application delta.
3. `orez-install.squashfs`: actual dpkg-owned OREZ package transaction.
4. `zz-orez.squashfs`: live-only owner setup, login theme, diagnostics and guard.

The component transaction runs real offline dpkg, its normal desktop-file
trigger and a clean final audit. It changes no existing package version or raw
package database record. All 38 current source files are owned by `orez-shell`;
the layer also carries four dpkg database files. Independently extracting the
packed layer reproduces all 68 paths and their expected metadata. An arbitrary
JSON manifest cannot authenticate a software update.

The temporary extraction omits runtime trees/xattrs and is **never** shipped as
a replacement base. It was removed only after packed-artifact validation to
recover approximately 10 GiB of staging space. Source, original input, packed
layers, package pool, audit inventories and evidence remain.

## Boot and installation boundaries

Both normal and safe-graphics GRUB entries now contain `boot=casper`. The pinned
upstream menu omits that literal token, while OREZ's service and helper require
it; simply inheriting that menu would skip enrollment and leave login blocked.
The OEM-install choice is removed. The normal choice explicitly says
“Try OREZ OS (installation unavailable).” New media branding makes the temporary
live username `orez`; casper lowercases the first word of `.disk/info`.

The volatile live session creates a locked account and asks locally for a new
12–128-character temporary password before starting SDDM. It has no existing
online-account requirement, shipped password or automatic admin grant. Boot-time
execution, effective authorization and login must still be tested together.

`image/installer/orez-unpackfs-candidate.conf` now declares **three** installed
sources in order: base, apps, then dpkg-owned components. It still excludes the
known live AppArmor override and never copies the live-only top layer. This
configuration remains inactive. Static or synthetic unpack checks do not prove
a completed Calamares installation, disk selection, encryption or recovery.

## Repeat the build

Use the isolated builder described in [IMAGE_APPLICATIONS.md](IMAGE_APPLICATIONS.md).
Inputs and output must be regular task files; no physical device, host home or
Docker socket is mounted into the builder. All output paths must be new.

After reconstructing the reviewed base plus verified app layer in a disposable
offline staging root, install the current source-matching Debian package:

```bash
python3 build/install-orez-layer.py --root /work/component-root \
  --iso /input/parent.iso --package /input/orez-shell_0.1.0-4_all.deb \
  --output /work/component-layer
```

The staging marker, actual ISO identity/extent and exact app package state are
required. This helper accepts the pinned official input or recorded development
parent; it cannot turn an unauthenticated hash into upstream signature proof.
The usual rootless container checks and loopback-only network remain enforced.

For the normal signed-upstream pipeline, prepare these local build inputs first:

```bash
export OREZ_APP_LAYER=/work/apps/orez-apps.squashfs
export OREZ_COMPONENT_LAYER=/work/components/orez-install.squashfs
export OREZ_COMPONENT_REPORT=/work/components/report.json
bash build/build-live.sh
```

`build-live.sh` now fails early if these are missing or stale; it no longer
produces an apparently complete image containing only copied OREZ files. The
legacy manual GitHub full-image job does not yet prepare these inputs, so it
remains blocked pending the isolated dependency-build job. Ordinary PR checks
remain separate and small. Do not trigger repeated full workflows expecting
missing inputs to appear.

For an explicitly labeled local development derivative only:

```bash
python3 build/assemble-live.py --iso /input/recorded-parent.iso \
  --apps /input/orez-apps.squashfs \
  --components /work/component-layer/orez-install.squashfs \
  --component-report /work/component-layer/report.json \
  --output /work/new/OREZ-OS-0.1-live-amd64.iso --development-parent
bash build/check-iso.sh /work/new/OREZ-OS-0.1-live-amd64.iso
```

Assembly preserves the original base, replays upstream EFI/BIOS boot metadata,
patches the reviewed initrd hooks, verifies all ten changed media mappings and
renews the corruption-check list. The final checker re-reads layers from the
finished ISO, enforces exact source bytes/package state, checks the boot flags
and rejects an absent installer guard. SHA-256 identities and signed upstream
inputs supply integrity/authenticity evidence; the upstream MD5 media table is
only for accidental corruption detection.

Fixed layer timestamps help repeatability but do not establish reproducible
whole-ISO bytes. Frozen APT snapshots, full source retention, build tool/version
pins, deterministic ISO metadata and an independent rebuild are still needed.
The actual local image records its pre-commit working-tree state; the evidence
runner also records a complete source digest. A later commit does not retroactively
change that artifact's recorded build identity.

## VM tool and release limits

The current `environment/orez-vm-tools.Dockerfile` builds a 737,968,451-byte
helper with optional software-backed VirGL, Xvfb and SDL. Local image ID:
`d169d643a3f43dbff1ef1113a22bae5bd8e1bb9aff0c5503f51538bf2ef4d25a`.
The prior headless-only image was 304,335,442 bytes. Both default to UID1500;
neither is published. See environment/README.md for the private-display command.

`build/probe-integrated-live.py` hashes the ISO and captures real QMP display
frames from an offline diskless UEFI guest. QEMU runs as an ordinary user; its
control socket is private, no display port is published, and no physical disk
or host GPU is passed through. Guest RAM is explicitly 6,144 MiB. This does not
qualify a 6 GiB desktop workload, host cgroup enforcement or RTX acceleration.
Recording frames successfully never sets `desktop_verified` to true. Optional
`--graphics virgl` verifies host llvmpipe and captures the real SDL window using
a private Xauthority display; it does not provide hardware acceleration. Missed
QMP captures are recorded without killing a VM during operator input. SDL capture
timeouts are now recorded too, with partial output removed; the latter correction
has source regression coverage but no subsequent full boot.

Before a full OS download: successful owner enrollment/login and effective
security tests, native desktop workloads, disposable-disk install/reboot and
recovery, current security updates, source/licence obligations, signed release
metadata and actual PC compatibility must pass. Keep the repository public
until the owner's PC-readiness condition is met. The installed disk footprint
has not been measured; ISO size is not installation size.

## Direct desktop session correction

Actual source inspection of the base and qa12-08 show that the inherited
Kubuntu Live Environment runs the upstream installer prompt before Plasma.
A successful owner login therefore did not immediately enter the desktop.
The live owner source now provides `OREZ Desktop` under
`/usr/share/orez/wayland-sessions` and selects it through live SDDM SessionDir.
It uses the same direct launcher as the base's Plasma (Wayland) entry; vendor
files are preserved and no autologin, no-lockscreen flag or authentication bypass
is added to the OREZ entry. An authenticated administrator can inspect/change
the directory in /etc/sddm.conf; reboot restores the nonpersistent live default.

210 source tests pass. The observed 1d68fccb ISO predates this correction; its
actual authenticated wrapper session is on VT4, while the greeter is on VT1.
Read loginctl and validate the active session instead of assuming every blank
VT is the desktop. Default-boot qualification of the new entry is pending.
