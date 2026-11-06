# OREZ graphical login blocker — investigation record

Status: 6 November 2026. **Open blocker. No fix is claimed.**

## Facts established by the current default-menu UEFI run

Image SHA-256: `6ca85cf37d48beeb8ac0fd6ffa99e94cc9806949584a970916024ddf30d80ac6`.

- Local owner enrollment completed; both password entries were concealed in the observed run.
- SDDM selected `/usr/share/orez/wayland-sessions/orez.desktop`.
- PAM authentication succeeded and opened the owner session.
- SDDM logged `Session started true`, then `sddm-helper exited with 64`; the greeter restarted.
- The session log was empty. The journal also reported `Failed to write utmpx: No such file or directory`.
- A separate manual launch of `startplasma-wayland` from an authenticated ordinary-owner TTY rendered real Plasma Welcome, wallpaper, panel, tray and Settings. This was not the normal SDDM route.

See `docs/evidence/2026-11-06-installer-graphics/qa12-17-vm-result.json`,
`guest-journal-excerpt.json`, `startup-source-review.json` and
`LIVE_ASSEMBLY.md`.

## What the evidence does not establish

Exit status 64 is not, by itself, proof of a GPU failure. The reviewed upstream
SDDM helper statuses do not make it a generic graphics error. The reviewed
upstream Plasma launcher did not show an explicit 64 return path. This does not
exclude downstream patches, an environment-dependent branch, a child process,
a wrapper, or an early process termination.

The missing utmpx warning is correlated in time, but no evidence proves it
caused the session to exit. Do not create an empty utmp file or suppress the
warning as a speculative fix.

The separate TTY launch proves that some native Plasma components can render
under the VM's software graphics path. It does not prove that the SDDM-launched
environment is equivalent.

## Required next investigation

1. Rebuild or retrieve an ISO whose embedded source identity is recorded. Boot it
   from the ordinary default UEFI menu with no changed kernel flags, no writable
   guest disks, no network and disposable credentials.
2. Capture the exact SDDM-selected desktop file, its resolved executable and
   symlink target, `/etc/sddm/wayland-session`, the Plasma wrapper, package
   versions and relevant systemd/PAM environment. Record hashes and modes.
3. Capture the child process tree and exact exit origin around
   `plasma-dbus-run-session-if-needed`, `dbus-run-session` and
   `startplasma-wayland`. If using tracing, preserve an untraced control run
   because tracing may change timing.
4. Compare only non-secret environment variables between the SDDM session and
   the successful ordinary-owner TTY diagnostic: HOME, PATH, locale,
   XDG_RUNTIME_DIR, DBUS_SESSION_BUS_ADDRESS, WAYLAND_DISPLAY, session type,
   systemd user-manager readiness and runtime directory ownership/mode.
5. Investigate the utmpx warning independently: verify the expected runtime
   directory and package-provided creation mechanism in the actual live root.
   Do not add a guessed file or change ownership/modes without a proven package
   requirement and a regression test.
6. Change one variable at a time. Preserve PAM authentication, the local
   password, root lock, owner privilege boundaries and SDDM session selection.
   Never hide the failure by forcing a success exit, enabling automatic login,
   removing authentication, or falling back silently to a different desktop.
7. Require a new ordinary default-menu UEFI boot to show: successful
   authentication, a usable Plasma desktop, keyboard/mouse input, launcher,
   Settings, Dolphin, terminal, logout and a second successful login. Record
   actual screenshots, journal, command exit chain and ISO hash.
8. Only then update the blocker status. A source test, manually launched TTY
   desktop, screenshot from a container, or successful ISO assembly is not a
   graphical-login pass.

## Release gate

Normal graphical login remains **BLOCKED** until the above default-boot test
passes. Installer activation, ISO publication and real-PC installation remain
prohibited independently of this login work.
