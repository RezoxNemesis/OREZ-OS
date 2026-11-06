# OREZ OS installer synthetic replay — security gate, NOT an install

The current Calamares candidate is deliberately inactive. The live ISO's normal
installer is replaced with a visible refusal until real installation and recovery
tests qualify. This page describes additional *source-level* protection.

The Python unittest test_install_manifest_replay.py:
- requires the candidate's exact three-source order: base Kubuntu, native-app
  delta, then the dpkg-owned OREZ SquashFS
- requires the known live-only AppArmor override to be excluded from the
  eventual installed root
- verifies OREZ's installed file allowlist contains no Calamares executable,
  VM-only witness, debug compositor script or policy overrides
- replays the allowlisted real repository files to a disposable TemporaryDirectory
- checks a synthetic AppArmor policy leak is caught and the excluded variant
  passes the offline auditor
- always requires safe_to_install=false

It does NOT run Calamares, copy the 5 GB base filesystem, write to an NVMe/USB
device, create partitions, encrypt storage, boot the installed result or prove a
real AppArmor kernel policy. The test fixture's vendor policy is synthetic.
Passing is an engineering guard against regression, NOT release approval.

Real next stages: a full isolated VM installation onto disposable virtual drives,
installed OREZ layer persistence, 26.04.1 AppArmor and LUKS issues, Btrfs snapshot
and backup/restore drills, explicit disk selection safety, Secure Boot and target
MSI/NVIDIA/Android device qualification. Never overwrite the Windows recovery USB.
