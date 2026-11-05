#!/usr/bin/env bash
set -Eeuo pipefail
trap 'printf "FAIL line %s: %s\n" "$LINENO" "$BASH_COMMAND" >&2' ERR
[[ -f /.dockerenv && "${OREZ_DISPOSABLE_TEST:-}" == 1 ]] || exit 2
mkdir -p /evidence
install -d -m 1777 /tmp/.X11-unix
printf 'NATIVE DESKTOP TEST: isolated Ubuntu container, not an ISO boot or hardware certification.\n'
cat /etc/os-release
apt-get -y --no-install-recommends -o 'Dpkg::Options::=--path-include=/usr/share/doc/orez/*' install /input/orez-shell.deb > /evidence/package-install.log 2>&1
dpkg-query -W -f='${Package} ${Version}\n' orez-shell kwin-wayland plasma-workspace dolphin konsole blender ffmpeg > /evidence/versions.txt
cat /evidence/versions.txt
getcap /usr/bin/kwin_wayland > /evidence/kwin-file-capabilities.txt
cat /evidence/kwin-file-capabilities.txt
if [[ "${OREZ_SCENARIO:-desktop}" != capabilities ]]; then
  # Drop a privilege from this private test container. Do NOT grant SYS_NICE,
  # alter host policy, or put this change in the OREZ image/package.
  sha256sum /usr/bin/kwin_wayland > /evidence/kwin-code-before.sha256
  setcap -r /usr/bin/kwin_wayland
  getcap /usr/bin/kwin_wayland > /evidence/kwin-file-capabilities-after.txt
  sha256sum --check /evidence/kwin-code-before.sha256
  printf 'Test fixture only: removed KWin realtime-scheduling file capability; executable bytes unchanged.\n'
fi
chown -R orez-test:orez-test /evidence
chmod 0755 /input
chmod 0644 /input/*
runuser -u orez-test -- env HOME=/home/orez-test LANG=C.UTF-8 \
  OREZ_SCENARIO="${OREZ_SCENARIO:-desktop}" OREZ_RENDERER="${OREZ_RENDERER:-software}" \
  bash /input/desktop-session.sh
