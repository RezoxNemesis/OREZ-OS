#!/usr/bin/env bash
# Builds an installable Debian package containing the actual OREZ desktop components.
set -euo pipefail
root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)"
command -v dpkg-deb >/dev/null || { echo 'dpkg-deb is required' >&2; exit 1; }
temporary="$(mktemp -d)"
trap 'rm -rf -- "$temporary"' EXIT
work="$temporary/payload"
# Use the SAME allowlist as the future installed-system SquashFS.
# Never ship VM witness services or live-only installer overrides in host .deb.
python3 "$root/build/stage-overlay.py" --source "$root/overlay" \
  --manifest "$root/image/installer/installed-files.txt" --output "$work"
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
Depends: plasma-workspace, systemsettings, kdeconnect, xdg-utils, python3, kdialog, konsole
Suggests: default-jre-headless, plasma-nm, bluedevil, bluez-obexd, kio-extras, scrcpy
Description: OREZ desktop assets, diagnostics and optional Android development manager
 Experimental OREZ shell assets for Kubuntu 26.04.1 and KDE Plasma 6.
 This package does not change the bootloader, disk partitions or security settings.
CONTROL
chmod 0644 "$work/DEBIAN/control"
# No maintainer scripts; installation never executes privileged arbitrary code.
dpkg-deb --build --root-owner-group "$work" "$root/dist/orez-shell_0.1.0-1_all.deb"
dpkg-deb --info "$root/dist/orez-shell_0.1.0-1_all.deb"
if dpkg-deb --contents "$root/dist/orez-shell_0.1.0-1_all.deb" | grep -E '([[:space:]])\./(usr/bin/calamares|usr/share/applications/calamares.desktop|usr/lib/systemd/system/orez-.*verify.service|etc/systemd/system/.*wants/orez-.*verify.service)([[:space:]]|$)' ; then
  echo "Unsafe package: live-only installer override leaked into normal .deb" >&2
  exit 1
fi
