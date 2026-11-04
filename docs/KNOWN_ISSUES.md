# OREZ OS — unresolved blockers

1. **Do not install on the real SSD.** The upstream Kubuntu installer is not customized/tested and may not install OREZ's live SquashFS overlay; no restore procedure exists yet.
2. Initial ISO creation and direct-kernel casper VM boot passed. Still missing: OVMF/UEFI boot, graphical Plasma session, Secure Boot, NVIDIA/Wi-Fi/Realme actual hardware tests.
3. The 5+ GB image was ephemeral in a GitHub job and was **not uploaded**. Public image redistribution must respect upstream licences/marks and verified release signatures.
4. LUKS2 encryption, Btrfs/Snapper root rollbacks, Restic backups, signed package repository and installation cancellation tests do not exist yet.
5. KDE Connect must be confirmed in the ISO's installed package inventory; Android pairing and transfer have not been verified.
6. AI capability broker and local model services are deliberately absent until threat-reviewed.
