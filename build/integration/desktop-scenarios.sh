#!/usr/bin/env bash
set -Eeuo pipefail
trap 'printf "FAIL line %s: %s\n" "$LINENO" "$BASH_COMMAND" >&2' ERR
[[ -f /.dockerenv && "${OREZ_DISPOSABLE_TEST:-}" == 1 ]] || exit 2
mkdir -p /evidence
install -d -m 1777 /tmp/.X11-unix
printf 'NATIVE DESKTOP TEST: isolated Ubuntu container, not an ISO boot or hardware certification.\n'
cat /etc/os-release
if [[ "${OREZ_SCENARIO:-desktop}" == native-upgrade ]]; then
  python3 /input/native-upgrade.py
  exit
fi
apt-get -y --no-install-recommends -o 'Dpkg::Options::=--path-include=/usr/share/doc/orez/*' install /input/orez-shell.deb > /evidence/package-install.log 2>&1
dpkg-query -W -f='${Package} ${Version}\n' orez-shell kwin-wayland plasma-workspace dolphin konsole blender ffmpeg > /evidence/versions.txt
cat /evidence/versions.txt
if [[ "${OREZ_SCENARIO:-desktop}" == connectivity ]]; then
  install -d /run/dbus
  dbus-daemon --system --fork --nopidfile
  # Private fixture bus and manager. Never manage even a container interface.
  cat > /tmp/orez-nm-test.conf <<'NMCONF'
[main]
plugins=keyfile
no-auto-default=*
[keyfile]
unmanaged-devices=interface-name:*
[connectivity]
enabled=false
NMCONF
  NetworkManager --no-daemon --config=/tmp/orez-nm-test.conf > /evidence/networkmanager.log 2>&1 &
  for attempt in $(seq 1 20); do
    if nmcli -t -f STATE general > /evidence/network-state.txt 2>&1; then break; fi
    sleep .5
  done
  nmcli -t -f DEVICE,TYPE,STATE device status > /evidence/network-devices.txt
  for daemon in /usr/libexec/bluetooth/bluetoothd /usr/lib/bluetooth/bluetoothd; do
    if [[ -x "$daemon" ]]; then
      "$daemon" --nodetach > /evidence/bluetoothd.log 2>&1 &
      break
    fi
  done
fi
getcap /usr/bin/kwin_wayland > /evidence/kwin-file-capabilities.txt
cat /evidence/kwin-file-capabilities.txt
if [[ "${OREZ_SCENARIO:-desktop}" != capabilities ]]; then
  # Drop a privilege from this private test container. Do NOT grant SYS_NICE,
  # alter host policy, or put this change in the OREZ image/package.
  sha256sum /usr/bin/kwin_wayland > /evidence/kwin-code-before.sha256
  if [[ -s /evidence/kwin-file-capabilities.txt ]]; then
    setcap -r /usr/bin/kwin_wayland
  fi
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
