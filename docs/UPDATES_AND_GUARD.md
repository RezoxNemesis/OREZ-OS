# Owner-controlled upgrades and security monitoring

Owner requirement, 5 November 2026: applications/OS need an upgrade path, and no
update, vendor or AI may silently weaken owner control. Suspicious activity must
be detected without unnecessarily interrupting legitimate work.

**Status:** this is the implementation contract and acceptance plan. A maintained
signed OREZ update repository and autonomous detection agent do not exist yet.
Existing `orezctl security` is a read-only status command, not an antivirus or
intrusion detector. Local synthetic APT upgrade/downgrade tests do not establish
a production update channel or complete system rollback.

The follow-up actual-package test upgrades `0.1.0-1` to `0.1.0-2` offline in a
rootless disposable container. It verifies ordinary-user denial, changed command
bytes and installed version, preserved project file/appearance opt-out/private
Android configuration, and stable repeat installation. Ten synthetic APT failure
and rollback cases also pass. These narrow results do not qualify signed remote
updates, a compromised authorized package, or full-system recovery.

## 1. Security policy persists through updates

The durable rule is owner-only human administration, no AI elevation bypass,
no vendor recovery credential and no hidden remote control. Security software
must still receive vulnerability fixes; freezing old protection code forever
would undermine the rule. OS mechanisms, code and signatures cannot guarantee
immunity to compromised authorized code or future vulnerabilities.

- Use distro-signed APT for the supported foundation; a separately scoped signed
  OREZ APT repository for original native components; Flatpak/provider channels
  for compatible applications. Show origin, installed/available version,
  signature status, relevant changes, download size and restart requirements.
  Third-party installation remains available under normal OS permissions.
- New permissions, administrator identities, remote listeners, broad device
  access, security-control disablement or a new trust root require a separate
  visible owner-authenticated decision. A release signature or AI prompt is not
  blanket consent to expand those grants. Do not apply them silently in a package
  script or migration. The current agent is subject to the same rule.
- Keep owner policy outside ordinary app-writable state, with restricted ownership,
  versioned schema, explicit migration and documented recovery. Store no vendor
  master password. AI/services can propose a change; only an authenticated owner
  can authorize it through a trusted system UI.
- Review package payloads and maintainer scripts, service units, sudo/Polkit rules,
  capabilities/setuid files, firewall/listener changes and permission migrations.
  CI must reject unauthorized policy regressions. Runtime and release signing
  keys are separate; production private keys never enter untrusted PR workflows.
- Settings → Updates shows automatic-download/install preferences, maintenance
  window, metered-network behavior, failures, logs and restore options. Initial
  policy: notify/download with owner configuration; no surprise application kill
  or forced reboot. Security updates should be timely with visible status.
- Stage/check an update, preserve required backups and previous recoverable boot
  state, then install. Apply migrations transactionally where possible. Verify
  services/boot/permissions afterward. Snapshots do not replace independent data
  backups. Never silently restore old user files or roll back into a known
  vulnerable version. Offer documented recovery with consequences explained.

## 2. Evidence-based local monitoring

No detector can perfectly identify the owner from input signals. Physical
keyboards can be spoofed, malware can inject input, and legitimate accessibility,
phone, remote-session or automation tools also generate software input. Typed
commands are not cryptographic proof of human authorization.

Use permission enforcement first, then local evidence from authentication,
application permissions, process/service identity, package integrity, device
changes and authorized remote sessions. Do not record keystrokes, passwords,
bank-page contents or personal screenshots. No cloud telemetry or external
administrator dashboard by default.

| Evidence | Default response |
|---|---|
| Operation lacks required OS permission | Existing kernel/Polkit/AppArmor boundary denies it; record a concise event |
| New administrator/trust/remote-control grant | Require separate owner authentication; a process cannot approve itself |
| Unknown device or remote session | Visible alert; apply the configured device/session policy, never guess identity from timing |
| Suspicious behavior with uncertain attribution | Non-disruptive explanation and owner choices; no automatic process kill, file deletion, radio shutoff or account suspension |
| Confirmed malicious newly downloaded file | Offer quarantine; automatic quarantine only under an explicit owner policy, with isolated storage, metadata and safe restore guidance |
| Active high-confidence containment condition | Only narrowly specified, preauthorized response; preserve evidence/work where possible and provide an emergency override/recovery path |

A first monitor should use maintained Linux audit/journal and application/device
permission events. Start in observe/notify mode, measure false positives and
resource cost before enabling optional automated containment. Signature scanning
may be on demand or limited to configured downloads; do not scan every project,
VM disk and model repeatedly. No expensive network inspection/ML model at boot.
No unreviewed root ML agent, arbitrary shell-action callback or automatically
rewritten security rule is acceptable.

Separate an unprivileged UI/detection process from a minimal audited action broker.
The broker, if implemented, accepts typed allowlisted actions and rechecks OS
permissions; it never accepts model-generated shell commands. Cancellation,
expiry, session revocation and emergency stop remain available. AI output is an
untrusted recommendation, not authentication or an exception to policy.

Optional USB policy can require consent for new HID devices, particularly while
locked, but must preserve a tested trusted keyboard/recovery route. Ordinary
apps should not gain `/dev/uinput` or compositor remote-input access automatically.
KDE Connect, accessibility and explicitly approved automation need distinguishable,
revocable grants; do not treat them as intrusions merely because input is synthetic.

## 3. Precision, performance and financial-use boundaries

Expose evidence, affected process/device, action taken and confidence/uncertainty
in Settings → Security → Activity. Provide per-rule status, explanation, retention,
export, disable/reset and owner-only response configuration. Rate-limit duplicate
alerts and bound local logs; default to metadata, not content collection.

Before enabling automation, test legitimate typing/mouse input, accessibility,
KDE Connect, scrcpy, approved development/debugging tools, games, compilers,
package updates, screen readers and financial websites. Test unauthorized
permission requests, mock malicious downloads, failed logins, revoked sessions
and spoofed/missing event attribution. Measure false positives/negatives,
foreground latency, CPU/RAM/energy and recovery under load. No false-positive-free
or perfect-owner-identification claim is permitted.

For financial use, keep supported sandboxed browsers/apps updated, isolate
untrusted extensions/profiles, protect credentials, support strong account
authentication/passkeys where the provider offers them, and avoid granting
screen/clipboard access unnecessarily. OREZ cannot guarantee a banking service,
website or authorized third-party extension is uncompromised. Never intercept
financial credentials to infer whether an action belongs to the owner.

## 4. Required implementation sequence and acceptance

1. Define the owner-policy schema and privilege boundaries; threat-review them
   before writing a privileged service. Add negative tests for AI/tool-response
   self-approval and unauthorized grants, including update/migration paths.
2. Establish native component versioning, signed repository metadata, owner-held
   signing/revocation/rotation process, SBOM/provenance and release retention.
3. Validate signed good/bad/expired/revoked updates, offline/interrupted download,
   insufficient disk, changed permissions, failed migrations, reboot/rollback
   and independent data restoration on disposable disks.
4. Implement bounded local observe-only monitoring with searchable transparent
   controls; evaluate false positives on actual owner workflows.
5. Enable only individually qualified, explicitly configured responses. Test
   broker denials, log limits, tampering, recovery and emergency stop. Preserve
   normal work when evidence is ambiguous.

A future implementation must demonstrate these properties through code and
negative/runtime tests. This document itself is not a working security layer.
