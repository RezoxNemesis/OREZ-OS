# OREZ 0.1 — transparent controls

The OS foundation uses native KDE System Settings and standard Linux security. These are real local commands, not an Android simulation.

- `orezctl settings`: open KDE System Settings.
- `orezctl appearance status|disable|enable`: control **only** the optional OREZ first-login wallpaper from your own account; also visible in KDE Autostart. Disabling leaves the current wallpaper alone.
- `orezctl connect open`: opens the standard KDE Connect pairing GUI if installed. Users explicitly pair and revoke their Android phone; no silent remote-command access.
- `orezctl connect devices`: lists currently visible/paired devices; does not pair or send files itself.
- `orezctl security`: read-only AppArmor and Secure Boot summary; **not** a security certification.
- `orezctl ai`: AI remains disabled until a reviewed permissions system exists.
- `orezctl hardware`: read-only CPU, GPU and storage inventory.

The opt-in VM boot verification service is separately documented in BOOT_VERIFICATION.md and only activates with a test kernel parameter. **No hidden administrator or AI controls are present in 0.1.**

- Read-only target PC preflight: `orezctl preflight` or OREZ Hardware Preflight in the KDE launcher; never changes disks or firmware. Does not certify boot, encryption, graphics drivers or installation.
