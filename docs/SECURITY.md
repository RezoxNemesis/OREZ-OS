# OREZ OS security — defence in depth

## Owner control and Android boundary — 5 November 2026

OWNER_CONTROL.md defines the owner's sole human administration policy and the
still-incomplete GitHub collaborator/access audit. Repository visibility remains
public until the owner's PC-ready condition is met. Public readers do not gain
host administrator rights; later privacy cannot recall public copies.

The Android development manager never runs as root or grants groups/firmware
permissions. It rejects unsafe managed paths and foreign process identities;
reset/removal needs explicit confirmation. A guest is not a proven security
boundary until runtime socket, camera, microphone, clipboard, filesystem and
escape exposure have been tested. Unprivileged host execution alone is not
proof of sandbox isolation. Google login stays inside the guest; no credentials
are requested by OREZ. No Play certification/Integrity spoofing is planned.

Brave QA keeps its browser sandbox enabled. This workspace denies nested
namespace creation; record BLOCKED rather than disabling sandbox, seccomp or
AppArmor. TLS and APT signature verification remain enabled when provisioning.

**Security is a release gate, not an absolute immunity guarantee.** Upstream Ubuntu/KDE updates, AppArmor, authenticated packages, least privilege, firewall, no auto-run, backups, signed releases, and user-controlled settings are required.

**Implemented in 0.1:** genuine upstream signed-image verification; no OREZ network listener, hidden root access, remote command runner or AI privileged broker; user-controlled one-time wallpaper; native read-only status; opt-in unprivileged VM-only boot verification (see BOOT_VERIFICATION.md). KDE Connect uses established pairing, never untrusted automatic remote commands.

**Not yet implemented:** audited OREZ package signing and update server, LUKS2/Snapper/Restic restore drills, default firewall profile, USBGuard, comprehensive sandbox/security center, safe installer and NVIDIA/Secure Boot hardening.

**Mandatory AI trust boundary:** an AI model, prompt, browser page or MCP tool response is untrusted and cannot authorize privileged effects. Future actions require independent typed broker, narrow grants, trusted visible exact-parameter approval, administrator authentication as needed, logs, revocation and emergency stop. No raw privileged shell or invisible system automation.

**User control:** security-related settings must be discoverable; privileged changes may require admin authentication but cannot be hidden. Rollback and recovery must be documented before modifications.

## 2026-11-04: installer hardening blockers
- [Ubuntu bug #2172113](https://bugs.launchpad.net/bugs/2172113) reports Kubuntu 26.04.1 installs retaining a **live-only** `/etc/sysctl.d/20-apparmor.conf` override that disables unprivileged user namespace restriction. Verify upstream fix independently and do not release before a tested installed system shows the intended effective AppArmor policy.
- [Ubuntu bug #2172138](https://bugs.launchpad.net/bugs/2172138) reports an encrypted Calamares install whose generated `crypttab` lacked the `luks` option and failed to boot. Do not enable encrypted install until disposable-VM LUKS2 boot and recovery tests pass.
- `build/audit-installed-root.py` is a **read-only offline static auditor**; its `safe_to_install` field is always false, and no successful static check replaces runtime boot/restore evidence.
