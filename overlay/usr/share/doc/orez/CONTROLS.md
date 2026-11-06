# OREZ 0.1 — transparent controls

The OS foundation uses native KDE System Settings and standard Linux security. These are real local commands, not an Android simulation.

- `orezctl settings`: open KDE System Settings.
- `orezctl appearance status|disable|enable`: control **only** the optional OREZ first-login wallpaper from your own account; also visible in KDE Autostart. Disabling leaves the current wallpaper alone.
- `orezctl connect open`: opens the standard KDE Connect pairing GUI if installed. Users explicitly pair and revoke their Android phone; no silent remote-command access.
- `orezctl connect devices`: lists currently visible/paired devices; does not pair or send files itself.
- `orezctl security`: read-only AppArmor and Secure Boot summary; **not** a security certification.
- `orezctl ai`: AI remains disabled until a reviewed permissions system exists.
- `orezctl hardware`: read-only CPU, GPU and storage inventory.

- **OREZ Android Apps** in the launcher (`orez-android gui`): optional development/testing emulator manager, with status, setup prompts, start/stop, memory/graphics, logs and confirmed reset/removal. Google Play consumer compatibility is not yet qualified. No Android guest or Google credentials are included. Status is `orez-android status`; private managed storage is `~/.local/share/orez/android/`. Google/SDK services receive no host administrator identity. SDK use is subject to Google's development-use licence.
- **Wallpapers:** KDE System Settings → Wallpaper offers the owner's OREZ Rest (default for a new account) and OREZ Horizon images. Existing user choices are not automatically replaced. Source images are included unmodified at 1280×720; the display may scale/crop them according to the chosen fit mode.

The opt-in VM boot verification service is separately documented in BOOT_VERIFICATION.md and only activates with a test kernel parameter. **No hidden administrator or AI controls are present in 0.1.**

- Read-only target PC preflight: `orezctl preflight` or OREZ Hardware Preflight in the KDE launcher; never changes disks or firmware. Does not certify boot, encryption, graphics drivers or installation.

## Performance and power

`orezctl performance` reads available memory, CPU/memory/I/O pressure and the
current native power profile once. It changes nothing and starts no service.
`orezctl power` opens KDE Power Management. Adjust and restore supported power
settings there; availability depends on the platform. No clocks, firmware,
cache-purge policy or security settings are changed automatically.

## Network, Bluetooth and removable drives

`orezctl network` opens KDE connections; `orezctl bluetooth` opens pairing;
`orezctl files` opens Dolphin. `orezctl network-status` reads connection/device
state without saved passwords or network changes. These native modules must
be installed and need actual services/devices. Pair/connect/allow transfers
through their visible controls; forget networks and unpair devices there.
No automatic pairing, firewall opening, USB formatting or remote admin is added.

## OREZ Store

Launcher → OREZ Store or `orezctl store`. Search app names/categories, filter
Android/native formats, review privacy and launch existing native apps.
Official Linux desktop versions (including Brave and Chrome) are preferred
unchanged. YouTube, Instagram and the requested games are actual Android
app targets, not websites. Consumer runtime/download/playback is pending.
Direct keyboard/mouse support needs per-app verification.
Android runtime controls expose the existing development SDK manager after a
visible acknowledgement. They do not accept licences or install apps silently.
`orez-android app-status|open-app|store-page|app-settings --app youtube
--development-test` operates only on the owned, verified development emulator;
it cannot target the phone. Store-page opens a page inside Android Google Play,
leaving app installation/permissions to the user; no automatic purchase occurs.

Activity and controls shows local logs and explains update/removal locations.
Android app permissions, updates and removals belong inside the guest. Runtime
stop/reset/removal remain in OREZ Android Apps. No web fallback, root helper,
background store service, APK mirror or automatic purchases exist. GUI needs
`python3-pyside6.qtwidgets`; the existing live ISO does not yet include this new
Store or its GUI dependency. CLI list/status work without Qt bindings.

Native Linux apps run as the ordinary user and can access that user's files;
this is not filesystem isolation. Full live owner authentication and Android
isolation are still release blockers. Paid publisher features cannot be made
free by OREZ. Store logs: `~/.local/share/orez/store/`; Android state:
`~/.local/share/orez/android/`. No real account credentials are captured by tests.
