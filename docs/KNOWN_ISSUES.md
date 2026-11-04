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

12. The OREZ development ISO intentionally replaces the live Calamares entry point with a visible non-destructive blocker until installer safety is qualified. This live-only override is explicitly excluded from the separate .deb package. Other root-capable partitioning tools remain available; this guard is not absolute drive-write isolation.

13. **Installer source conclusively incomplete:** [run 41817833118](https://github.com/RezoxNemesis/OREZ-OS/actions/runs/41817833118) read `/etc/calamares/modules/unpackfs.conf` from the actual base SquashFS and found it copies **only** `/cdrom/casper/filesystem.squashfs`, excluding `zz-orez.squashfs`. An installation may therefore produce unbranded Kubuntu. Never run it until OREZ persistence is designed and tested.
14. **AppArmor hardening exposed:** the same ISO's `/etc/sysctl.d/20-apparmor.conf` sets `kernel.apparmor_restrict_unprivileged_userns = 0` for live sessions. Installed-system state remains unverified and release-blocked pending remediation and runtime testing.
15. **Graphical VM gate still fails:** the strict guest test did not prove `plasmashell`. `display-manager` reported active but `graphical.target` and `multi-user.target` inactive at timed checks. Long-running `snapd.service` seen; cause unknown. UEFI early + late screenshots both remained at Kubuntu splash. Do not identify VM-only graphics behavior with physical NVIDIA failure or success.
16. **Live-only Calamares guard** has passed native source/package tests in [run 41818841716](https://github.com/RezoxNemesis/OREZ-OS/actions/runs/41818841716); still must verify it in a rebuilt ISO. The .deb package deliberately excludes the override.

18. Visual-proof run 41854833186 correctly failed: KDE process active, but two delayed std-VGA screenshots after Try are still black except cursor. CI now rejects process-only success. Next VirtIO VGA comparison is test-only and requires independent proof.

19. [VirtIO retry run 41874348585](https://github.com/RezoxNemesis/OREZ-OS/actions/runs/41874348585): Try was successfully selected, KDE processes started, but TWO later framebuffer captures were completely black. M1 real desktop rendering **BLOCKED**, full job failed. The next test-only experiment conditionally tries KWin's QPainter compositor in the isolated VM without changing the installed OS or hardware graphics defaults; no results have been obtained yet.

20. [QPainter full run 41882928635](https://github.com/RezoxNemesis/OREZ-OS/actions/runs/41882928635): adding test-only `KWIN_COMPOSE=Q` did NOT resolve the VirtIO 2D black framebuffer. Both delayed screenshots were mathematically all-black. Boot/root, Try, Plasma processes passed; GUI visual and OVMF graphical gates remain blocked. Do not equate this VM failure with target NVIDIA hardware. Avoid blind reruns until an upstream baseline or better GPU-backed VM gives a control.

21. QPainter all-black QEMU evidence is inconclusive about root cause because no pristine upstream control was previously run. A one-shot **unchanged Kubuntu** control under the same headless VirtIO 2D/TCG device is now available and running as #41887435151. Its outcome must be inspected before drawing an upstream-versus-OREZ conclusion.
