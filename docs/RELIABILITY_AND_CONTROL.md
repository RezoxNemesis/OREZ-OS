# Reliability, privacy and owner control: first-release contract

Review date: **6 November 2026**. Reviewed source commit:
`56af0a24133985d225ac22c2e85a6f3cb050f483`.

The owner's reference comment describes broken updates, unwanted data
collection, difficult driver maintenance, background work hurting games, time
spent debloating, and settings that are hard to find. These become acceptance
criteria for OREZ, not claims that Linux ancestry automatically solves them.
The goal is a familiar, responsive KDE desktop whose behavior the owner can
inspect, control and recover. This document records a **source/evidence review**;
no new test was run and no new runtime screenshot is claimed by this review.

This contract supplements [FIRST_PC_RELEASE.md](FIRST_PC_RELEASE.md),
[OWNER_CONTROL.md](OWNER_CONTROL.md), [UPDATES_AND_GUARD.md](UPDATES_AND_GUARD.md),
and [PERFORMANCE.md](PERFORMANCE.md). Android consumer emulation stays deferred.
It does not authorize formatting the owner's SSD, changing firmware or
publishing an unqualified ISO.

## Evidence vocabulary and present release boundary

- **Implemented source:** concrete code exists. This alone proves neither its
  installation nor its correct behavior in a booted OS.
- **Scoped verification:** an identified test observed the stated behavior in
  its recorded environment. Its limitations travel with the result.
- **Unverified:** the integrated behavior or target hardware outcome has not
  been established. An absent measurement is not a pass.
- **Missing:** the required implementation does not yet exist.

The exact reviewed commit's [CI run 42172398708](https://github.com/RezoxNemesis/OREZ-OS/actions/runs/42172398708)
reports 210 source cases, 38 package paths and 68 browser-preview cases passing;
the full ISO job was skipped. See the retained
[CI record](evidence/2026-11-06-installer-graphics/ci-direct-session.json).
These counts do not establish update recovery, privacy, performance or driver
compatibility. Browser-preview screenshots are not booted desktop screenshots.

Earlier actual ISO boots established a scoped owner-enrollment/PAM path and
passwordless-sudo refusal. They also exposed the inherited live session's
installer-prompt wrapper instead of a directly usable Plasma session. The
reviewed source selects a dedicated OREZ native Plasma session. Its corrected
development ISO, SHA-256
`6ca85cf37d48beeb8ac0fd6ffa99e94cc9806949584a970916024ddf30d80ac6`,
was **still under normal-boot testing at this review**. A later handoff and
associated evidence must establish its outcome; this document does not.

The offline installer candidate and exact eight-package cleanup simulation
retain SMB support (`cifs-utils`) and avoid optional installation-time network
downloads. They are inactive and do not execute package maintainer scripts.
No safe installed-system, driver-update or recovery certification follows.

## Complaint-to-engineering gap assessment

| Concern | Required OREZ behavior | What actually exists | Gap before claiming the benefit |
|---|---|---|---|
| Broken updates | Show provenance, size, restart needs and recovery; preserve owner policy and saved work; no forced session restart | Ordinary Debian package payload; documented offline previous-version upgrade and failure simulations | **Missing:** maintained signed OREZ update channel and complete recovery integration. **Unverified:** interrupted whole-system updates, kernel/initramfs failure and installed recovery |
| Unwanted data collection | Explain background network traffic and data flows, provide appropriate controls and redacted local diagnostics | First-party CLI reports are on demand; wallpaper initialization is local; Store asks before opening publisher information | **Missing:** complete effective inventory and owner-facing privacy view. **Unverified:** inherited services, browser defaults and actual network behavior. No basis for a blanket “zero telemetry” claim |
| Difficult driver maintenance | Use maintained distro packages, show selected driver/kernel/signing state, retain a recoverable previous state | Read-only hardware/preflight checks; supported NVIDIA package strategy documented | **Missing:** integrated driver guidance/recovery path. **Unverified:** RTX 3050, Secure Boot/MOK, actual kernel/driver upgrade and rollback |
| Background work reducing FPS | Small idle footprint, explicit optional services, scheduled maintenance, measured frame pacing | `orezctl performance` is a one-shot report; no resident OREZ performance optimizer; Android does not autostart | **Unverified:** full idle service inventory, CPU/RAM/power, 6/16 GiB workloads and game frametimes. Actual offline TCG boot logs include a pending `snapd.seeded.service`; cause and physical impact remain unresolved |
| Debloating effort | Ship a justified package set; show optional apps/services and dependency-aware removal/reset | Package inventory and allowlisted OREZ payload; visible wallpaper opt-out; Store activity controls | **Missing:** integrated app/service purpose and removal inventory. Store currently detects/opens native apps and supplies installation information; it is not an implemented package installer/updater |
| Hidden or fragmented settings | Searchable routes to effective controls, status, implications, reset and logs | `orez-settings` delegates to KDE System Settings; `orezctl` opens native network, Bluetooth, power and file management | **Missing:** dedicated OREZ Settings integration and coverage index. **Unverified:** discoverability, accessibility and consistent integrated navigation |
| Familiar desktop behavior | Reliable login, taskbar, windows, shortcuts, workspaces, files and fullscreen applications | Native KDE/Plasma foundation and OREZ branding/session code | **Unverified:** complete normal boot and installed-session lifecycle at this review. Branding does not itself prove native desktop correctness |

## First-release behavior that must be demonstrable

### Updates and recovery

Use maintained upstream package paths and a properly signed, scoped OREZ
channel. List each origin and trust root visibly. A checksum alone is not an
authenticated release, and a valid signature is not authorization to expand
permissions. Package maintainer scripts and kernel drivers can run privileged
code; review and trust in their supply chain remain necessary.

Separate update **checking/downloading** from installation and reboot policy.
Show scheduled work, metered-network handling, pending restart and failures.
Never silently reboot, kill an application or replace a user's security choices.
Background security maintenance must be documented and configurable with clear
consequences rather than hidden or disabled merely to win a benchmark.

Before applying an update, check disk space, dependencies, signatures and a
usable recovery path. Retain a known-good kernel and compatible modules. APT
transactions are not atomic filesystem deployments: interrupted `dpkg`,
initramfs and bootloader operations need explicit repair tests. First release
may use documented, tested recovery media and manual repair; do not advertise
instant or automatic rollback unless implemented and tested.

Snapshots cover only the paths actually included. Keep separate recoverable
backups of important data. Restoring system state must preserve current device
revocations, owner credentials and policy unless the owner deliberately reviews
a change. Do not silently restore vulnerable packages or roll back personal
documents. Define how incompatible data migrations are handled before shipping
them. Tests and evidence requirements are in
[REL-UPD and REL-AUTH](qa/RELIABILITY_TEST_CASES.md).

### Privacy and owner authority

Create a versioned inventory of every shipped service, scheduled job, network
listener and network-using integration: purpose, publisher/package, privilege,
activation, endpoints or endpoint classes, data categories, log retention,
control location, disable/remove effects and recovery. Include inherited distro
components, updates, time synchronization, connectivity checks, browser services
and optional phone integration. Unknown behavior remains an explicit issue.

First-party OREZ components must not collect keyboard contents, passwords,
financial activity, microphone/camera data or browsing contents for monitoring.
Diagnostic sharing is a visible, opt-in action with preview/redaction. Logs use
bounded retention, restrictive access and no stored secrets. Independent packet
capture corroborates endpoint/activation inventory but cannot establish the
contents of encrypted traffic by itself; review configuration and upstream
documentation too.

Brave, Google, games and other providers may process data when their services
are used. Explain their permissions and data controls independently of OREZ's
policy. Provider sign-in grants no Linux account, sudo authority, recovery key
or system-management role. Ordinary native apps under the owner's UID can still
read that user's permitted files unless separately sandboxed. Vendor packages
and the browser's sandbox helper are trusted privileged code where applicable,
not proof of a vendor remotely holding an administrator account. Do not remove
browser sandbox protections to make a test pass.

No AI, website, MCP response or input heuristic grants authorization. Keep
administrator authentication independent of the application requesting action.
There is no implemented autonomous OREZ malware detector or AI privileged
broker. An unavailable feature stays visibly unavailable. Future monitoring
starts with observable evidence and notifications; timing a mouse or keyboard
cannot reliably determine whether an action belongs to the owner.

### Drivers, resources and games

The Ryzen 5 5600 has no integrated GPU: a broken dedicated NVIDIA path needs a
tested console/recovery route. Qualify an exact supported distro
kernel/NVIDIA-module/userspace tuple on the RTX 3050 6 GB. Record Secure Boot
state, module signature and any explicit owner MOK enrollment. Do not silently
disable Secure Boot, mix the vendor `.run` installer with distro packages, flash
firmware or invent an unsupported GPU “unlock.” Software cannot add VRAM or
upgrade the motherboard's Wi-Fi/Bluetooth radio generation.

Use [PERFORMANCE.md](PERFORMANCE.md)'s existing budgets. In particular, fresh
desktop working-set target is at most 1.5 GiB after five minutes, launcher and
settings target p95 response is at most 150 ms, 1080p video target is under 1%
dropped frames across ten minutes, and an eight-hour mixed-use soak has no
session loss, OOM kill or hang. These are **targets, not achieved figures**.
Do not describe Linux cache as wasted RAM or sum shared RSS to claim physical
memory use. Record the measurement definition, cache, kernel and swap separately.

Use enforced 6 GiB and actual 16 GiB scenarios. Containers without enforced
cgroups and TCG software-rendered VMs are component/debug evidence only. Use
matched real-hardware samples for game p95/p99 frame times, 1% lows, power and
thermal behavior. Investigate a reproducible regression; never promise higher
FPS for every game or lower energy from a shorter benchmark alone.

Schedule optional indexing, scans, downloads and backup work visibly. Avoid
duplicate updaters, boot-time AI/Android loads, periodic cache purges, blanket
service removal, weakened security or permanent maximum clocks. Disabling a
feature must name its dependency and consequences. Keep update/security checks
functional when measuring production defaults.

### Settings and desktop ergonomics

Reuse native KDE controls and established backends. An OREZ navigation layer
should show the effective backend value and link to its actual control instead
of keeping a contradictory second setting. Search terms must include ordinary
words such as Wi-Fi, password, Bluetooth, startup, permissions, updates, drivers,
backup, power, display, camera and microphone. Initially a clear indexed set of
native routes is preferable to recreating every KCM.

For each OREZ feature expose enabled state, purpose, data/permission effects,
configure/disable where appropriate, reset/restore, logs and its package/service
identity. Explain when administrator authentication is needed. Keep every
significant control reachable by keyboard and usable with reduced motion,
opaque panels and accessible contrast. Do not require the terminal for normal
networking, software updates or routine preference changes; retain the terminal
for professional use and recovery.

## Next implementation tasks, in dependency order

1. **Qualify the current direct Plasma boot before broadening features.** Finish
   normal offline UEFI boot, record session/service states, verify the installer
   prompt no longer intercepts login, then lock/unlock/logout/reboot. Investigate
   pending live services from evidence, without blanket removal. Capture actual
   screens and logs; keep the installer safety block meanwhile.
2. **Finish the disposable-disk installation and recovery path.** Enable the
   candidate only after install/reboot account policy, cleanup, dual-boot data
   preservation and optional encryption/recovery tests. Resolve the known
   installed AppArmor and `crypttab` issues identified in SECURITY.md.
3. **Produce the effective inventory from a booted candidate.** Capture packages,
   services, timers, autostarts, listeners, repositories and trust roots. Review
   each OREZ/vendor addition and inherited data flow; publish a human-readable
   control map with owners and unresolved entries. Do not add a resident monitor
   solely to generate this one-time inventory.
4. **Implement maintainable updates and document recovery.** Establish scoped
   signing/key rotation and protected release CI, package provenance, update
   failure display and a tested restore path. Test policy migrations and power
   interruptions on disposable disks before routine owner use.
5. **Add searchable OREZ settings routes and inventories.** Keep KDE controls as
   the authority; integrate update/recovery/privacy/service links and visible
   reset/status. Describe application removal dependency effects before applying
   it. Do not mislabel the present Store catalog as an installer.
6. **Qualify physical driver, privacy and performance gates.** Collect the exact
   PCI/USB IDs, kernel/NVIDIA versions and Secure Boot state. Execute the case
   matrix below on the target PC once live and recovery media are qualified.
   Tune only against recorded regressions with a reversible change.
7. **Close the release ledger.** Every blocking case has an exact artifact hash,
   environment, result and evidence; missing equipment yields BLOCKED, never
   PASS. Complete independent security/license/signing and owner-access gates
   already required elsewhere. Publish installation media only after approval
   criteria actually pass; a development screenshot bundle is not that media.

The first four tasks protect the basic boot/install/update lifecycle. Cosmetic
refinement, consumer Android compatibility and autonomous security responses
must not displace them. Existing AI functionality must still meet the owner's
first-release requirements and permission boundary before it can be advertised.

## Source and evidence references

- [`orezctl`](../overlay/usr/bin/orezctl),
  [`orez-settings`](../overlay/usr/bin/orez-settings),
  [`orez-preflight`](../overlay/usr/bin/orez-preflight): native routes and
  read-only reports, not continuous protection or tuning.
- [Wallpaper autostart](../overlay/etc/xdg/autostart/orez-initialize.desktop):
  named, one-time local customization with visible opt-out.
- [Store manager](../overlay/usr/lib/orez/store_manager.py) and
  [Store UI](../overlay/usr/lib/orez/store_ui.py): native executable detection,
  publisher-information confirmation and transparent Android pending state.
- [Image application security audit](evidence/2026-11-06-image-apps/security-audit.json):
  staged package/policy facts, including Brave update source and sandbox helper;
  explicitly not running desktop enforcement.
- [Architecture](ARCHITECTURE.md), [hardware](HARDWARE.md),
  [security](SECURITY.md), [live assembly](LIVE_ASSEMBLY.md) and
  [latest handoff](AI_HANDOFF.md): integrated status and remaining gates.

No promise of zero failures, perfect intrusion detection, absence of provider
data collection or universal performance superiority follows from this plan.
OREZ's distinct advantage must be demonstrated through transparent controls,
recoverable changes and measured behavior on the owner's machine.
