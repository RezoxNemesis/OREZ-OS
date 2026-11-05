# OREZ OS architecture decisions

## 2026-11-05 — owner assets, Android, resources and environment

- Adopt original user-provided Rest JPEG as initial wallpaper and Horizon as an
  alternative. Keep existing user choices; do not force a wallpaper on upgrades.
- Build an opt-in normal-user Android manager with memory admission checks and
  explicit lifecycle/reset controls. Google SDK is for permitted development/
  testing; consumer Play Store support requires a separately qualified provider.
- Keep public repository until full PC-readiness, then make private per owner
  instruction. Restrict development authority to owner; actual access audit
  remains incomplete due connector/browser limits.
- Favor measured efficiency over unverified tuning. No firmware unlocks,
  blanket security removal, periodic cache purging or forced maximum clocks.
- Correct historical low-memory wording: rootless Docker cgroup enforcement is
  absent. Native test passes remain valid component results, not RAM ceilings.
- Add reusable QA dependency definition; host KVM/GPU/sandbox/network permissions
  cannot be created by adding packages. No automatic environment publication.

- ADR-009 (2026-11-05): Implement phone-first exploration as a clearly labelled responsive React preview with a portable HTML export and optional HTTPS PWA. Do not replace Android or connect browser code to native permissions. Pairing and installer views remain demonstrative/blocked until real implementations are qualified.
- ADR-010 (2026-11-05): Every test run retains screenshots, output, source identity and failure evidence. Native Xvfb windows, browser views and VM framebuffers are separate evidence classes. Use manual-only Ubuntu container tests for APT ownership/reinstall/removal while VM graphics remain blocked; this cannot qualify Calamares or hardware.
- ADR-011 (2026-11-05): Align the blueprint with the repository's existing owner-reserved original-source/artwork policy. An explicit original-code licence and component obligations are release prerequisites; a public repository is not a licence grant.
- ADR-012 (2026-11-05): Builders stage explicit root-owned 0755 directories/commands and 0644 data instead of inheriting checkout permissions. Package mode/owner checks and ordinary-user execution are required acceptance gates. A source file-list pass alone is insufficient.

- ADR-001 (2026-11-04): Kubuntu 26.04.1 LTS + KDE Plasma 6 selected for stable drivers, software, desktop and security foundation.
- ADR-002 (2026-11-04): Signed-checksum-verified upstream ISO + small original SquashFS overlay for fast initial live proof. Installer persistence requires separate qualification.
- ADR-003 (2026-11-04): AI privileges/remote command absent until typed least-privilege broker and user consent are independently tested.
- ADR-004 (2026-11-04): KDE Connect provides Android pairing and encrypted local file communication; no homemade cryptographic protocol.
- ADR-005 (2026-11-04): No public modified ISO distribution before redistribution rights, integrity and capacity are resolved.
- ADR-006 (2026-11-04): GitHub docs, source commit, CI and hardware logs are the authority for cross-chat continuity.

- ADR-007 (2026-11-04): Keep an independent install-only `orez-install.squashfs` with a reviewed file allowlist, instead of installing live-only Calamares stubs, verification services or diagnostic grants into an installed root. Stage an *inactive* Calamares `unpackfs` two-source profile for later disposable-disk validation. Exclude the known live AppArmor override from the candidate first-source copy. Do not activate installation without actual rollback, encryption, data-preservation and target-device tests.

- ADR-008 (2026-11-04): Because default KWin Wayland on CPU-only QEMU with standard VGA and VirtIO 2D can report running Plasma but still produce black framebuffer, test an explicitly gated `KWIN_COMPOSE=Q` software backend **only** under the QEMU-provided `orez.verify=1` kernel argument. This is a diagnostic, not a default OS policy; do not include the script in installed packages or enable it on the physical PC.
