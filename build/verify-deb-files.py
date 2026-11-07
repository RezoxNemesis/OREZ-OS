#!/usr/bin/env python3
"""Read-only .deb file-list and maintainer-script guard for OREZ's own package.

This validates provenance within a locally built artifact; it never installs
the package and never grants permission to install a complete operating system.
"""
import argparse
import io
import json
import pathlib
import subprocess
import sys
import tarfile


def manifest(text):
    values = []
    for line in text.splitlines():
        p = line.strip()
        if not p or p.startswith("#"):
            continue
        if p.startswith("/") or ".." in pathlib.PurePosixPath(p).parts or "\\" in p:
            raise ValueError("unsafe manifest path: " + p)
        values.append(p)
    if not values or len(values) != len(set(values)):
        raise ValueError("empty or duplicated manifest")
    return set(values)


def parse_contents(text):
    paths = set()
    forbidden_types = []
    for line in text.splitlines():
        parts = line.split(maxsplit=5)
        if len(parts) < 6:
            raise ValueError("unexpected dpkg-deb file listing format")
        permissions, name = parts[0], parts[5].split(" -> ", 1)[0]
        if not name.startswith("./"):
            raise ValueError("unsafe dpkg-deb archive pathname")
        relative = name[2:].rstrip("/")
        if not relative or permissions.startswith("d"):
            continue
        if not permissions.startswith("-"):
            forbidden_types.append(relative)
        paths.add(relative)
    return paths, sorted(forbidden_types)


def inspect(contents, required, control_members, package_name, architecture):
    present, other_types = parse_contents(contents)
    wanted = manifest(required)
    members = {
        member.removeprefix("./").strip("/")
        for member in control_members
        if member.strip("./")
    }
    dangerous_scripts = sorted(members & {
        "preinst", "postinst", "prerm", "postrm", "config", "templates"
    })
    unexpected_control = sorted(members - {"control", "md5sums"})
    missing = sorted(wanted - present)
    unexpected = sorted(present - wanted)
    bad_permissions = []
    for line in contents.splitlines():
        parts = line.split(maxsplit=5)
        mode, owner, name = parts[0], parts[1], parts[5].split(' -> ', 1)[0]
        relative = name.removeprefix('./').rstrip('/')
        expected = 'drwxr-xr-x' if mode.startswith('d') else '-rwxr-xr-x' if relative.startswith('usr/bin/') or (relative.startswith('etc/xdg/plasma-workspace/env/') and relative.endswith('.sh')) else '-rw-r--r--'  # same rule as stage-overlay.py
        if mode != expected or owner != 'root/root':
            bad_permissions.append({'path': name, 'mode': mode, 'owner': owner, 'expected': expected})
    blocked = bool(
        missing or unexpected or other_types or dangerous_scripts or
        unexpected_control or bad_permissions or package_name != "orez-shell" or architecture != "all"
    )
    return {
        "status": "BLOCKED" if blocked else "PACKAGE_CONTENTS_PASS",
        "installation_approved": False,
        "manifest_paths": len(wanted),
        "missing_files": missing,
        "unexpected_files": unexpected,
        "nonregular_payload_files": other_types,
        "maintainer_scripts": dangerous_scripts,
        "unexpected_control_members": unexpected_control,
        "package": package_name,
        "architecture": architecture,
        "invalid_permissions_or_owners": bad_permissions,
        "limitations": "No installation, apt dependency resolution, dpkg ownership on target, boot or recovery test performed.",
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--package", type=pathlib.Path, required=True)
    p.add_argument("--manifest", type=pathlib.Path, required=True)
    p.add_argument("--report", type=pathlib.Path, required=True)
    p.add_argument("--version", help="Expected declared version; reject stale package artifacts")
    args = p.parse_args()
    try:
        if not args.package.is_file():
            raise ValueError("Debian archive missing")
        def run(*argv):
            return subprocess.check_output(["dpkg-deb", *argv, str(args.package)])
        contents = run("--contents").decode()
        meta_name = subprocess.check_output(
            ["dpkg-deb", "--field", str(args.package), "Package"]
        ).decode().strip()
        meta_arch = subprocess.check_output(
            ["dpkg-deb", "--field", str(args.package), "Architecture"]
        ).decode().strip()
        ctrl = run("--ctrl-tarfile")
        with tarfile.open(fileobj=io.BytesIO(ctrl), mode="r:*") as tar:
            members = [m.name for m in tar.getmembers() if m.isfile() or m.issym() or m.islnk()]
        result = inspect(contents, args.manifest.read_text(), members, meta_name, meta_arch)
        result['version'] = subprocess.check_output(['dpkg-deb', '--field', str(args.package), 'Version']).decode().strip()
        if args.version and result['version'] != args.version:
            result.update(status='BLOCKED', expected_version=args.version)
    except (OSError, ValueError, subprocess.CalledProcessError, tarfile.TarError) as exc:
        print("OREZ .deb audit refused: " + str(exc), file=sys.stderr)
        return 2
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print("OREZ .deb manifest and maintainer-script audit: " + result["status"])
    return int(result["status"] != "PACKAGE_CONTENTS_PASS")


if __name__ == "__main__":
    sys.exit(main())
