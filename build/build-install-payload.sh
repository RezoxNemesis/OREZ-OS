#!/usr/bin/env bash
# Produce a whitelisted, installation-only OREZ filesystem payload.
# No partitioning, root access, service activation or system modification.
set -Eeuo pipefail
repo="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)"
[[ "$#" -eq 1 ]] || { echo 'Usage: build-install-payload.sh OUTPUT.squashfs' >&2; exit 2; }
out="$1"
command -v mksquashfs >/dev/null || { echo 'mksquashfs is required' >&2; exit 2; }
tmp="$(mktemp -d)"
trap 'rm -rf -- "$tmp"' EXIT
# Explicit allowlist. NEVER include the live-only Calamares stub,
# systemd VM verification units, auto-granted privileges or live overrides.
while IFS= read -r rel; do
  [[ -n "$rel" && "$rel" != \#* ]] || continue
  [[ "$rel" != /* && "$rel" != *'..'* ]] || { echo "Unsafe path: $rel" >&2; exit 2; }
  [[ -f "$repo/overlay/$rel" && ! -L "$repo/overlay/$rel" ]] || { echo "Missing payload source: $rel" >&2; exit 2; }
  ( cd -- "$repo/overlay" && cp --parents -p -- "$rel" "$tmp" )
done < "$repo/image/installer/installed-files.txt"
[[ -f "$tmp/etc/orez-release" && -x "$tmp/usr/bin/orezctl" ]] || { echo 'Missing OREZ identity or CLI' >&2; exit 2; }
for forbidden in "$tmp/usr/bin/calamares" "$tmp/etc/sysctl.d/20-apparmor.conf" "$tmp/usr/lib/systemd/system/orez-live-verify.service" "$tmp/usr/lib/systemd/system/orez-gui-verify.service"; do
  [[ ! -e "$forbidden" ]] || { echo "Unsafe payload: $forbidden" >&2; exit 2; }
done
mkdir -p -- "$(dirname -- "$out")"
mksquashfs "$tmp" "$out" -comp xz -all-root -noappend -no-progress >/dev/null
[[ -s "$out" ]] || { echo 'Empty installation payload' >&2; exit 1; }
echo "OREZ install-only desktop payload generated (NOT installer-certified): $out"
