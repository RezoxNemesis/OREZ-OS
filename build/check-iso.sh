#!/usr/bin/env bash
# Static checks only; this is NOT a substitute for QEMU or hardware boot tests.
set -euo pipefail
[[ "$#" -eq 1 && -f "$1" ]] || { echo 'Usage: check-iso.sh PATH/ISO' >&2; exit 2; }
command -v xorriso >/dev/null || { echo 'xorriso missing' >&2; exit 2; }
iso="$1"
listing="$(xorriso -indev "$iso" -ls /casper 2>&1)"
for name in filesystem.squashfs zz-orez.squashfs orez-install.squashfs initrd vmlinuz; do
  grep -Fq "$name" <<<"$listing" || { echo "Missing /casper/$name" >&2; exit 1; }
done
# Boot record details must be present; an ISO structure check is not a boot test.
boot="$(xorriso -indev "$iso" -report_el_torito plain 2>&1)"
grep -Eiq 'El Torito|boot image' <<<"$boot" || { echo 'No El Torito boot metadata' >&2; exit 1; }
area="$(xorriso -indev "$iso" -report_system_area plain 2>&1)"
[[ -n "$area" ]] || { echo 'No system area diagnostics' >&2; exit 1; }
echo 'Static ISO structure: PASS (boot execution NOT tested)'
