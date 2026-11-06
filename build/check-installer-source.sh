#!/usr/bin/env bash
# Inspect actual integrated media without mounting or extracting the whole base.
# Caller-selected checksum binding is not a release-signature verification.
set -Eeuo pipefail
[[ "$#" -ge 1 && "$#" -le 2 && -f "$1" && ! -L "$1" ]] || {
  echo 'Usage: check-installer-source.sh OREZ.iso [expected-sha256]' >&2; exit 2;
}
for tool in xorriso unsquashfs sha256sum python3; do
  command -v "$tool" >/dev/null || { echo "Missing $tool" >&2; exit 2; }
done
ISO="$(realpath "$1")"
ROOT="$(cd -- "$(dirname -- "$0")/.." && pwd -P)"
OUT="${OREZ_INSTALLER_AUDIT_DIR:-$ROOT/dist/installer-source}"
EXPECTED="${2:-$(sha256sum "$ISO" | cut -d ' ' -f 1)}"
python3 "$ROOT/build/inspect-installer-source.py" "$ISO" --sha256 "$EXPECTED" --output "$OUT"
echo 'Certified for SSD installation: NO'
