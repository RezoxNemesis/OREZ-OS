#!/usr/bin/env python3
"""Read-only inspection of an *existing* installed root for OREZ alpha blockers.

Not an installer, repair tool or certification. No shell commands are executed.
Run against a disposable VM's installed filesystem before approving installation.
"""
import argparse
import json
import re
import stat
import sys
from pathlib import Path


def inspect(root: Path, expect_encryption: bool = False, expect_btrfs: bool = False,
            owner: str | None = None) -> dict:
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

    if owner is not None:
        if not re.fullmatch(r'[a-z_][a-z0-9_-]{0,31}', owner) or owner == 'root':
            raise ValueError('Provide the expected normal owner username')
        passwd, shadow, group = read('etc/passwd'), read('etc/shadow'), read('etc/group')
        if any(value is None for value in [passwd, shadow, group]):
            record('owner_accounts', 'fail', 'Cannot inspect all required account databases')
        else:
            def rows(text, count):
                result = {}
                for line in text.splitlines():
                    if not line or line.startswith('#'):
                        continue
                    fields = line.split(':')
                    if len(fields) != count or fields[0] in result:
                        raise ValueError('Malformed or duplicate account database entry')
                    result[fields[0]] = fields
                return result
            users, secrets, groups = rows(passwd, 7), rows(shadow, 9), rows(group, 4)
            chosen = users.get(owner)
            normal = chosen is not None and 1000 <= int(chosen[2]) < 65534
            unique = normal and sum(int(u[2]) == int(chosen[2]) for u in users.values()) == 1
            record('owner_identity', 'pass' if unique else 'fail',
                   'Expected owner must have a unique normal-user UID')
            root_names = {name for name, fields in users.items() if int(fields[2]) == 0}
            record('root_identity', 'pass' if root_names == {'root'} else 'fail',
                   'Only the root account may have UID zero')
            root_locked = secrets.get('root', ['', ''])[1].startswith(('!', '*'))
            record('root_password_locked', 'pass' if root_locked else 'fail',
                   'Direct root password login must be locked; SSH/PAM runtime needs separate tests')
            owner_hash = secrets.get(owner, ['', ''])[1]
            configured = bool(re.fullmatch(r'\$(?:y|6|5|2[aby])\$[^:\n]+\$[^:\n]+', owner_hash))
            record('owner_password', 'pass' if configured else 'fail',
                   'Owner must have a configured modular password hash; no value is logged')
            admins = set()
            for name in ['sudo', 'admin', 'wheel']:
                if name not in groups:
                    continue
                entry = groups[name]
                admins.update(filter(None, entry[3].split(',')))
                admins.update(name for name, fields in users.items() if int(fields[3]) == int(entry[2]))
            record('administrator_groups', 'pass' if admins - {'root'} == {owner} else 'fail',
                   'Known administrator groups must contain only the expected human owner; custom authorization still needs runtime review')
            shadow_path = (root / 'etc/shadow').resolve()
            metadata = shadow_path.stat()
            mode = stat.S_IMODE(metadata.st_mode)
            # Interpret IDs using the selected installed root, never the
            # builder's host group database. A copied tree must preserve its
            # real installed metadata; an unprivileged extraction is not proof.
            allowed_gids = {
                int(fields[2]) for name, fields in groups.items()
                if name == 'shadow' or (name == 'root' and int(fields[2]) == 0)
            }
            group_members = {
                member for fields in groups.values() if int(fields[2]) == metadata.st_gid
                for member in fields[3].split(',') if member
            }
            group_members.update(name for name, fields in users.items()
                                 if int(fields[3]) == metadata.st_gid)
            # Include every alias of a numeric GID, primary memberships and
            # unresolved member names. Even the owner should authenticate to
            # obtain privileged access rather than read hashes as an ordinary
            # process. Unexpected service readers also need explicit review.
            exposed_members = group_members - {'root'} if mode & 0o040 else set()
            protected = (stat.S_ISREG(metadata.st_mode) and metadata.st_uid == 0
                         and metadata.st_gid in allowed_gids and bool(mode & 0o400)
                         and not mode & ~0o640 and not exposed_members)
            record('shadow_permissions', 'pass' if protected else 'fail',
                   'Shadow must be a root-owned regular file, readable by root, with only safe root/shadow-group access; group-readable hashes must not be exposed to non-root accounts. Verify metadata-preserving extraction and effective ACL/runtime policy separately')
        # A scoped static check, not a replacement for visudo and effective
        # sudo/Polkit/SSH authorization tests on the installed system.
        sudo_paths = ['etc/sudoers']
        directory = (root / 'etc/sudoers.d').resolve()
        if not directory.is_relative_to(root):
            raise ValueError('Sudo configuration directory escapes selected root')
        if directory.exists():
            sudo_paths += ['etc/sudoers.d/' + p.name for p in directory.iterdir() if p.is_file()]
        policy = [read(path) for path in sudo_paths]
        lines = [line for content in policy if content for line in content.splitlines()
                 if line.strip() and not line.lstrip().startswith('#')]
        record('known_passwordless_sudo', 'fail' if any(re.search(r'\bNOPASSWD\s*:', line, re.I) for line in lines)
               else 'unknown' if policy[0] is None else 'pass',
               'Known NOPASSWD tags in the main sudoers files are forbidden; includes, aliases and other authorization mechanisms still need effective tests')

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
    parser.add_argument("--owner", help="Expected installed owner; inspect account/known sudo policy without logging hashes")
    parser.add_argument("--strict", action="store_true", help="Treat missing hardening evidence as a CI failure")
    args = parser.parse_args(argv)
    try:
        result = inspect(args.root, args.expect_encryption, args.expect_btrfs, args.owner)
    except (OSError, ValueError) as exc:
        print(json.dumps({"status": "blocked", "error": str(exc), "safe_to_install": False}))
        return 2
    print(json.dumps(result, indent=2))
    if result["blockers"] or (args.strict and result["unknowns"]):
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
