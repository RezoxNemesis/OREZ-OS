#!/usr/bin/env python3
"""Read-only inspection of an *existing* installed root for OREZ alpha blockers.

Not an installer, repair tool or certification. No shell commands are executed.
Run against a disposable VM's installed filesystem before approving installation.
"""
import argparse
import json
import re
import sys
from pathlib import Path


def inspect(root: Path, expect_encryption: bool = False, expect_btrfs: bool = False) -> dict:
    root = root.resolve(strict=True)
    if not root.is_dir():
        raise ValueError("--root must be an existing directory")

    checks = []

    def record(name: str, status: str, detail: str):
        checks.append({"id": name, "status": status, "detail": detail})

    def read(relative: str):
        candidate = root / relative
        resolved = candidate.resolve(strict=False)
        if not resolved.is_relative_to(root):
            raise ValueError(f"Path escapes selected root: {relative}")
        try:
            return resolved.read_text(encoding="utf-8", errors="replace")
        except FileNotFoundError:
            return None

    identity = read("etc/orez-release")
    if identity and "OREZ" in identity.upper() and read("usr/bin/orezctl") is not None:
        record("installed_orez_identity", "pass", "OREZ identity and CLI are present in installed root")
    else:
        record("installed_orez_identity", "fail", "Installed OREZ files are missing: live-only overlays cannot pass")

    # LP #2172113: live-only AppArmor override can leak into installed systems.
    override = read("etc/sysctl.d/20-apparmor.conf")
    if override and re.search(r"(?m)^\s*kernel\.apparmor_restrict_unprivileged_userns\s*=\s*0\s*(?:#.*)?$", override):
        record("apparmor_live_override", "fail", "Live-only AppArmor user-namespace restriction override remains in installed root")
    else:
        record("apparmor_live_override", "pass", "No known live-only disablement detected in /etc/sysctl.d/20-apparmor.conf")
    vendor = read("usr/lib/sysctl.d/10-apparmor.conf") or ""
    if "kernel.apparmor_restrict_unprivileged_userns" in vendor:
        record("apparmor_vendor_policy", "pass", "Vendor AppArmor policy exists; effective runtime policy still needs testing")
    else:
        record("apparmor_vendor_policy", "unknown", "Cannot confirm expected AppArmor vendor policy in installed root")

    crypttab = read("etc/crypttab") or ""
    entries = [line.split() for line in crypttab.splitlines() if line.strip() and not line.lstrip().startswith('#')]
    if expect_encryption:
        if not entries:
            record("luks_root_crypttab", "fail", "Encryption requested, but no crypttab mapping found")
        elif any(len(e) < 4 or "luks" not in e[3].split(',') for e in entries):
            record("luks_root_crypttab", "fail", "Encrypted mapping lacks explicit luks option; check Kubuntu bug #2172138")
        else:
            record("luks_root_crypttab", "pass", "Encrypted mappings request explicit LUKS; actual unlock boot still needs VM test")
    else:
        record("luks_root_crypttab", "not-applicable", "Encryption was not requested in this inspection")

    fstab = read("etc/fstab") or ""
    if expect_btrfs:
        root_entries = [line.split() for line in fstab.splitlines() if line.strip() and not line.lstrip().startswith('#')]
        if any(len(e) >= 3 and e[1] == '/' and e[2] == 'btrfs' for e in root_entries):
            record("btrfs_root", "pass", "Root filesystem entry specifies Btrfs; snapshots/rollback remain unverified")
        else:
            record("btrfs_root", "fail", "Blueprint requires Btrfs but installed root does not declare it")
    else:
        record("btrfs_root", "not-applicable", "Btrfs installation was not requested in this inspection")

    blockers = [c["id"] for c in checks if c["status"] == "fail"]
    unknowns = [c["id"] for c in checks if c["status"] == "unknown"]
    return {
        "tool": "OREZ installed-root read-only audit",
        "mode": "offline installed-root inspection",
        "status": "blocked" if blockers else ("incomplete" if unknowns else "static-checks-passed"),
        "safe_to_install": False,
        "blockers": blockers,
        "unknowns": unknowns,
        "checks": checks,
        "notice": "Never claim installer, boot, recovery or physical-PC certification from this static inspection.",
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path, help="Existing disposable VM installed-root directory; no writes")
    parser.add_argument("--expect-encryption", action="store_true")
    parser.add_argument("--expect-btrfs", action="store_true")
    parser.add_argument("--strict", action="store_true", help="Treat missing hardening evidence as a CI failure")
    args = parser.parse_args(argv)
    try:
        result = inspect(args.root, args.expect_encryption, args.expect_btrfs)
    except (OSError, ValueError) as exc:
        print(json.dumps({"status": "blocked", "error": str(exc), "safe_to_install": False}))
        return 2
    print(json.dumps(result, indent=2))
    if result["blockers"] or (args.strict and result["unknowns"]):
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
