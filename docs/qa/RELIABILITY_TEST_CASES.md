# Reliability and owner-control acceptance cases

Defined **6 November 2026** against reviewed source commit
`56af0a24133985d225ac22c2e85a6f3cb050f483`. These are **unexecuted acceptance
cases**, not test results. [The reliability contract](../RELIABILITY_AND_CONTROL.md)
states current gaps; [PERFORMANCE.md](../PERFORMANCE.md) owns resource targets.
This review does not modify runtime policy or claim any new screenshots.

## Execution and evidence rules

Run destructive fault injection only on identified disposable virtual disks
whose paths and backing files have been checked. Never attach the owner's NVMe,
Windows USB or physical block devices to these tests. Preserve a clean snapshot
per scenario and use synthetic data/accounts only. Installation and recovery
need a functioning booted candidate; source tests do not satisfy that prerequisite.

For every attempt retain: UTC time, case ID, PASS/FAIL/BLOCKED/NOT RUN, commit,
ISO SHA-256, package/driver versions, firmware/Secure Boot state, VM or physical
hardware, exact steps/parameters, expected and observed result, logs and real
PNG screenshot paths. Store secrets only in the disposable test environment;
redact passwords, tokens, serials and personal data from published evidence.
Screenshots demonstrate visible state; logs, hashes and measurements establish
nonvisual claims. A rendered report image must be labeled as a report, never as
a running OS screen. Keep failures and retries in the ledger.

All listed cases block the relevant first-release claim. Optional functionality
may be explicitly unavailable, but cannot be shown as working. Physical-device
cases may first be BLOCKED in the lab; release qualification still needs their
actual target results. Fixes require rerunning affected cases, not unrelated
expensive suites without a reason.

## REL-BOOT — normal desktop and install prerequisite

1. Cold-boot exact media in UEFI with the network disconnected. Complete temporary
   live enrollment without revealing the password, authenticate in SDDM and
   obtain a usable native Plasma desktop. Confirm terminal, Dolphin, Settings,
   taskbar and window/workspace operations. Verify wrong-password rejection,
   passwordless-sudo denial, lock/unlock and logout/login.
2. Record actual active/failed/activating units and time-to-desktop. A lingering
   live installer prompt or unexplained startup dependency blocks qualification.
   Diagnose `snapd.seeded.service` if still pending; do not call TCG timing a
   target-PC performance measurement.
3. Install only to a disposable guest disk using explicit disk confirmation,
   owner-chosen credentials and no optional network dependency. Reboot without
   media. Repeat ordinary and encrypted paths when both are offered; confirm
   expected AppArmor and `crypttab` behavior, no live-only bypasses or installer
   account residue, and recovery access.

**Pass:** usable authenticated desktop and installed reboot; false credentials
and unprivileged elevation denied; saved fixture survives; offered recovery
works. Include boot/login/home/settings PNGs and journal/package evidence.

## REL-UPD-01 — trusted update and owner-visible lifecycle

Use a dedicated signed test repository and disposable keys; never production
signing secrets. Exercise old-to-new OREZ package plus a supported distro
kernel/application update, including no-update and already-updated cases.

- Show origin, old/new versions, download size, restart need and changelog;
  document trust-root scope. Confirm usable failure/cancel/retry status and logs.
- Reject modified payload, invalid signature, expired repository metadata when
  expiry applies, wrong origin/key and unauthorized downgrade. Test key rotation
  and removed-key behavior according to the actual documented trust procedure.
- Keep an unsaved synthetic document and long-running user task open; updates
  must not force logout, reboot or terminate those tasks. Separate restart
  notification from an owner-initiated restart.
- Disconnect/reconnect the network, choose a metered connection and change the
  maintenance window; observe the documented schedule/download policy.
- Verify current package versions and no broken dependencies after success.

**Pass:** authentic scoped updates succeed; invalid inputs fail closed with an
actionable error; scheduling matches visible settings; owner work is preserved.
No authenticated update channel means BLOCKED, not a checksum-only substitute.

## REL-UPD-02 — interruption, repair and rollback

Prepare fsynced synthetic document canaries, a separate backup, recorded owner
policy/credential state and one revoked test device. Retain a previous supported
kernel/module combination and tested recovery media. Do not store production
credentials in the evidence. Record and verify the intended interruption point.

Inject virtual power loss separately during (a) download, (b) package unpack,
(c) package configuration, (d) initramfs generation and (e) boot-entry update
when that stage is used. Also test full destination filesystem, interrupted
dependency resolution and a controlled maintainer-script failure from a test
package. Repeat each power-loss stage twice from fresh state; enumerate any
unreachable stage as BLOCKED rather than pretending it ran.

For each failure, boot the normal/previous entry or trusted recovery media and
follow the exact documented repair path. Check filesystem, dpkg/APT state,
boot artifacts, signing, networking and user login; then complete a subsequent
update. A normal boot need not magically repair every interrupted `dpkg`
transaction, but the documented recovery must actually work.

**Pass:** recover to a bootable supported state; no lost fsynced fixture data,
silent credential change, revived device grant or weakened security policy;
no partial update shown as success. Record recovery duration and manual steps.
Set a usability target of at most **20 minutes of operator work**, excluding
download/restore transfer time, for the documented routine recovery path; this
target is unmeasured and may only change through a recorded decision.

Test snapshot restore separately from independent backup restore after deleting
the disposable guest's primary data. Confirm that a stale snapshot does not
silently undo revocations or user documents. A rollback into a known vulnerable
version needs an explicit warning and supported recovery/update path; it is not
an acceptable silent steady state. Filesystem or physical-drive failures beyond
these scenarios remain risks, not claimed coverage.

## REL-AUTH — invariants across update, restore and settings

Record effective accounts/admin-group membership, root lock state, sudo and
Polkit rules, listeners/firewall, trust roots, enabled services, device grants
and AI/remote-control state. Compare before/after install, upgrade, failed-update
repair and restore. Inspect effective runtime policy, not only source text.

- Only the enrolled owner is the intended human administrator. Wrong/canceled
  authentication, ordinary application execution, provider sign-in, untrusted
  web content and AI output must not authorize administrative effects.
- Attempt changes to privileged policy from the ordinary application account
  and verify denial. Where applications share the owner UID, document that
  same-user file access is possible unless separately sandboxed.
- An update attempting a new admin grant, remote listener, trust root or weaker
  protection must stop for a separately authenticated owner decision or be
  rejected by the supported policy path. Package signatures alone do not grant
  this new scope. Trusted root package scripts remain part of the threat model.
- Existing opted-out integrations and revoked devices stay opted out/revoked.
  Security patches remain installable; do not freeze security software forever.
- If the AI broker is absent, it stays unavailable. If supplied later, verify
  exact-parameter approval, cancellation, narrow grants, expiration, emergency
  stop and revocation with ordinary and adversarial requests.

**Pass:** no unexplained authority expansion or bypass; policy changes are
traceable and authenticated, credentials are absent from logs. A static absence
of `NOPASSWD` alone is insufficient to certify the complete privilege boundary.

## REL-PRIV — data flows and background exposure

Generate the package/service/timer/autostart/listener/repository inventory from
the running default candidate. Match each entry to purpose, privilege, activation,
data categories, endpoint classes, retention, control and reset/removal.

From an external lab capture point record: first boot (30 minutes), idle (30
minutes), update check, Brave launch/site visit, optional phone pairing and
explicit diagnostic export. Repeat relevant scenarios after disabling optional
features. Review config/source/vendor documentation for encrypted payload
semantics; TLS packet capture alone cannot prove what data was sent.

**Pass:** every observed OREZ/system-owned endpoint has an explained purpose and
documented control; no undisclosed listening service or prohibited first-party
content collection; disabled optional integrations cease their stated traffic.
Record unavoidable or essential traffic and security consequences rather than
promising complete silence. Separate app/site data collection from OS behavior.
Inspect diagnostic preview/redaction and log access/retention. Published capture
summaries must omit real user tokens, browsing history and device identifiers.

## REL-DRV — RTX 3050, kernel updates and Secure Boot

Use the actual Ryzen 5600/RTX 3050 machine after live/recovery qualification;
record PCI IDs, monitor connection, driver/kernel/userspace versions and module
signatures. Test offered supported Secure Boot modes independently. MOK enrollment
or firmware changes require the owner's explicit actions and recorded choices.

1. Verify graphical login, acceleration, Vulkan/OpenGL, supported video decode,
   display sleep/wake, fullscreen game/video and audio. Record real renderer so
   software rendering cannot masquerade as GPU success.
2. Perform a supported kernel/NVIDIA update and reboot. Confirm signed-module
   acceptance, working graphics and retained known-good kernel/modules.
3. In a controlled recovery test, exercise missing/incompatible module and
   signature rejection without compromising the owner's normal system; use a
   disposable test installation or equivalent safe setup. Recover via documented
   console/known-good boot/media, since this CPU has no integrated GPU.

**Pass:** supported package tuples work, failed updates have demonstrated recovery
and the owner can inspect version/signing/error state. No silent Secure Boot
disable, firmware flash, unsupported module patch or permanent maximum clocks.
No GPU hardware means BLOCKED; a virtio display is not NVIDIA certification.

## REL-PERF — responsiveness, games and energy

Record physical hardware or enforced VM limits, OS/driver version, monitor
refresh, game/app version, resolution, settings, compositor, power profile,
temperature, background jobs and cold/warm cache condition. Use production
security defaults. Do not compare different drivers or power profiles and
attribute the difference to OREZ.

- Measure three fresh-login idle runs after five minutes with CPU, memory,
  cache/kernel/swap accounting, I/O, processes, timers and package inventory.
  Apply the existing 1.5 GiB working-set target with a documented accounting
  method; report shared-memory handling rather than summing RSS.
- On enforced 6 GiB and actual 16 GiB configurations, run terminal, Dolphin,
  Settings, a fixed modest browser workload and ten minutes of 1080p VLC
  playback. Record memory pressure, OOM events, app response and dropped frames.
  Apply the existing p95 150 ms and under-1%-dropped-frames targets with suitable
  measurement equipment; API latency is not input-to-visible latency.
- Repeat a fixed game scene at least five times per candidate/baseline using
  the same hardware and supported drivers. Report median FPS, 1% lows and
  p95/p99 frame times with run-to-run spread. Alternate run order to reduce
  thermal/cache bias. Prefer repeatable bundled free Linux games first.
- Repeat with a pending update/download/backup scenario and visible scheduling
  policy. As an initial regression guard, investigate and block an unexplained
  repeatable worsening above **5%** in p95/p99 frame time or 1% lows versus the
  matched previous candidate, outside baseline variability. This is a proposed
  comparison guard, not a promised FPS gain; record any justified decision.
- Record idle CPU and power plus energy for a completed fixed workload where
  reliable instrumentation exists. Target no continuously busy first-party OREZ
  process at idle. Report actual numbers; do not claim whole-machine energy
  from CPU package counters alone.
- Complete the existing eight-hour mixed-workload soak: no session loss, hang
  or OOM kill. Record suspend/resume, thermal throttling and recovery behavior;
  follow with the planned multi-day pilot.

**Pass:** existing performance budgets and evidence requirements are met, no
unresolved repeatable regression, and no security reduction to obtain results.
Network buffering and unbounded heavy workloads cannot be certified away.

## REL-CONTROL — services, removal and searchable settings

Use ordinary-user UI tasks with fresh accounts: find Wi-Fi/password/connectivity,
Bluetooth, phone sharing, startup apps, power, display, permissions, updates,
driver state, backup/recovery, logs and reduced-motion/opaque-panel settings.
Include keyboard-only navigation, 125%/150% display scaling and contrast checks.

For every significant OREZ component verify purpose, effective status, permission
effects, logs, disable/configure where appropriate, reset and package/service
identity. Native KDE routes must reflect actual backend state. Test search terms
and synonyms rather than only memorized menu paths; the target is a relevant
result from Settings search and at most two further navigation actions to its
control. Record missing routes explicitly.

Choose optional applications/services, show dependency consequences and remove
them through a supported package path. Reboot and verify the removed component
does not silently return or leave a running listener/timer. Reinstall/reset and
verify recovery. Essential dependency/security warnings must be specific; avoid
blanket removal scripts or uninstalling the desktop during a routine app removal.

**Pass:** required controls are discoverable and functional, values agree with
the backend, removal is transparent and recoverable, and the owner can complete
normal tasks without terminal-only hidden configuration. Retain actual settings,
confirmation, disabled-state and restored-state screenshots for executed cases.

## Release decision

Link each case's completed evidence into the release ledger and latest handoff.
No percentage complete substitutes for failed or blocked boot/install/security/
recovery gates. A different source commit, package set or image hash must state
which prior results remain applicable and which must be repeated. This matrix
adds no claim that the current ISO is installable or safe for sensitive work.
