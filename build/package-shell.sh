#!/usr/bin/env bash
# Builds an installable Debian package containing the actual OREZ desktop components.
set -euo pipefail
root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)"
command -v dpkg-deb >/dev/null || { echo 'dpkg-deb is required' >&2; exit 1; }
work="$(mktemp -d)"
trap 'rm -rf -- "$work"' EXIT
# Use the SAME allowlist as the future installed-system SquashFS.
# Never ship VM witness services or live-only installer overrides in host .deb.
while IFS= read -r rel; do
  [[ -n "$rel" && "$rel" != \#* ]] || continue
  [[ "$rel" != /* && "$rel" != *'..'* ]] || { echo "Unsafe path: $rel" >&2; exit 2; }
  [[ -f "$root/overlay/$rel" && ! -L "$root/overlay/$rel" ]] || { echo "Missing payload source: $rel" >&2; exit 2; }
  ( cd -- "$root/overlay" && cp --parents -p -- "$rel" "$work" )
done < "$root/image/installer/installed-files.txt"
# The live-only Calamares safety blocker must NEVER replace Calamares on a normal host.
rm -f -- "$work/usr/bin/calamares" "$work/usr/share/applications/calamares.desktop"
mkdir -p "$work/DEBIAN" "$root/dist"
chmod 0755 "$work/DEBIAN"
chmod g-s "$work/DEBIAN"
cat > "$work/DEBIAN/control" <<'CONTROL'
Package: orez-shell
Version: 0.1.0-1
Section: x11
Priority: optional
Architecture: all
Maintainer: OREZ OS Project <orez@invalid.example>
Depends: plasma-workspace, xdg-utils
Description: OREZ OS first-login styling and read-only diagnostics
 Experimental OREZ shell assets for Kubuntu 26.04.1 and KDE Plasma 6.
 This package does not change the bootloader, disk partitions or security settings.
CONTROL
# No maintainer scripts; installation never executes privileged arbitrary code.
dpkg-deb --build --root-owner-group "$work" "$root/dist/orez-shell_0.1.0-1_all.deb"
dpkg-deb --info "$root/dist/orez-shell_0.1.0-1_all.deb"
if dpkg-deb --contents "$root/dist/orez-shell_0.1.0-1_all.deb" | grep -E '([[:space:]])\./(usr/bin/calamares|usr/share/applications/calamares.desktop|usr/lib/systemd/system/orez-.*verify.service|etc/systemd/system/.*wants/orez-.*verify.service)([[:space:]]|$)' ; then
  echo "Unsafe package: live-only installer override leaked into normal .deb" >&2
  exit 1
fi
