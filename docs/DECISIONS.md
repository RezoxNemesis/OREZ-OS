# OREZ OS architecture decisions

- ADR-001 (2026-11-04): Kubuntu 26.04.1 LTS + KDE Plasma 6 selected for stable drivers, software, desktop and security foundation.
- ADR-002 (2026-11-04): Signed-checksum-verified upstream ISO + small original SquashFS overlay for fast initial live proof. Installer persistence requires separate qualification.
- ADR-003 (2026-11-04): AI privileges/remote command absent until typed least-privilege broker and user consent are independently tested.
- ADR-004 (2026-11-04): KDE Connect provides Android pairing and encrypted local file communication; no homemade cryptographic protocol.
- ADR-005 (2026-11-04): No public modified ISO distribution before redistribution rights, integrity and capacity are resolved.
- ADR-006 (2026-11-04): GitHub docs, source commit, CI and hardware logs are the authority for cross-chat continuity.

- ADR-007 (2026-11-04): Keep an independent install-only `orez-install.squashfs` with a reviewed file allowlist, instead of installing live-only Calamares stubs, verification services or diagnostic grants into an installed root. Stage an *inactive* Calamares `unpackfs` two-source profile for later disposable-disk validation. Exclude the known live AppArmor override from the candidate first-source copy. Do not activate installation without actual rollback, encryption, data-preservation and target-device tests.
