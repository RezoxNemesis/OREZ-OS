# Blueprint requirements-to-evidence map

| Requirement | Implementation | Evidence / blocker |
|---|---|---|
| Real Linux ISO | `build/build-live.sh` | Full image construction/static check passed CI 41809241570 |
| Live root boots | `build/test-casper-vm.sh` | QEMU casper overlay proof passed 41810060479 |
| UEFI/Plasma UI | Kubuntu boot and KDE overlay | Still untested with OVMF/screenshot |
| Japanese paper desktop | OREZ SVG and first-login setup | SVG parsed; in-guest appearance not certified |
| User-changeable settings | `orezctl appearance`, KDE Settings | Source tests; live KDE GUI pending |
| Android phone integration | KDE Connect CLI/GUI | Source interface; physical pairing not tested |
| AI safety | No privileged AI runtime shipped | Source absence checked; full broker not implemented |
| Malware security / firewall | Ubuntu/KDE foundation | Default effective protections need verification |
| Installer/backup/recovery | Not implemented | Disposable disk, BitLocker, encryption, rollback checks required |
| Hardware/NVIDIA | Read-only `orezctl hardware` | MSI/RTX 3050 real device test required |
| Cross-chat project memory | `docs/AI_HANDOFF.md` | Update only after verifying commits and evidence |
