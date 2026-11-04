# OREZ OS — unresolved blockers

1. **Do not install on the real SSD.** The upstream Kubuntu installer is not customized/tested and may not install OREZ's live SquashFS overlay; no restore procedure exists yet.
2. Initial ISO creation and direct-kernel casper VM boot passed. Still missing: OVMF/UEFI boot, graphical Plasma session, Secure Boot, NVIDIA/Wi-Fi/Realme actual hardware tests.
3. The 5+ GB image was ephemeral in a GitHub job and was **not uploaded**. Public image redistribution must respect upstream licences/marks and verified release signatures.
4. LUKS2 encryption, Btrfs/Snapper root rollbacks, Restic backups, signed package repository and installation cancellation tests do not exist yet.
5. KDE Connect must be confirmed in the ISO's installed package inventory; Android pairing and transfer have not been verified.
6. AI capability broker and local model services are deliberately absent until threat-reviewed.

7. OVMF evidence [run 41811624570](https://github.com/RezoxNemesis/OREZ-OS/actions/runs/41811624570) reaches TianoCore/GRUB and Kubuntu boot splash, but NOT verified graphical OREZ/KDE session. Serial output contains `error: can't find command grub_platform`; investigate whether upstream or remixed boot configuration caused this. This may be non-fatal but must be qualified rather than ignored.
8. Linux vendor splash and GRUB show upstream Kubuntu branding; OREZ boot/login experience still needs packaging and testing. Do not mistake wallpaper SVG for complete desktop design.

9. **Installer hardening (reported upstream):** [LP #2172113](https://bugs.launchpad.net/bugs/2172113) live-only AppArmor sysctl override may persist on Kubuntu 26.04.1 installed system. **Release blocker** until removed/qualified and effective policy tested.
10. **Encrypted installation (reported upstream):** [LP #2172138](https://bugs.launchpad.net/bugs/2172138) Calamares LUKS2 crypttab omission may cause an unbootable encrypted install. **Release blocker** until tested encrypted installation, unlock and rollback pass in disposable virtual machines.

11. [Run 41816102051](https://github.com/RezoxNemesis/OREZ-OS/actions/runs/41816102051): stricter direct-kernel graphical gate failed although the OREZ live filesystem was present. The screenshot is black; serial reached login prompts but did not prove KDE graphical.target/display manager. Cause is **unverified** (the serial-console test kernel parameters are a candidate). Neither firmware/desktop readiness nor USB install is qualified.
