# Owner control and repository visibility

Updates/security follow-up: [UPDATES_AND_GUARD.md](UPDATES_AND_GUARD.md) defines
owner-authorized upgrades, protection-policy invariants and local detection that
preserves legitimate work. Security software receives fixes; no AI/vendor may
silently expand privileges. Autonomous detection and signed OREZ updates remain
unimplemented; perfect owner identification or zero false positives is not claimed.

Owner instruction, 5 November 2026: **RezoxNemesis is the sole human administrator
and development authority.** Third-party services may provide functionality but
must not receive an OREZ administrator identity, remote management channel,
recovery bypass, vendor master key or control over system configuration.

## Host enforcement contract

- The installer must create only the owner's chosen administrative user, with
  a locked direct root login. Additional human accounts default to standard
  users; any later administrator grant requires the owner's explicit action and
  authentication. This installer policy is still a release acceptance gate,
  not an implemented/verified installation claim.
- Google sign-in is confined to the chosen Android guest. No Google account is
  used for Linux login, sudo, Polkit, disk unlock, signing keys or recovery.
- AI, MCP tools, websites, downloaded applications and remote service responses
  cannot authorize elevation. No vendor/admin credentials, passwordless sudo
  rules, hidden remote services or externally controlled update keys are added.
- Privileged local Linux services and kernel/GPU drivers remain necessary.
  Their execution is not a vendor login. Root-capable package installation still
  executes trusted distributor code and requires owner authorization; third-party
  packages are not automatically trusted merely because they are in a store.
- Android runs under a non-root host account with no default shared home,
  physical disks, USB passthrough or host-admin credentials. Clipboard, camera,
  microphone and shared folders must receive explicit, revocable controls before
  a consumer runtime is qualified. Guest root, if ever offered for development,
  must never imply host root; the initial Play profile does not request it.
- Settings must expose every service, capability and integration with current
  status, logs, off controls and safe reset. Emergency stop terminates only the
  owned guest process, not unrelated user applications.

No absolute protection against vulnerabilities, a compromised approved package,
stolen owner credentials or physical attack can be promised. Release testing
must verify actual effective permissions and recovery, not merely source text.

## Public now; private when PC-ready

The owner explicitly chose **public during development** and **private when OREZ
is completely ready for the PC**. Do not change visibility early. Public readers
may view and fork published code; that does not grant repository write access or
host administrator rights. Making the repository private later cannot recall
existing copies, and does not remove upstream open-source source-offer obligations.

The privacy transition is a required release task after all PC readiness gates
pass: visible UEFI/live boot, safe install/reboot, independent recovery, actual
MSI/RTX/Secure Boot/network/audio/USB checks, functional owner controls and the
agreed Android compatibility gate. Verify the evidence, save an owner-held backup,
then apply and verify the requested private visibility using owner-authorized
repository administration access. Do not mark it done before the setting changes.

Only the owner may authorize code changes or administrative grants. Automation
is revocable, task-scoped assistance under the owner's authority, not a separate
human administrator or independent maintainer. Public PR submission is not write
access and must never trigger a privileged workflow with contributor-controlled
code and secrets. Existing workflows declare read-only contents permissions.

## Verified audit and unresolved access check

The connected GitHub metadata reports owner `RezoxNemesis`, repository public,
and owner permission `admin`. Repository rulesets returned an empty list. This
does not prove that no collaborators, invitations, branch-protection settings,
deploy keys or installed apps have write access.

The connector rejects the collaborator-list and workflow-permission endpoints
as unsupported. The read-only browser fallback could not start because its
Browser Use project has insufficient credits. **Collaborator/write-access audit
is therefore incomplete; no access setting was changed.** Do not retry a billed
tool or claim an access restriction has been applied. Use the owner's GitHub
Settings → Collaborators/access, deploy keys, installed applications and Actions
permissions to complete the audit when an authorized interface is available.
