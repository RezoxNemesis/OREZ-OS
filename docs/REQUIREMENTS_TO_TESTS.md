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

### New evidence 2026-11-04
- ISO build/live-root: PASS in 41817833118, but full CI concluded failure because graphical gate is mandatory.
- UEFI/Plasma: FAIL to reach desktop in two screenshots; `display-manager` active, `graphical.target` not active during observed window. Cause unverified.
- Calamares: `unpackfs.conf` copies base SquashFS only. Persistence of OREZ overlay fails readiness. No real SSD installation allowed.
- AppArmor: live-only `kernel.apparmor_restrict_unprivileged_userns=0` present. Installed configuration and effective policy must be verified before release.
- Safety: unqualified Calamares live wrapper source/pkg tests PASS 41818841716, new ISO image test outstanding.

### Verified 2026-11-05 test evidence
- Authentic Kubuntu 26.04.1 checksum + **live VM graphical control**: the upstream distro also renders a completely black desktop after Try in this TCG/VirtIO environment (41889832695). OREZ-specific visual failure **not isolated**. Real target RTX 3050 and GUI remain unverified.
- Installed OREZ file allowlist: 16/16 present, zero path collisions with actual pinned Kubuntu root, zero extras (41937702881). **Static** only; does not run Calamares.
- Native Debian archive: 16/16 manifest files, no unexpected files, nonregular links or maintainer scripts (41938238699). **Not** installed or update-certified.
- Calamares execution and AppArmor/LUKS2/Btrfs/backup recovery: **STILL BLOCKED**.
