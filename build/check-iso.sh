#!/usr/bin/env bash
# Static checks only; this is NOT a substitute for QEMU or hardware boot tests.
set -euo pipefail
[[ "$#" -eq 1 && -f "$1" ]] || { echo 'Usage: check-iso.sh PATH/ISO' >&2; exit 2; }
command -v xorriso >/dev/null || { echo 'xorriso missing' >&2; exit 2; }
iso="$1"
listing="$(xorriso -indev "$iso" -ls /casper 2>&1)"
for name in filesystem.squashfs zz-orez.squashfs orez-install.squashfs initrd vmlinuz orez-initrd.json; do
  grep -Fq "$name" <<<"$listing" || { echo "Missing /casper/$name" >&2; exit 1; }
done
# Boot record details must be present; an ISO structure check is not a boot test.
boot="$(xorriso -indev "$iso" -report_el_torito plain 2>&1)"
grep -Eiq 'El Torito|boot image' <<<"$boot" || { echo 'No El Torito boot metadata' >&2; exit 1; }
area="$(xorriso -indev "$iso" -report_system_area plain 2>&1)"
[[ -n "$area" ]] || { echo 'No system area diagnostics' >&2; exit 1; }
# Installation-only OREZ layer must exist and carry NO live-only services or installer guards.
# This is a static payload check, never an installer or filesystem mount.
command -v unsquashfs >/dev/null || { echo 'unsquashfs missing' >&2; exit 2; }
tmp="$(mktemp -d)"
trap 'rm -rf -- "$tmp"' EXIT
repo="$(cd -- "$(dirname -- "$0")/.." && pwd -P)"
xorriso -osirrox on -indev "$iso" -extract /casper/initrd "$tmp/initrd" >/dev/null 2>&1
xorriso -osirrox on -indev "$iso" -extract /casper/orez-initrd.json "$tmp/orez-initrd.json" >/dev/null 2>&1
python3 "$repo/build/patch-live-initrd.py" --verify --input "$tmp/initrd" --report "$tmp/orez-initrd.json"
python3 - "$tmp/orez-initrd.json" <<'PY_OWNER_PROFILE'
import json,sys
value=json.load(open(sys.argv[1]))
if value.get('schema_version') != 3 or not value.get('administrator_policy_changed'):
    raise SystemExit('Missing reviewed live-owner setup profile; legacy passwordless images are not current candidates.')
PY_OWNER_PROFILE
xorriso -osirrox on -indev "$iso" -extract /casper/orez-install.squashfs "$tmp/install.squashfs" >/dev/null 2>&1
[[ -s "$tmp/install.squashfs" ]] || { echo 'OREZ install payload missing from ISO' >&2; exit 1; }
files="$(unsquashfs -ll "$tmp/install.squashfs")"
for expected in squashfs-root/etc/orez-release squashfs-root/usr/bin/orezctl squashfs-root/usr/share/backgrounds/orez/orez-ink.svg; do
  grep -Fq "$expected" <<< "$files" || { echo "Missing install-safe OREZ component: $expected" >&2; exit 1; }
done
if grep -Eq 'squashfs-root/(usr/bin/calamares|etc/sysctl.d/20-apparmor.conf|usr/lib/orez/owner_setup.py|usr/lib/systemd/system/orez-owner-setup.service|usr/lib/systemd/system/orez-.*verify.service|etc/systemd/system)' <<< "$files"; then
  echo 'Unsafe live-only component leaked into OREZ install payload' >&2
  exit 1
fi
# A missing live-only installer guard must fail image construction.
# This does not prevent arbitrary root disk writes; it blocks the usual GUI install path.
xorriso -osirrox on -indev "$iso" -extract /casper/zz-orez.squashfs "$tmp/live.squashfs" >/dev/null 2>&1
[[ -s "$tmp/live.squashfs" ]] || { echo 'OREZ live layer absent' >&2; exit 1; }
python3 "$repo/build/verify-live-owner.py" --source "$repo/image/live-owner" --squashfs "$tmp/live.squashfs"
unsquashfs -cat "$tmp/live.squashfs" usr/bin/calamares > "$tmp/orez-installer-guard" 2>/dev/null ||
  { echo 'Live installer guard missing inside ISO' >&2; exit 1; }
grep -Fq 'OREZ LIVE TEST' "$tmp/orez-installer-guard" ||
  { echo 'OREZ live installer guard message missing' >&2; exit 1; }
grep -Fqx 'exit 78' "$tmp/orez-installer-guard" ||
  { echo 'OREZ live installer guard must refuse installation' >&2; exit 1; }
# Check the four changed/added files against the upstream media-error list.
xorriso -osirrox on -indev "$iso" -extract /md5sum.txt "$tmp/md5sum.txt" >/dev/null 2>&1
python3 - "$repo" "$tmp" <<'PY_CHECK'
import importlib.util
from pathlib import Path
import sys
repo, root = map(Path, sys.argv[1:])
spec = importlib.util.spec_from_file_location('media', repo / 'build/update-media-checksums.py')
media = importlib.util.module_from_spec(spec); spec.loader.exec_module(media)
entries = media.parse((root / 'md5sum.txt').read_text())
for name, local in zip(media.NAMES, ['initrd', 'orez-initrd.json', 'live.squashfs', 'install.squashfs']):
    if entries.get(name) != media.md5(root / local):
        raise SystemExit(f'Media checksum mismatch: {name}')
print('PASS: four OREZ media-error checksums match extracted bytes (not an authenticity proof)')
PY_CHECK
echo 'Static ISO structure, install-safe payload and live-only installer guard: PASS (boot/install execution NOT tested)'
