#!/usr/bin/env bash
# Real X11 application rendering in a disposable container; NOT a booted OS.
set -euo pipefail
[[ -f /.dockerenv && "${OREZ_DISPOSABLE_TEST:-}" == 1 ]] || exit 2
mkdir -p /evidence/native
chown orez-test:orez-test /evidence/native
sudo -u orez-test -H bash <<'SESSION'
set -euo pipefail
export DISPLAY=:99 XDG_RUNTIME_DIR=/tmp/orez-runtime-1500
mkdir -p "$XDG_RUNTIME_DIR"
chmod 700 "$XDG_RUNTIME_DIR"
Xvfb :99 -screen 0 1440x900x24 -nolisten tcp > /evidence/native/xvfb.log 2>&1 &
xpid=$!
trap 'kill "$xpid" 2>/dev/null || true' EXIT
for _ in $(seq 1 30); do xdpyinfo >/dev/null 2>&1 && break; sleep 1; done
xdpyinfo >/dev/null
dbus-run-session -- bash <<'APPS'
set -euo pipefail
export QT_QPA_PLATFORM=xcb QT_QUICK_BACKEND=software
systemsettings > /evidence/native/systemsettings.log 2>&1 &
app=$!
trap 'kill "$app" 2>/dev/null || true' EXIT
found=0
for _ in $(seq 1 30); do
    if xdotool search --onlyvisible --class systemsettings >/dev/null 2>&1; then found=1; break; fi
    kill -0 "$app"
    sleep 1
done
[[ "$found" == 1 ]]
sleep 2
xdotool search --onlyvisible --class systemsettings getwindowname > /evidence/native/window-titles.txt
scrot /evidence/native/kde-systemsettings.png
APPS
SESSION
printf 'PASS: actual native KDE System Settings window rendered in Xvfb; screenshot saved.\n'
