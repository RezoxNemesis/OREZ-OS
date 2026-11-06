# OREZ graphical login blocker — investigation record

Status: 6 November 2026. **Open blocker. Diagnostic instrumentation is committed; no login fix is claimed.**

## Confirmed boot behaviour

Image SHA-256: `6ca85cf37d48beeb8ac0fd6ffa99e94cc9806949584a970916024ddf30d80ac6`.

- The default-menu UEFI boot completed local owner enrollment with concealed password entries.
- SDDM selected `/usr/share/orez/wayland-sessions/orez.desktop`.
- PAM authentication succeeded and opened the ordinary owner session.
- SDDM logged `Session started true`, then `sddm-helper exited with 64`; the greeter restarted.
- A separate manual `startplasma-wayland` launch from an authenticated ordinary-owner TTY rendered Plasma Welcome, wallpaper, panel, tray and Settings. This is not a normal SDDM login pass.

Primary evidence: `docs/evidence/2026-11-06-installer-graphics/qa12-17-vm-result.json`, `guest-journal-excerpt.json`, `startup-source-review.json`, and `LIVE_ASSEMBLY.md`.

## What exit status 64 means — and does not mean

The pinned SDDM source reviewed for the image defines its own `HelperExitStatus` values as 0 through 5. For a Wayland user session, SDDM starts its configured `Wayland.SessionCommand` with the selected desktop file's Exec command. When that process finishes, `UserSession` forwards its numeric exit code to `HelperApp::sessionFinished(int status)`, which exits with that same value. Therefore the observed 64 is **the exit code returned by the configured Wayland session command chain**, not one of SDDM's ordinary helper-status enum values. It does not yet identify which inner command returned 64.

Pinned source references:
- [SDDM Auth helper status enum](https://github.com/sddm/sddm/blob/4fe234b/src/auth/Auth.h#L83-L89)
- [SDDM connects session completion and forwards the status](https://github.com/sddm/sddm/blob/4fe234b/src/helper/HelperApp.cpp#L128-L130) and [exit forwarding](https://github.com/sddm/sddm/blob/4fe234b/src/helper/HelperApp.cpp#L196-L198)
- [SDDM launches the configured Wayland session command](https://github.com/sddm/sddm/blob/4fe234b/src/helper/UserSession.cpp#L114-L127)

The reviewed KDE Plasma 6.6.6 `startplasma-wayland` main path explicitly returns 1 for D-Bus setup failures, 4 when Plasma session start fails, and 0 after normal shutdown. It does not show an explicit 64 return in that file. This narrows the next trace, but does not rule out a downstream script, a library, a child, or another process in the launched chain. [Pinned KDE source](https://github.com/KDE/plasma-workspace/blob/v6.6.6/startkde/startplasma-wayland.cpp).

## The utmpx warning is separate

The journal also contains `Failed to write utmpx: No such file or directory`. This is a known compatibility warning: Debian maintainers documented that systemd 256.7-2 disabled legacy utmp support, so `/run/utmp` is no longer created by systemd on those systems. The warning is not evidence that the login exited because of utmp. Do not create an empty utmp file, change permissions, or suppress the warning as a speculative login fix. [Debian bug 1087449](https://bugs.debian.org/1087449).

## Diagnostic change committed

Commit `b979c6b7505670d41cd6342d19e86ebe850e443e` adds a live-only session trace wrapper at `image/live-owner/usr/lib/orez/orez-session-trace`. The OREZ session entry now calls that wrapper, which then invokes the exact original native command:

```sh
/usr/lib/x86_64-linux-gnu/libexec/plasma-dbus-run-session-if-needed /usr/bin/startplasma-wayland
```

It records a start marker, a small allowlisted set of non-secret environment facts, and the exact child exit status through the system journal. It does not dump the environment, passwords, command-line credentials, personal files, or process memory. It returns the child's exact status. It does not bypass PAM, enable automatic login, change user privileges, relax AppArmor, change compositor settings, or choose another desktop. The instrumentation remains live-only and is excluded from the normal installed package allowlist.

CI run [42211534711](https://github.com/RezoxNemesis/OREZ-OS/actions/runs/42211534711) passed **225 source tests, the 38-path Debian package audit, and 68 desktop/mobile preview tests**. The full ISO job was skipped; this validates source and packaging checks, not a rebuilt or booted diagnostic ISO. Evidence artifact: `13499580862`, 211,801,054 bytes, expires 20 November 2026.

## Next evidence required

1. Build a new ISO from the reviewed base, native-app layer, dpkg-owned OREZ layer and updated live-owner layer. Record its exact source commit and SHA-256. The existing manual full-image workflow is not yet wired to prepare all three inputs, so do not re-trigger it expecting missing inputs to appear.
2. Boot that exact ISO from the ordinary default UEFI menu in a disposable, offline, diskless VM with disposable credentials. Do not edit kernel flags.
3. Inspect the journal for `orez-session-trace: wrapper_started`, `starting plasma-dbus-run-session-if-needed`, and `plasma_session_child_exit=N`. If the wrapper-start marker is absent, investigate SDDM's configured `SessionCommand` / `/etc/sddm/wayland-session` boundary. If present, the returned status narrows the failure to the native helper/startplasma chain; inspect its corresponding process tree and stderr log.
4. Preserve a matched control boot and capture non-secret values only: HOME, PATH, locale, XDG_RUNTIME_DIR, whether DBUS_SESSION_BUS_ADDRESS is set, WAYLAND_DISPLAY, DISPLAY, XDG_SESSION_TYPE, XDG_CURRENT_DESKTOP, and user-manager readiness.
5. Investigate the compositor's process lifetime and exact crash/exit evidence separately. A greeter compositor stopping after greeter shutdown is not proof that the user's compositor failed.
6. Change one justified variable at a time. Preserve authentication, locked root, owner privilege boundaries and session selection. Do not turn errors into success or use automatic login.
7. Require a new default-menu UEFI boot to show authentication, usable desktop, keyboard/mouse input, launcher, Settings, Dolphin, terminal, logout and a second successful login. Record ISO hash, journal, screenshots and command exit chain.

## Release gate

Normal graphical login remains **BLOCKED****. Installer activation, ISO publication and real-PC installation remain prohibited until the login passes and the independent installer, disk-safety, encryption, update/recovery, licensing and target-hardware gates are completed.
