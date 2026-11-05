# OREZ Store — native applications and real Android integration

Latest owner scope (5 November 2026): **finish the first PC release before Android emulation.** Native Brave/VLC/Linux games, explicitly authorized web YouTube, owner login, OREZ Calendar/Reuz, themes, AI permissions and connectivity take priority. See [FIRST_PC_RELEASE.md](FIRST_PC_RELEASE.md) for implementation, test limits and blocking gates. No installable release is approved. This supersedes older Android-first and web-YouTube-prohibited statements for the first release only.

## Product decision, 5 November 2026

The owner explicitly requires **actual Android applications**, including YouTube,
Instagram, Subway Surfers, Free Fire and Asphalt Legends. A website shortcut,
PWA or browser app window does not satisfy this requirement. Where an official
Linux desktop version exists, prefer that version unchanged: Brave, Chrome, VLC
and SuperTux are native entries. Do not repackage them as Android apps, modify
upstream binaries or install mappings for native Linux apps. Android games may use automatic,
visible presets without manual setup, as the owner explicitly confirmed. The earlier web-shortcut
proposal was rejected and removed before this implementation was committed.

The Store itself is free. Use official free base downloads where offered, with
publisher identity, permissions and compatibility visible. Optional purchases,
subscriptions, regional availability and publisher restrictions remain separate.
No paid feature unlocks, mirrored commercial APKs, purchase automation or account
credentials are bundled. Store use is optional; ordinary package managers and
the terminal remain available to the owner.

**Current boundary:** the native catalog, search, filters, local action log,
installed-native-app detection and native launch actions are implemented.
Consumer Android installation, a running Android guest, Android app playback,
keyboard/mouse gameplay and per-app desktop windows are **not delivered yet**.
A catalog entry is not a working application. The browser preview cannot launch
or install anything and explicitly says so.

## Implemented components

- `orez-store` / `orezctl store`: ordinary-user PySide6 Qt Widgets window. No
  Electron engine, resident downloader, network listener or privileged helper.
- `store-catalog.json`: shared, validated catalog for native GUI and preview;
  ten entries, six Android and four native. HTTPS publisher links are information
  only, require an explicit GUI action and never substitute for the application.
- Native launch: fixed absolute command allowlist, no shell or arbitrary catalog
  commands. Detecting a binary is not a sandbox or compatibility certification.
  The official Linux browser's existing profile and settings are left to it.
- Android controls: opening the development manager requires acknowledgment;
  it does not accept SDK terms, start a guest or install apps automatically.
- Development Android adapter: `orez-android app-status`, `open-app`,
  `store-page`, `app-settings`, with `--app <reviewed-alias>` and explicit
  `--development-test`. Require the owned OREZ emulator process and AVD name;
  fixed loopback ADB port 5038, serial `emulator-5556`, no attached-phone target.
  Open a verified Android launcher component or a package-specific guest intent,
  never a website fallback. Commands are bounded and errors remain errors.
  The flag is not a consumer licence grant. Adapter tests use controlled mocks;
  they do not prove an emulator or downloaded application worked.

## Runtime direction and licensing gates

Use one shared, opt-in Android runtime with per-app desktop launchers, bounded
resources, visible stop/reset/uninstall and no host-home sharing by default.
Prefer a maintained virtual-machine provider for a stronger host boundary;
qualify GPU support, lifecycle and application licences before consumer shipping.
Waydroid remains a candidate to evaluate, not an already-supported fallback:
its documentation identifies NVIDIA/software rendering constraints and its
shared kernel is a different isolation boundary.

Google's SDK emulator is currently an optional **development/testing provider**.
Its terms and a Google Play image do not grant OREZ blanket consumer distribution
rights. A maintained consumer provider, its licences and the Google Play access
path are unresolved. Do not bundle unreviewed Google services, spoof certification
or bypass Play Integrity/anti-cheat. Accounts must be entered privately in the
qualified guest by the owner; no credentials in OREZ settings or screenshots.

## Keyboard and mouse: automatic presets, no manual setup

The owner explicitly confirmed **automatic presets; no manual setup** after
providing the BlueStacks/Free Fire example. This replaces the earlier literal
interpretation that no input translation was allowed. Prefer an app's own
keyboard/mouse support; for Android games that need it, use visible, maintained
presets that translate controls inside the active game. Native Linux apps retain
their existing controls unchanged.

Product flow: install through the qualified provider, choose Play, and load a
compatible preset automatically. Show a dismissible controls overlay and a
per-game Controls entry with effective preset/version, sensitivity, reset,
disable and optional editing. Initial setup must not require drawing touch
zones or manually assigning keys. OREZ must not claim that preset support exists
until it works with an actual game and runtime.

Engineering requirements for the future input adapter:

- Profiles identify Android package, tested app/runtime versions, orientation,
  resolution/layout assumptions, supported actions and provenance. Use a
  declarative schema and reviewed release integrity; never execute downloaded
  scripts or copy proprietary BlueStacks profiles.
- Capture events only in the focused, visible OREZ guest/game window. Send them
  through the runtime's narrow guest-input API. No root helper, host `/dev/uinput`
  writer, global keyboard logger or cross-application input injection.
- Release every held key/touch immediately on focus loss, lock, pause, close,
  runtime failure, device revocation or emergency stop. An always-visible
  release-pointer/stop control remains available; do not trap owner input.
- Show a known-compatible preset automatically. Detect app/runtime/layout
  changes; never silently reuse stale touch coordinates as verified controls.
  If compatibility is unknown, explain the limitation and preserve native
  guest input. Native controls may still be usable; do not invent a game pass.
- No macros, automated play, anti-cheat evasion or certification spoofing. Respect
  publisher emulator/input policy. Profile changes are visible and reversible,
  with data-only logs that never capture chat, passwords or typed content.

Acceptance: actual app launch; default typing/pointer/scrolling; automatically
loaded game movement, aim and essential actions; resize/orientation; simultaneous
input; focus loss and emergency release; pause/resume; update and stale-profile
handling; disabled/revoked mode. Record exact app/runtime/preset versions and
screenshots. Test native Linux controls separately without any preset adapter.
A successful launch, a frame capture and full functionality are distinct gates.

**Status:** automatic presets are now an approved requirement and planned work.
No preset engine or tested Android game profile is implemented by this session.
The existing developer app-launch adapter is not an input-mapping engine.

## Permissions, transparency and updates

Store commands reject root and never grant administrator authority. Logs and
managed state use private user permissions; action logs contain timestamp,
action and catalog ID, not account credentials. Launch logs may contain private
upstream error details. Location: `~/.local/share/orez/store/` (or XDG data home).
Activity and controls explains storage and current runtime boundaries. The Store
has no autostart; closing it stops its UI, not a separately launched native app.

Ordinary native apps can access user-owned files. **No administrator access is
not the same as no sensitive-data access.** Upstream browser sandboxes protect
particular process boundaries, not all files from the browser's main process.
Do not promise otherwise. Android filesystem, clipboard, microphone, camera,
USB, network and screen-capture defaults still require real guest verification
and visible per-feature controls before release.

App updates must use authenticated upstream package mechanisms or the qualified
Android store inside the guest. No owner/admin bypass, remote policy mutation
or silent upgrade grant. Store component upgrades use the OREZ Debian package;
preserve user files/preferences and verify downgrade/recovery separately.
The inherited live ISO's blank-password/passwordless-sudo/wildcard-Polkit issues
remain release blockers: this Store does not solve the live authentication gate.

## Packaging and tests

Component package is `orez-shell` **0.1.0-3**, 28 allowlisted payload paths.
`python3-pyside6.qtwidgets` is a declared dependency. The QA recipe additionally
installs QtTest for GUI interaction. Qt/PySide remain distribution dependencies;
retain their notices and satisfy the exact component LGPL/GPL/commercial terms,
including applicable source/relinking obligations. No claim that proprietary
original code removes third-party licence duties.

The retained Kubuntu base ISO does not contain PySide6, and both retained OREZ
ISOs predate this Store. Source overlay copying alone does not resolve missing
GUI dependencies. Provision authenticated dependencies in a reproducible image
step, verify live and installed roots separately, then test a new ISO. No full
ISO was rebuilt or released for this feature; installer remains disabled.

Local evidence for this session is `dist/evidence/qa7-*` and the final handoff.
Runs 01–10 include the superseded web-first proposal, fixture failures and the
unchanged-path collision audit. Runs 11–14 switch to actual Android targets;
runs 15 onward apply the owner's preference for unchanged Linux versions.
Keep all attempts and their screenshots. Native Qt/Xvfb tests are component
checks in a disposable container, not proof of an installed OREZ desktop, GPU
performance, real speakers, Android downloads or target-PC compatibility.

## Next implementation gates

1. Publish the maintained QA environment on a host providing real KVM and usable
   graphics, enforced memory limits, and functioning browser sandbox namespaces.
   Packages alone cannot create these host capabilities. Never disable the
   browser sandbox, AppArmor or kernel protections to make tests pass.
2. Select and document the qualified consumer runtime/licensing path. Boot a
   real guest, audit host isolation and resource controls, then implement actual
   install progress/cancel/retry, installed-library state and per-app launchers.
3. Test actual YouTube/Instagram and chosen free casual games. Capture launch,
   playback/input, close/reopen, offline/error, permission revocation and update
   scenarios. Record direct keyboard/mouse limitations honestly; use automatic presets only after actual guest/game qualification.
4. Implement authenticated native-app installation/update UI through the system
   package broker with owner-visible package plans and cancellation. Current
   native install buttons only open official information.
5. Resolve live-owner authentication and GUI dependency provisioning before
   ISO/installer/hardware acceptance. The sole owner remains administrator.

## Official references consulted

- [Brave Linux installation](https://brave.com/linux/): official native package;
  upstream warns that Flatpak modifies Chromium sandboxing without Brave vetting.
- [Chrome official download](https://www.google.com/chrome/)
- [VideoLAN VLC](https://www.videolan.org/vlc/)
- [Android Emulator](https://developer.android.com/studio/run/emulator),
  [acceleration](https://developer.android.com/studio/run/emulator-acceleration),
  [SDK terms](https://developer.android.com/studio/terms)
- [Waydroid GPU/VM constraints](https://docs.waydro.id/faq/get-waydroid-to-work-through-a-vm)
- [Flatpak permissions](https://docs.flatpak.org/en/latest/sandbox-permissions.html):
  requested broad permissions change the effective isolation; labels are not proof.
- [Qt for Python licences](https://doc.qt.io/qtforpython-6/licenses.html),
  [Qt LGPL obligations](https://www.qt.io/development/open-source-lgpl-obligations)
- Publisher listings: [Subway Surfers](https://play.google.com/store/apps/details?id=com.kiloo.subwaysurf),
  [Free Fire](https://play.google.com/store/apps/details?id=com.dts.freefireth),
  [Asphalt Legends](https://play.google.com/store/apps/details?id=com.gameloft.android.ANMP.GloftA9HM).

- [BlueStacks Free Fire Smart Controls](https://support.bluestacks.com/hc/en-us/articles/11055358500109-How-to-play-Free-Fire-with-Smart-controls-on-BlueStacks-5)
- [BlueStacks control schemes](https://support.bluestacks.com/hc/en-us/articles/360058810512-How-to-create-and-edit-keyboard-controls-for-Free-Fire-on-BlueStacks-5)

BlueStacks is an experience reference, not an OREZ dependency or proof of a
working Linux provider. No BlueStacks binary, proprietary preset or game asset
is copied. The approved automatic presets must be visible, reversible,
limited to the focused guest, version-tested and compatible with game policy.
