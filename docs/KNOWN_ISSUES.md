# OREZ OS — unresolved blockers

## Current diagnostic and installer preparation — 6 November 2026

The fifth integrated UEFI run (qa12-02, old e9d423a image) stopped owner setup
because Plymouth did not exit within its 20-second observation window. No
password was read. The new 1d68fccb image permits up to 120 seconds, reports
progress, preserves cancellation and still fails closed. Static checks pass;
the longer wait itself has not been qualified by a default boot.

A sixth diskless/offline boot (qa12-08) is in progress with the cosmetic splash
disabled and the existing test-only QPainter flag. Its result is pending, not a
normal-boot, performance or installation pass. Final result belongs in AI_HANDOFF.

Actual inspection of 30 source configurations and an offline APT simulation now
support an [inactive installer profile](INSTALLER_PROFILE.md). Only eight exact
installer/live packages would be removed; the 2,301-package dependency graph
remains consistent. Maintainer scripts, actual installation and reboot remain
untested. Original installer branding and installed OREZ login-theme packaging
still need integration. The full image CI job still lacks prepared layer inputs.

## Integrated ISO and actual owner boot — 6 November 2026

A new 5.46 GB integrated ISO passes exact-base, native-app, dpkg ownership,
owner payload and media checks. The first two actual UEFI runs exposed the
initial enrollment password. The current correction waits for Plymouth's actual
process exit and refuses visible-input fallback. Third boot: both entries hidden,
setup completes, tty2 owner authentication works and passwordless sudo is refused.
185 source tests pass. One cold-boot observation does not certify all timings.

Third-run SDDM/PAM graphical authentication succeeded and Plasma started, but
the actual desktop remained black. Guest logs include a missing render node,
software graphics errors and a splash timeout; root cause is unqualified.
The fourth software-VirGL boot completed owner setup and tty2 authentication,
but no usable desktop. QMP contention ended run three and scrot timeout ended
run four through harness cleanup, not demonstrated kernel crashes. Both capture
failures are retained; error handling was corrected with 187 local source tests.
No further boot validates the last capture-only correction. Native applications
are integrated but not workload-tested inside the booted current image.
See [LIVE_ASSEMBLY.md](LIVE_ASSEMBLY.md) and the latest handoff/evidence ledger.
Installer, recovery, current security baseline, redistribution/signing and
physical hardware qualification remain open. These results supersede older
“not assembled” and “no visible login” entries; historical failures remain.



## Image applications checkpoint — 6 November 2026

- CI timeout corrected: first run finished its checks but exceeded the 12-minute
  deadline after slow HTTP-mirror font downloads. An 18-minute bounded job now
  passes in run 42140670101. The conditional HTTPS rewrite of standard source
  files did not affect the hosted runner's indirect mirror list; its actual
  transport remains Azure HTTP with APT signature validation. Do not claim that
  the faster rerun proved a mirror optimization. Pinned Actions still
  emit the platform Node 20 deprecation warning while being forced onto Node 24;
  review newer official Action pins in a separate maintenance change.

- Native browser/player/game/Qt dependencies are now genuinely installed in the
  extracted ISO base and packed as a verified additive layer. The production
  builder still needs exact-base binding, correct layer ordering/manifests,
  current owner initrd/payload assembly and renewed media checksums. No new full
  ISO, authenticated graphical boot or safe installer is established.
- The isolated chroot cannot load AppArmor or qualify normal Brave wrapper/
  sandbox launch; SuperTux needs its documented explicit data directory there.
  Version output is not playback/gameplay. Qt screenshots are offscreen
  components using the actual installed dependencies, not the booted desktop.
- 32 GiB storage is inadequate for retaining multiple full ISO/staged/VM images.
  Only the checksum-verified superseded cache-only development ISO was removed
  this turn; its reports/checksum remain. The original older ISO is retained and
  predates owner-policy hardening. Neither artifact is an installation release.
- Package versions/index hashes are retained, but snapshot repositories, complete
  source/licence inventory, signed releases and current base security-update
  qualification remain open. See [IMAGE_APPLICATIONS.md](IMAGE_APPLICATIONS.md).

Latest owner scope (5 November 2026): **finish the first PC release before Android emulation.** Native Brave/VLC/Linux games, explicitly authorized web YouTube, owner login, OREZ Calendar/Reuz, themes, AI permissions and connectivity take priority. See [FIRST_PC_RELEASE.md](FIRST_PC_RELEASE.md) for implementation, test limits and blocking gates. No installable release is approved. This supersedes older Android-first and web-YouTube-prohibited statements for the first release only.

## Offline startup follow-up — 5 November 2026, latest

- The actual initrd cache hook left legacy Internet repositories active. A pinned
  one-hook repack now selects local CD sources only, preserves authentication
  checks and bounds optional cache generation. Rootless authenticated local APT
  and independent initrd extraction pass. The new 5,070,782,464-byte derivative
  ISO passes static checks; both original and derivative hashes are recorded.
- The actual 600-second offline/diskless VM passes that cache stage with a
  warning/fallback and reaches systemd. It still does not show a usable desktop:
  last serial jobs include `ldconfig.service` and `snapd.apparmor.service`, while
  graphical captures retain the firmware text. Capture success is not desktop
  acceptance. No UEFI or hardware qualification follows from this direct boot.
- Actual initrd audit confirms **three owner-control blockers**: blank live-user
  password, passwordless full sudo and wildcard Polkit grants. The cache fix
  changes none of these. A reviewed owner setup/authentication flow and effective
  runtime allow/deny tests are still required before sensitive live use.
- See [offline startup evidence](OFFLINE_BOOT_QA.md) and the latest AI_HANDOFF.md.
  Keep AppArmor enabled; investigate service timing on a supported KVM/GPU host
  instead of disabling protections or repeating identical TCG boots.

## Earlier live boot follow-up — 5 November 2026

- A new 5,073,338,368-byte ISO was built and its static structure/installer guard
  passed. Software-backed VirGL starts as a normal user, but live desktop
  qualification remains blocked. Corrected pristine control qa5-12 did not reach
  Try/Plasma within 600 seconds and logged offline APT/DNS retries. OREZ UEFI
  qa5-13 reached firmware/GRUB, then black frames; SDL capture timed out around
  390 seconds. No root cause for the missing desktop is established. See
  [VM graphics evidence](VM_GRAPHICS_QA.md). Do not repeat identical probes blindly.
- **Live privilege-policy gate:** the actual upstream base contains casper's
  `25adduser` hook writing `NOPASSWD: ALL` for the live user. This is a static
  source finding (qa5-18), not a tested effective runtime policy. Audit the actual
  initrd and all live sudo/Polkit grants, then implement owner-authenticated
  elevation before qualifying sensitive live use. The Calamares blocker does
  not enforce owner-only administrator access. OREZ has added no such grant.
- The GRUB `grub_platform` warning is now attributed: qa5-14 finds byte-identical
  configurations in both actual ISOs with the stray bare command at line 23.
  Address it in the reviewed OREZ boot-menu work; it does not prove the cause of
  missing graphics. No firmware signature was modified in this session.
- QEMU GUI/OpenGL modules are now explicit QA recipe dependencies. The existing
  compact image needs rebuilding to include them; the test lab installed them
  temporarily. Host KVM, physical GPU and enforced Docker cgroups remain absent.

## Native follow-up — 5 November 2026

Native network/Bluetooth open-close, Settings search/clear and the dummy-password
mask/reveal/re-mask/clear/cancel lifecycle now pass (qa4-29). Actual package
0.1.0-1 → 0.1.0-2 upgrade and ten APT failure/recovery cases pass. SuperTux reaches
a playable scene with observed movement/death response (qa4-27). These close
component gates only. See [follow-up evidence](CONTINUED_QA.md).

## Daily-use blockers — 5 November 2026

- Consumer Play Store runtime/licensing, guest boot and Android game/YouTube
  downloads remain unqualified. Only the development manager exists in source.
- Brave is installed but its required sandbox cannot create namespaces here.
  YouTube separately returns a proxy 403; do not weaken policy to force a pass.
- Rootless Docker lacks cgroup enforcement. No 2/4/6 GiB performance proof;
  visible counters belong to the shared environment. No KVM/GPU access.
- 32 GiB storage and Docker's VFS copies constrain tests. Publish on a supported
  host with at least 80 GiB. Dependency images can be rebuilt from recorded files.
- Owner is verified repository admin; collaborator/deploy-key/app access audit
  is incomplete. No access settings or visibility have been changed.
- The expanded 23-path collision gate now passes against the actual pinned
  Kubuntu image (run 42014023573). Actual installation, encryption and recovery
  remain unqualified; do not treat this static audit as permission to install.
- VLC passed software playback with a virtual audio sink; physical speakers,
  PipeWire, GPU decoding and long-duration frame-drop targets remain untested.


## Current additions — 5 November 2026

- The successful latest CI warns that pinned checkout/setup-node/upload-artifact actions target deprecated Node 20 and are being run on Node 24 by GitHub. Follow up with verified upstream action updates and full validation; this run passed, but the pins need maintenance.

- Expanded QA now has a visible native KWin/Plasma container desktop, application windows, real launcher input and window/workspace interaction. This does not resolve the earlier ISO/UEFI black-frame gate. Full results and failure history: [QA scenarios](QA_SCENARIOS.md).
- The desktop fixture lacks a full system bus/login stack, portals, PipeWire audio and hardware devices. Logs report those omissions; successful Settings rendering does not prove administrator dialogs, sound, capture or device settings work. Qt also warns about an unsupported SVG child in the wallpaper; final paper texture/rendering and native accessibility/contrast need design qualification.
- Preview update handling no longer accesses sessionStorage after the blocked-storage regression. All 60 desktop/mobile browser cases now pass locally, including offline operation, actual consented worker updates and automated accessibility checks. This is not physical Android validation.

- An actual ordinary-user package test found inaccessible commands when builders inherited a restrictive checkout umask. Explicit payload staging and stricter archive mode/owner validation fix the source; 52 regression tests pass. Full ISO boot with the changed staging path is still untested. This does not establish the cause of prior CI black frames, where checkout permissions differed.

- Browser preview is interactive but separate from native Plasma. Real Android browser/PWA installation and touch/accessibility-device testing are pending. The portable HTML requires a browser capable of running local JavaScript; a file viewer may not work.
- Package tests use a minimal Ubuntu dependency container with networking disabled. It has no kernel boot or physical GPU. Its default documentation exclusions initially removed two OREZ files; the desktop test fixture includes OREZ docs explicitly. Move runtime welcome HTML out of `/usr/share/doc` before supporting minimized hosts, and repeat the upstream path-collision audit when its path changes.
- Ten real APT transition/failure cases now pass using local synthetic versions, including explicit package rollback and user-data retention. Signed repository updates, distro upgrades, encrypted system rollback, Calamares, Secure Boot, GPU graphics and real phone pairing remain unqualified.
- Source screenshots and logs retained by Actions expire after 14 days; older ISO evidence expires after two days. The tracked ledger is durable but does not replace the original downloadable evidence bundle.
- Original-code licensing remains owner-reserved; public binary release obligations and long-term security maintenance are still unresolved.

## Historical blocker ledger (read latest handoff first)

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

22. [Pristine Kubuntu run 41887435151](https://github.com/RezoxNemesis/OREZ-OS/actions/runs/41887435151) produced no meaningful graphics comparison: the test incorrectly depended on `kubuntu-installer-prompt` appearing in serial output, but pristine Kubuntu has no OREZ GUI diagnostic unit that writes that marker. The safe Try action was never attempted. Corrected to use pinned framebuffer pixels without serial dependency; CI and guest rerun needed before drawing any upstream conclusion.

23. Pristine Kubuntu checksum-verified control [41889832695](https://github.com/RezoxNemesis/OREZ-OS/actions/runs/41889832695) safely clicked Try but **also** produced two fully black VirtIO 2D frames. CPU-only QEMU cannot currently qualify KDE visuals for either Kubuntu or OREZ; avoid more identical tests without an accelerated control. Physical GPU remains untested.
24. Install-only OREZ layer has zero file-path collisions with authentic Kubuntu 26.04.1 (16 whitelisted files, [41937702881](https://github.com/RezoxNemesis/OREZ-OS/actions/runs/41937702881)), and native `.deb` has exactly 16 allowed files and no maintainer scripts ([41938238699](https://github.com/RezoxNemesis/OREZ-OS/actions/runs/41938238699)). Neither test proves actual installation, signed update ownership, encryption or rollback.

Owner update/monitor requirement: signed OREZ channel, owner-policy migration
guards and local security detection are not implemented. Follow UPDATES_AND_GUARD.md;
do not present existing read-only status as protection against all attacks.

## Store integration (5 November 2026)

- Android YouTube/Instagram/games have not run; catalog and mocked ADB tests do
  not establish a consumer emulator, Play Store or game/input compatibility.
- Official Linux apps are preferred without modification. Automatic Android game presets are approved but unimplemented.
  Touch-only controls require real preset qualification before claiming support.
- `orez-shell` 0.1.0-3 requires `python3-pyside6.qtwidgets`. The pinned base and
  retained ISOs lack this dependency/the new Store; image provisioning and new
  live/installed-root checks are pending.
- Native Brave is installed in the QA container but its Chromium sandbox cannot
  create required namespaces here. Do not disable it to force a pass. No new
  successful Brave browsing claim follows from this session.
- Native packages run as the ordinary user and may read user-owned files; no
  blanket data isolation is implemented by Store launch. Live auth blockers
  remain unchanged. See OREZ_STORE.md and the latest AI_HANDOFF.md.
