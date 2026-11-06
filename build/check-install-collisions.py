#!/usr/bin/env python3
"""Fail-closed, read-only comparison of a Kubuntu base and OREZ install-layer file list.

Lists come from unsquashfs -ls. This does not install an OS or certify an installer.
"""
import argparse
import json
import pathlib
import sys


def read_listing(text: str) -> set[str]:
    prefix = "squashfs-root/"
    return {line.strip()[len(prefix):] for line in text.splitlines()
            if line.strip().startswith(prefix)}


def manifest_paths(text: str) -> list[str]:
    names = []
    for raw in text.splitlines():
        name = raw.strip()
        if not name or name.startswith("#"):
            continue
        parts = pathlib.PurePosixPath(name).parts
        if name.startswith("/") or ".." in parts or "." in parts or "\\" in name:
            raise ValueError(f"unsafe path in payload manifest: {name}")
        names.append(name)
    if len(names) != len(set(names)):
        raise ValueError("duplicate paths in OREZ manifest")
    if not names:
        raise ValueError("OREZ manifest is empty")
    return names


def inspect(base_text: str, payload_text: str, manifest_text: str) -> dict:
    base = read_listing(base_text)
    payload = read_listing(payload_text)
    wanted = set(manifest_paths(manifest_text))
    missing = sorted(wanted - payload)
    collisions = sorted(wanted & base)
    unexpected_files = sorted(
        path for path in payload if path not in wanted and
        not any(file.startswith(path + "/") for file in wanted)
    )
    # Parent directories are harmless; unexpected files, symlinks or additional
    # content must not silently enter an installed filesystem layer.
    failed = bool(missing or collisions or unexpected_files)
    return {
        "tool": "OREZ offline install-layer path collision check",
        "status": "BLOCKED" if failed else "STATIC_FILE_PATHS_PASS",
        "installation_approved": False,
        "paths_in_manifest": len(wanted),
        "overwrites_existing_base_paths": collisions,
        "missing_manifest_paths": missing,
        "unexpected_payload_paths": unexpected_files,
        "limitations": "No actual Calamares, ownership, symlink-target, AppArmor runtime, encrypted boot, or recovery test performed.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-list", type=pathlib.Path, required=True)
    parser.add_argument("--payload-list", type=pathlib.Path, required=True)
    parser.add_argument("--manifest", type=pathlib.Path, required=True)
    parser.add_argument("--report", type=pathlib.Path, required=True)
    args = parser.parse_args()
    try:
        report = inspect(args.base_list.read_text(), args.payload_list.read_text(),
                         args.manifest.read_text())
    except (OSError, ValueError) as exc:
        print(f"Installer layer collision check failed closed: {exc}", file=sys.stderr)
        return 2
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(f"OREZ install overlay: {report['status']}; installation_approved=false")
    if report["status"] != "STATIC_FILE_PATHS_PASS":
        print(json.dumps(report, indent=2), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
