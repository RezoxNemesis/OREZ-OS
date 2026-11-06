# First PC release: owner login and daily applications

Latest owner clarification (6 November 2026): use the official **native Linux Brave** browser. YouTube is optional for the first release; prioritize consented phone screen mirroring through scrcpy. KDE Connect handles pairing/transfers/controls, not Android screen mirroring by itself. Actual mirroring and phone audio remain unverified without the Realme connected.

6 November follow-up: [actual image application stage](IMAGE_APPLICATIONS.md)
now installs Brave, VLC, SuperTux and PySide6 into the extracted base and packs
an independently verified app layer. No new full ISO is assembled yet. Calendar/
Reuz also pass offscreen component checks against those actual dependencies.

**Binding owner scope update, 5 November 2026:** prioritize reliable boot,
installation, authenticated login, the desktop, settings, native Brave/VLC/Linux
games, web YouTube, OREZ themes, Calendar, Reuz Time, permission-controlled AI,
connectivity and security. Android emulation/Play Store/game presets move to a
later upgrade. Web YouTube is explicitly authorized for this first release;
this does not turn the future Android requirement into a browser shortcut.

**Release is not ready.** This checkpoint implements and tests components. No
new full ISO was built. Retained development ISOs predate these changes and must
not be used for sensitive work or installed on the owner's SSD. A passing native
window test does not certify boot, installation or physical hardware.

## Implemented changes and their evidence

| Component | Implementation | Verification and limit |
|---|---|---|
| Live owner enrollment | Local-console temporary password, locked root, no default password/autologin, removal of known casper sudo/Polkit grants | Real pinned initrd patched and independently extracted; five isolated account/authentication scenarios pass. Full boot/service ordering, graphical login, lock screen and Polkit dialogs remain open |
| Login appearance | Original OREZ SDDM theme with approved Rest wallpaper, masked password, keyboard navigation, session selector and errors | Actual SDDM test-mode captures; missing Wayland session is disclosed and sign-in disabled. Test mode cannot authenticate |
| OREZ Calendar | Native Qt month view, all-day event create/edit/delete, SQLite and UTF-8 .ics export | Real native window interaction and model tests pass. No cloud sync, import, timed reminders or background service; unsaved editor text is not a persisted draft |
| Reuz Time | Native Qt clock with IANA timezone/12h/24h, countdown pause/resume and stopwatch/laps | Real native preferences, countdown completion, stopwatch and close cancellation tested. No wake alarm, scheduled alarm or background timer; physical sound untested |
| OREZ Paper / Ink | Two original KDE color-scheme files; local apps follow palette changes | Actual app-level palette changes tested. Complete Plasma theme/session integration and other apps still need qualification |
| YouTube (Web) | Explicitly labeled launcher opens official YouTube in normal native Brave | Fixed URL/launcher source tested. No Android claim. Brave sandbox and YouTube network access are blocked in this workspace |
| Component updates | `orez-shell` 0.1.0-4; 38 allowlisted files; no maintainer scripts or live root helper in the normal package | Actual package installation and offline previous-version upgrade tested; signed production repository and whole-system rollback remain open |

The Calendar/Reuz source is a small first desktop edition. Reuz repository
`RezoxNemesis/Reuz` was verified public at
`becce2284e270085a7a42ae805ca53f01d218649`. Its existing web/Android code supplies
the product reference and UTC/24-hour clock defaults. This desktop implementation
does not import its server/MCP setup route or claim parity with its Android app.
No Reuz repository change was made. No public OREZ AI repository was found in the
owner's inspected repository list; `orezctl ai` still reports **NOT ENABLED**.

## Live authentication design

The optional schema-3 initrd profile replaces four exact hash-pinned casper
hooks, including the previously implemented offline-cache hook. Verification
restores the exact original final CPIO archive and preserves every early
archive/microcode byte. Changed upstream inputs are rejected for review. A new
live-only overlay carries the owner setup helper, systemd unit, SDDM dependency
and theme. Static image checks require exact source bytes, root ownership and
canonical file/directory permissions. The ordinary Debian/install payload
excludes this live-only setup policy.

Before SDDM, the console prompts twice for a 12–128-character temporary password.
No echo, command-line password, embedded credential, remote listener or AI
approval mechanism is used. The helper requires root, nonpersistent casper boot,
trusted root-owned state, locked root and the expected sole sudo-group member.
It refuses piped input and an existing unlocked account. Failures leave the
desktop blocked; attempted account changes are relocked on failure. Recovery is
to reboot verified media and retry. This is a volatile live-session credential,
not a disk-unlock password or implemented installer account workflow.

The fixture executed real `chpasswd`/sudo/PAM inside a disposable container:
non-live production invocation denied; cancellation/short/mismatched passwords
left setup incomplete; the correct password allowed `id -u`; wrong password,
passwordless sudo, cached credentials and a non-admin user were denied. The
fixture substitutes the live-boot predicate **only in the test process** because
this is not a casper-booted machine. No such switch exists in production code.
The three known old grant patterns are absent from the extracted patched hooks.
This does not prove the complete effective policy of a booted OS.

First physical access can enroll the temporary live owner. This cannot prove
human identity. UEFI configuration, verified boot, encryption and owner-held
recovery remain separate protections. Upstream privileged services and approved
packages still execute trusted system code. A shared Unix UID is not a sandbox:
ordinary apps can access that user's files unless separately confined. No
promise of immunity to malware, trackers, compromised packages or stolen
credentials follows from removing passwordless sudo.

## Visible controls and data

| Feature | Location and controls | Data / recovery |
|---|---|---|
| Calendar | Launcher → OREZ Calendar; New, Save, Delete confirmation, Export, Data and controls | `$XDG_DATA_HOME/orez/calendar/events.sqlite3` (default `~/.local/share`); directory 0700/file 0600; export .ics. Close before backing up database. Do not erase malformed/unrecognized databases automatically |
| Reuz | Launcher → Reuz Time; Clock/Timer/Stopwatch tabs; Data and controls | `~/.local/share/orez/reuz/settings.json`, or XDG equivalent; atomic private preferences. Display timezone does not change system time. Reset timer/laps with visible buttons; closing active work requires confirmation |
| Color schemes | KDE System Settings → Colors & Themes → Colors | Select OREZ Paper/Ink or restore Breeze. Assets never silently change an existing user's choice |
| Login theme | SDDM configuration; documented `theme.conf.user` override, `SolidPanel` and `Background` | Live-only policy; changes require administrator authority. No credentials stored in theme files |
| Owner setup | Visible first live console; service `orez-owner-setup` | `/var/lib/orez-live/owner-required`, `/run/orez-live/owner-ready.json`; root-only state. `systemctl status`/journal metadata, no password/hash logs; reboot retries volatile setup |
| YouTube | Launcher → YouTube (Web), or `orezctl youtube` | Normal Brave profile/site permissions. No owner/root access is granted by Google login |

## Test ledger and failed attempts

All `qa8-*` attempts retain report screenshots; native GUI attempts also retain
actual PNG window captures. Reports are not desktop screenshots. Consult the
machine-readable ledger under `docs/evidence/2026-11-05-owner-login/` and the
handoff for final counts, artifact hashes, CI and download URL.

- 01 timed out while preparing the lab; the already-running package transaction
  completed before follow-up. 02 assumed an obsolete `main/` extraction layout;
  03 corrected it and inspected the real initrd.
- 04 source checks passed. 05 failed because a direct `docker cp` preserved
  workspace ownership; its early cancellation result was not valid proof.
  07 used canonical root-owned staging and actual prompt witnesses; all five
  authentication scenarios passed.
- 06 first greeter captures showed a blank session control. 14 exposed another
  fixture mistake: direct source tar preserved restrictive directory modes.
  15 corrected canonical staging. 18 correctly exposes the actual environment's
  missing desktop session. SDDM checks `/dev/dri` before listing Wayland; merely
  installing the session package cannot create acceleration.
- 08 real initrd compression exceeded the conservative 30-second pack limit.
  The compression-only timeout was raised to 120 seconds; bounded decoder
  limits were retained. 09 passed actual repack, reversibility and independent
  extraction. No complete ISO was rebuilt.
- 10 daily-app source tests passed. 11 package passed but the copied test script
  was unreadable to UID 1500. 13 fixed that fixture: seven app scenarios passed,
  hot palette switching failed. 16's first palette fix still failed. 17 fixed
  the actual Qt palette signal/stylesheet cache; all eight scenarios passed.
- 12 installed signed official SDDM/session/Plymouth test dependencies and then
  disconnected networking. No image publication or host security change.
- 19 upgrade setup refused an implicit downgrade because the lab already had
  the new version. 21 explicitly restored the old artifact as a fixture before
  exercising the real upgrade, without relaxing APT downgrade policy.
- 20 builds a real small live SquashFS and passes the new metadata/byte audit.

No physical disks, firmware, Windows recovery USB or real user credentials were
accessed. Screenshots use dummy data. Two systemd diagnostic-unit warnings about
historical `User=nobody` remain in the greeter logs; owner service verification
returned success. Service verification does not execute startup ordering.

## Blocking work before the promised full OS download

1. Provision the documented environment: actual usable KVM/render access,
   browser namespace sandbox, enforced resource limits and at least 80 GiB
   workspace. The current 32 GiB workspace cannot safely retain a new build
   alongside its evidence, two old ISOs and dependency/lab images. Publish the
   updated `environment/orez-qa.Dockerfile`; its new dependencies alone do not
   grant these host capabilities. No unsupported security bypass.
2. Build a dependency-complete candidate with signed upstream Qt, native Brave,
   VLC and a free native game such as SuperTux. The existing remix builder layers
   OREZ source but does not yet provision the new application dependencies into
   the pinned base. QA-container installation is not preinstallation in an ISO.
   Capture SBOM, licences, package inventory, authentic input and output hashes.
3. Qualify offline UEFI boot → local enrollment → SDDM → authenticated Plasma,
   incorrect-password denial, lock/unlock, logout/login and reboot. Check actual
   effective sudo/Polkit, network exposure and no autologin. Revalidate upstream
   control if the new rendering environment fails. Do not repeat known black
   CPU-only VM tests without a new hypothesis.
4. Finish real Calamares/dpkg integration, owner-chosen credentials, explicit
   disk confirmations, dual-boot preservation, encrypted installation, reboot,
   failed-update recovery and independent backup restore on disposable VM disks.
   Keep the current installer safety blocker until these pass.
5. Integrate the requested visible OREZ AI UI/provider configuration with narrow
   permissions and owner-authenticated sensitive actions. Current AI support,
   automatic malware detection, isolation policy and signed OREZ update service
   are incomplete. Test revocation, cancellation, audit redaction, no implicit
   root and updates preserving owner restrictions before marking them delivered.
6. Validate actual MSI/RTX/Secure Boot, Realme Wi-Fi/Bluetooth/tethering/sharing,
   sound, USB/eject, sleep, displays and normal browser/media/game workloads.
   Linux ancestry does not replace these checks. Software cannot upgrade radio
   generations, create extra VRAM, or safely unlock arbitrary GPU power limits.
7. Measure cold/warm launch, frame pacing, memory pressure, idle CPU/power,
   suspend/resume and update regressions at enforced 6 GiB and actual 16 GiB.
   Use the thresholds in PERFORMANCE.md. Network buffering depends on network
   and service conditions; zero lag, crashes or attacks cannot be promised.
8. Complete signing, redistribution/source obligations and owner/access audit.
   Only then publish checksummed installation media and independent recovery
   instructions, and perform the owner's requested public→private repository
   transition. Android compatibility is no longer a first-PC-release gate.

Technical references: [SDDM theme API](https://github.com/sddm/sddm/wiki/Theming),
[SDDM session discovery](https://github.com/sddm/sddm/blob/develop/src/greeter/SessionModel.cpp),
[systemd execution controls](https://www.freedesktop.org/software/systemd/man/latest/systemd.exec.html),
[Reuz source](https://github.com/RezoxNemesis/Reuz/tree/becce2284e270085a7a42ae805ca53f01d218649),
[Qt palettes](https://doc.qt.io/qt-6/qpalette.html),
[iCalendar RFC 5545](https://www.rfc-editor.org/rfc/rfc5545).
The pinned distro packages and observed behavior take precedence over assumptions
from current upstream documentation. See third_party/casper for GPL notices.
