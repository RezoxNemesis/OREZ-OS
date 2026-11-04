# Blueprint requirements-to-evidence map

| Requirement | Implementation | Evidence / blocker |
|---|---|---|
| Real Linux ISO | `build/build-live.sh` | Full image construction/static check passed CI 41809241570 |
| Live root boots | `build/test-casper-vm.sh` | QEMU casper overlay proof passed 41810060479 |
| UEFI/Plasma UI | OVMF firmware screenshots and opt-in KDE process test | OVMF showed Kubuntu splash in run 41811624570; direct-kernel GUI gate FAILED run 41816102051; graphical UI NOT certified |
| Japanese paper desktop | OREZ SVG and first-login setup | SVG parsed; in-guest appearance not certified |
| User-changeable settings | `orezctl appearance`, KDE Settings | Source tests; live KDE GUI pending |
| Android phone integration | KDE Connect CLI/GUI | Source interface; physical pairing not tested |
| AI safety | No privileged AI runtime shipped | Source absence checked; full broker not implemented |
| Malware security / firewall | Ubuntu/KDE foundation | Default effective protections need verification |
| Installer/backup/recovery | Read-only installed-root audit and real ISO Calamares-source inspector implemented | Calamares installed-layer persistence, actual Btrfs/LUKS2 tests, backup restore and non-target disk safety NOT implemented; current ISO remains blocked |
| Hardware/NVIDIA | Read-only `orezctl hardware` | MSI/RTX 3050 real device test required |
| Cross-chat project memory | `docs/AI_HANDOFF.md` | Update only after verifying commits and evidence |
