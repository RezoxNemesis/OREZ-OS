# OREZ live-owner setup and login

This live-only component creates no remote-access service and is excluded from
the normal desktop package and installed-system payload. It is a candidate,
not proof of a working boot or complete host security.

On a nonpersistent live boot, casper creates the temporary owner account with
its password locked. The OREZ console setup asks you to choose and repeat a
12–128 character password without echo. This password is for this volatile live
session only: login, screen unlock and administrator prompts. It does not modify
your SSD or save a password on the USB. Direct root login stays locked. Choose a
separate password during a later qualified installation.

SDDM cannot start until the setup service succeeds. Cancel/mismatch/system error
leaves the desktop blocked; reboot to retry. No default/bypass password exists.
The root service runs once on the local console, has no network, and exits after
setup. Passwords are not written to logs or command-line arguments. Python and
the system PAM/password utility handle secret memory; guaranteed memory erasure
is not claimed. No owner password is used in automated test evidence.

Controls and diagnostics:

- Login: the OREZ Paper SDDM theme uses the normal local SDDM/PAM backend.
- Status: `systemctl status orez-owner-setup.service` and
  `systemctl status sddm.service`; logs identify startup/failure, never passwords.
- Live owner name: `/var/lib/orez-live/owner-required` before setup; private
  root-owned `/run/orez-live/owner-ready.json` after setup (no credential hash).
- Change your live password after login with the standard `passwd` command.
- Login appearance: System Settings → Login Screen (administrator authentication).
  Theme configuration is `/usr/share/sddm/themes/orez/theme.conf`; supported
  administrator override `theme.conf.user` can enable `SolidPanel=true` or choose
  another wallpaper. This theme adds no remote content or account provider.
- Initial sudo policy: `/etc/sudoers.d/orez-live-owner` sets no cached sudo
  authentication for the sudo group. No passwordless command grant is created.
  The owner can inspect effective privileges with `sudo -l` after authentication.
- Stop/reset: reboot the nonpersistent live session. This discards its temporary
  password and settings. Persistent live media is deliberately unsupported by
  this enrollment flow; do not use it for retained sensitive data.

This setup cannot identify who physically holds the keyboard at first boot.
Use verified media and keep physical control of initial setup. It does not replace
Secure Boot, full-disk encryption, AppArmor, application isolation, authenticated
updates, recovery or physical-hardware testing. UI screenshots from SDDM test mode
are not proof of an authenticated login or a full OREZ desktop session.
