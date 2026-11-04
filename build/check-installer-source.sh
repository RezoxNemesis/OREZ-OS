#!/usr/bin/env bash
# Inspect real Calamares input inside an ISO; do not mount or modify disks.
set -Eeuo pipefail
[[ "$#" -eq 1 && -f "$1" ]] || { echo 'Usage: check-installer-source.sh OREZ.iso' >&2; exit 2; }
for tool in xorriso unsquashfs grep mktemp; do command -v "$tool" >/dev/null || { echo "Missing $tool" >&2; exit 2; }; done
ISO="$(realpath "$1")"
ROOT="$(cd -- "$(dirname -- "$0")/.." && pwd -P)"
OUT="$ROOT/dist/boot-evidence"
mkdir -p -- "$OUT"
TEMP="$(mktemp -d "$OUT/installer-inspect-XXXXXXXX")"
trap 'rm -rf -- "$TEMP"' EXIT
REPORT="$OUT/INSTALLER_READINESS.txt"
xorriso -osirrox on -indev "$ISO" -extract /casper/filesystem.squashfs "$TEMP/base.squashfs" >/dev/null 2>&1
[[ -s "$TEMP/base.squashfs" ]] || { echo 'Missing installer base squashfs' >&2; exit 1; }
unsquashfs -cat "$TEMP/base.squashfs" etc/calamares/modules/unpackfs.conf > "$OUT/upstream-unpackfs.conf" 2>/dev/null || {
  echo 'Cannot inspect original Calamares unpackfs.conf' >&2; exit 1;
}
if grep -Fq 'orez-install.squashfs' "$OUT/upstream-unpackfs.conf"; then
  install_source='NEEDS_MANUAL_REVIEW: OREZ install-only payload referenced'
else
  install_source='BLOCKED: stock Calamares ignores the OREZ install-only payload'
fi
if unsquashfs -cat "$TEMP/base.squashfs" etc/sysctl.d/20-apparmor.conf > "$OUT/upstream-live-apparmor.conf" 2>/dev/null &&
   grep -Eq '^kernel\.apparmor_restrict_unprivileged_userns\s*=\s*0' "$OUT/upstream-live-apparmor.conf"; then
  apparmor_status='BLOCKED: live-only AppArmor restriction override in installer source'
else
  apparmor_status='UNKNOWN: installed AppArmor policy needs runtime verification'
fi
{
  echo 'OREZ — DEVELOPMENT INSTALLATION SAFETY AUDIT'
  echo "Install source: $install_source"
  echo 'Candidate OREZ installation SquashFS is present for future disposable-VM installer development (not active).'
  echo "AppArmor: $apparmor_status"
  echo 'LUKS2/Btrfs installation and recovery: NOT TESTED'
  echo 'Non-target disk preservation: NOT TESTED'
  echo 'Certified for SSD installation: NO'
} > "$REPORT"
cat "$REPORT"
