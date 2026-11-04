# OREZ OS — Installation and Recovery (development hold)

**DO NOT INSTALL THE CURRENT DEVELOPMENT ISO ON YOUR REAL SSD.** This is a Linux live-boot candidate, not a qualified installer. Upstream Kubuntu's install button may be present, but it has not been adapted to persist OREZ components. No safe USB-installable OREZ release is published yet.

## Required qualification sequence
1. Build a verified ISO from pinned, signed Kubuntu sources. Record exact SHA-256, source commit and licence provenance.
2. Confirm EFI boot, Linux live root, graphical Plasma desktop and correct wallpaper under disposable virtual firmware.
3. Validate that a Calamares installation copies the OREZ desktop and package-management state into the installed system (not merely the live overlay).
4. Exercise plain and LUKS2+Btrfs installations **only onto disposable virtual disks**; verify preflight disk summary, explicit confirmation, cancel before writes and non-target disk preservation.
5. Run `python3 build/audit-installed-root.py --root /path/to/mounted/vm-root --expect-btrfs --expect-encryption --strict` against the **offline VM root**. Any failure blocks release. The static result can never certify a system by itself.
6. Test repeated boots, Secure Boot as a separate qualified path, actual NVIDIA/Wayland operation, Wi-Fi/Bluetooth, keyboard, mouse and NVMe read-only detection on the target MSI board.
7. Cause and recover from interrupted package updates, graphics-driver rollback and restore from an independently checked backup. Verify root snapshots do not roll back revocations or erase user files.
8. Publish only after signed source/release metadata and image-redistribution permissions are reviewed.

## Known reported upstream issues
- https://bugs.launchpad.net/bugs/2172113 — reported AppArmor user-namespace restriction disabled by a live-only config carried into installed Kubuntu.
- https://bugs.launchpad.net/bugs/2172138 — reported encrypted Calamares install missing `luks` option in crypttab, leading to an unlock/boot failure.

Do not assume either bug is resolved without updated tests. Do not patch settings silently; owner-visible, documented configuration and rollback are mandatory.

## Owner data and USB safety
The Windows 11 installation/recovery USB is reserved and must not be overwritten. Only a separate, clearly identified USB drive may eventually be written with the verified OREZ ISO. In the installer, no SSD erase target is preselected; Windows/BitLocker/EFI partitions must be identified and preserved unless the user explicitly approves a destructive plan. Never make an AI prompt or remembered setting sufficient authorization to erase storage.

## Source-only synthetic installer replay
Source suite test_install_manifest_replay.py validates the inactive two-stage Calamares candidate and copies the installed OREZ file allowlist into a fresh temporary directory with a synthetic vendor baseline. It verifies a known live-only AppArmor override would block release and that the candidate's exclusion removes this synthetic problem. A passing source test **does not** qualify a real installed system, encryption, boot, update or recovery. See docs/INSTALLER_SYNTHETIC_TEST.md.

## File-level collision gate (development source)
`build/check-install-collisions.py` compares the contents listed from the **real base filesystem.squashfs** and the separate allowlisted `orez-install.squashfs`. Any preexisting base file with the same OREZ payload pathname, unexpected extra payload path, or missing allowlisted path blocks the image audit. Shared parent directories are permitted. The output is `INSTALL_LAYER_COLLISIONS.json`, and `installation_approved` always remains false. This is a read-only check, not a real install, a filesystem permission review or package-ownership verification.
