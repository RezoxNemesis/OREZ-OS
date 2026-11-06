#!/usr/bin/env bash
set -Eeuo pipefail
trap 'printf "SESSION FAIL line %s: %s\n" "$LINENO" "$BASH_COMMAND" >&2' ERR
export XDG_RUNTIME_DIR=/tmp/orez-desktop-runtime
mkdir -p "$XDG_RUNTIME_DIR"
chmod 700 "$XDG_RUNTIME_DIR"
export DISPLAY=:99 QT_QPA_PLATFORM=xcb LIBGL_ALWAYS_SOFTWARE=1
Xvfb :99 -screen 0 1440x900x24 -nolisten tcp +extension GLX +render > /evidence/xvfb.log 2>&1 &
xpid=$!
trap 'kill "$xpid" 2>/dev/null || true' EXIT
for _ in $(seq 1 30); do if xdpyinfo >/dev/null 2>&1; then break; fi; sleep 1; done
xdpyinfo >/dev/null
glxinfo -B > /evidence/software-graphics.txt 2>&1
cat /evidence/software-graphics.txt
if [[ "${OREZ_SCENARIO:-desktop}" == capabilities ]]; then
  python3 /input/capabilities.py
  exit
fi
setpriv --no-new-privs kwin_wayland --help > /evidence/kwin-help.txt 2>&1
dbus-run-session -- bash <<'SESSION'
set -Eeuo pipefail
export XDG_CURRENT_DESKTOP=KDE XDG_SESSION_DESKTOP=KDE XDG_SESSION_TYPE=wayland XDG_MENU_PREFIX=plasma-
export QT_ACCESSIBILITY=1 QT_LINUX_ACCESSIBILITY_ALWAYS_ON=1
export QT_QUICK_BACKEND=software
# Ignore privileged file-capability gains rather than granting the container
# CAP_SYS_NICE. Software rendering needs no elevated scheduling privilege.
setpriv --no-new-privs kwin_wayland --x11-display :99 --width 1440 --height 900 --socket wayland-orez --xwayland > /evidence/kwin.log 2>&1 &
kwin=$!
trap 'scrot /evidence/last-frame.png 2>/dev/null || true; kill "$kwin" 2>/dev/null || true' EXIT
for _ in $(seq 1 40); do
  [[ ! -S "$XDG_RUNTIME_DIR/wayland-orez" ]] || break
  kill -0 "$kwin"
  sleep 1
done
test -S "$XDG_RUNTIME_DIR/wayland-orez"
export WAYLAND_DISPLAY=wayland-orez QT_QPA_PLATFORM=wayland
plasmashell --no-respawn > /evidence/plasma.log 2>&1 &
plasma=$!
for _ in $(seq 1 40); do
  if qdbus6 org.kde.plasmashell /PlasmaShell org.kde.PlasmaShell.evaluateScript 'print(desktops().length)' > /evidence/desktop-count.txt 2>/dev/null && grep -Eq '^[1-9][0-9]*$' /evidence/desktop-count.txt; then break; fi
  kill -0 "$plasma"
  sleep 1
done
cat /evidence/desktop-count.txt
grep -Eq '^[1-9][0-9]*$' /evidence/desktop-count.txt
/usr/bin/orez-session-init
sleep 3
DISPLAY=:99 scrot /evidence/01-plasma-desktop.png
qdbus6 org.kde.KWin /KWin org.kde.KWin.supportInformation > /evidence/kwin-support.txt
printf 'PASS: native KWin and Plasma desktop objects exist; screenshot requires review.\n'
if [[ "${OREZ_SCENARIO:-desktop}" == tour ]]; then
  python3 /input/tour-desktop.py "$plasma"
  exit
fi
if [[ "${OREZ_SCENARIO:-desktop}" == connectivity ]]; then
  python3 /input/connectivity.py
  exit
fi
if [[ "${OREZ_SCENARIO:-desktop}" == everyday ]]; then
  python3 /input/everyday.py
  exit
fi
systemsettings > /evidence/settings.log 2>&1 &
dolphin /home/orez-test > /evidence/dolphin.log 2>&1 &
konsole --separate -e bash -c 'orezctl status; printf "\nNative terminal: uname and Python\n"; uname -sr; python3 --version; read -r -t 240' > /evidence/konsole.log 2>&1 &
sleep 8
DISPLAY=:99 scrot /evidence/02-applications.png
ps -u "$(id -u)" -o pid,comm,rss > /evidence/processes.txt
cat /evidence/processes.txt
python3 /input/desktop-interactions.py "$plasma"
SESSION
