# OREZ OS security — defence in depth

**Security is a release gate, not an absolute immunity guarantee.** Upstream Ubuntu/KDE updates, AppArmor, authenticated packages, least privilege, firewall, no auto-run, backups, signed releases, and user-controlled settings are required.

**Implemented in 0.1:** genuine upstream signed-image verification; no OREZ network listener, hidden root access, remote command runner or AI privileged broker; user-controlled one-time wallpaper; native read-only status; opt-in unprivileged VM-only boot verification (see BOOT_VERIFICATION.md). KDE Connect uses established pairing, never untrusted automatic remote commands.

**Not yet implemented:** audited OREZ package signing and update server, LUKS2/Snapper/Restic restore drills, default firewall profile, USBGuard, comprehensive sandbox/security center, safe installer and NVIDIA/Secure Boot hardening.

**Mandatory AI trust boundary:** an AI model, prompt, browser page or MCP tool response is untrusted and cannot authorize privileged effects. Future actions require independent typed broker, narrow grants, trusted visible exact-parameter approval, administrator authentication as needed, logs, revocation and emergency stop. No raw privileged shell or invisible system automation.

**User control:** security-related settings must be discoverable; privileged changes may require admin authentication but cannot be hidden. Rollback and recovery must be documented before modifications.
