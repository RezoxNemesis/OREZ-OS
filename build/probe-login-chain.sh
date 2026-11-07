#!/usr/bin/env bash
# OREZ login-chain probe (diagnostic only; no device or host-account changes).
#
# Replays SDDM's Wayland user-session chain inside a read-only Kubuntu base
# with OREZ's overlay/live-owner files layered on top (tmpfs upper layer).
# The real Plasma launcher is replaced only inside the disposable overlay by a
# probe that records its arguments and exits 0, so we learn which script in the
# chain returns 64 before Plasma starts.
#
# Usage: sudo bash build/probe-login-chain.sh <verified-kubuntu.iso> <report-dir>
set -Eeuo pipefail
ISO=$1
OUT=$2
REPO_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)"
[[ $(id -u) -eq 0 ]] || { echo 'Run with sudo (loop/overlay mounts).' >&2; exit 1; }
mkdir -p "$OUT"
WORK=$(mktemp -d /tmp/orez-probe.XXXXXX)
cleanup() {
  set +e
  for m in "$WORK/root/proc" "$WORK/root/dev/pts" "$WORK/root/dev" "$WORK/root" "$WORK/base" "$WORK/iso"; do
    mountpoint -q "$m" && umount -l "$m"
  done
}
trap cleanup EXIT
mkdir -p "$WORK"/{iso,base,upper,work,root,tmpfs}
mount -o loop,ro "$ISO" "$WORK/iso"
mount -o loop,ro "$WORK/iso/casper/filesystem.squashfs" "$WORK/base"
mount -t tmpfs tmpfs "$WORK/tmpfs"
mkdir -p "$WORK/tmpfs/upper" "$WORK/tmpfs/work"
mount -t overlay overlay -o "lowerdir=$WORK/base,upperdir=$WORK/tmpfs/upper,workdir=$WORK/tmpfs/work" "$WORK/root"
R=$WORK/root

set +e  # inventory is best-effort; missing files are reported, not fatal
# Inventory of the exact files SDDM and bash read during a Wayland login.
{
  echo '### /etc/sddm/wayland-session (resolved)'; ls -l "$R/etc/sddm/wayland-session" || true
  cat "$R/etc/sddm/wayland-session" 2>&1 || true
  echo; echo '### SDDM config fragments'; ls -l "$R/etc/sddm.conf.d" "$R/usr/lib/sddm/sddm.conf.d" 2>&1 || true
  cat "$R"/usr/lib/sddm/sddm.conf.d/*.conf "$R"/etc/sddm.conf.d/*.conf 2>/dev/null || true
  echo; echo '### /etc/X11/Xsession.d'; ls -l "$R/etc/X11/Xsession.d" 2>&1 || true
  echo; echo '### /etc/profile.d'; ls -l "$R/etc/profile.d" 2>&1 || true
  echo; echo '### /etc/skel'; ls -la "$R/etc/skel" 2>&1 || true
  echo; echo '### plasma-dbus-run-session-if-needed'; cat "$R/usr/lib/x86_64-linux-gnu/libexec/plasma-dbus-run-session-if-needed" 2>&1 || true
  echo; echo '### plasma-workspace env scripts'; ls -l "$R/etc/xdg/plasma-workspace/env" 2>&1 || true
  echo; echo '### upstream wayland sessions'; ls -l "$R/usr/share/wayland-sessions" 2>&1 || true
  for f in "$R"/usr/share/wayland-sessions/*.desktop; do echo "-- $f"; grep -E '^(Exec|TryExec|Type)=' "$f"; done
  echo; echo '### look-and-feel'; ls "$R/usr/share/plasma/look-and-feel"
  for d in "$R"/usr/share/plasma/look-and-feel/*kubuntu* ; do echo "-- $d"; find "$d" -maxdepth 3 | head -30; cat "$d/contents/defaults" 2>&1; cat "$d/metadata.json" 2>&1 | head -30; done
  echo; echo '### /etc/xdg/kdeglobals'; cat "$R/etc/xdg/kdeglobals" 2>&1
  echo; echo '### /etc/xdg (kde files)'; ls "$R/etc/xdg"
  echo; echo '### plasmarc etc'; cat "$R/etc/xdg/plasmarc" "$R/etc/xdg/kwinrc" "$R/etc/xdg/ksplashrc" 2>&1
  echo; echo '### skel Desktop'; ls -la "$R/etc/skel/Desktop" "$R/etc/skel/.config" 2>&1
  echo; echo '### kubuntu-default-settings'; find "$R/usr/share/kubuntu-default-settings" 2>&1 | head -40
  echo; echo '### kubuntu layout.js'; cat "$R/usr/share/kubuntu-default-settings/layout.js" 2>&1
  echo; echo '### plasma shell layout.js'; cat "$R/usr/share/plasma/shells/org.kde.plasma.desktop/contents/layout.js" 2>&1 | head -80
  echo; echo '### KUBUNTU LAYOUT JS'; cat "$R/usr/share/plasma/look-and-feel/org.kubuntu.desktop/contents/layouts/org.kde.plasma.desktop-layout.js"
  echo; echo '### kf5 kdeglobals'; cat "$R/usr/share/kubuntu-default-settings/kf5-settings/kdeglobals"
  echo; echo '### kf5 plasmarc'; cat "$R/usr/share/kubuntu-default-settings/kf5-settings/plasmarc"
  echo; echo '### who sets XDG_CONFIG_DIRS'; grep -rl "kf5-settings" "$R/etc" "$R/usr/lib/environment.d" "$R/usr/share/plasma" 2>/dev/null | head; grep -rh "kf5-settings" "$R/etc" "$R/usr/lib/environment.d" 2>/dev/null | head -5
  echo; echo '### kickoff favorites'; cat "$R/etc/xdg/kicker-extra-favoritesrc"
  echo; echo '### CALAMARES FILES'
  for f in settings.conf modules/unpackfs.conf modules/shellprocess_fix_oem_uid.conf modules/displaymanager.conf modules/packages.conf modules/bootloader.conf modules/users.conf; do
    echo "===== FILE etc/calamares/$f"; base64 -w0 "$R/etc/calamares/$f"; echo; done
  echo "===== FILE status-sha"; sha256sum "$R/var/lib/dpkg/status"
  echo; echo '### calamares launchers'; ls -l "$R/usr/bin/" | grep -i calamares; cat "$R/usr/bin/calamares-launch"* 2>/dev/null | head -40
  echo; echo '### calamares desktop'; cat "$R/usr/share/applications/kubuntu-calamares.desktop" 2>&1
  echo; echo '### calamares settings + branding'; cat "$R/etc/calamares/settings.conf" 2>&1; ls -R "$R/etc/calamares/branding" 2>&1 | head -30
  echo; echo '### firefox / welcome'; ls "$R/usr/share/applications" | grep -iE "firefox|welcome|kubuntu" ; ls "$R/etc/xdg/autostart" | head -60
} > "$OUT/inventory.txt" 2>&1

set -e
# Apply OREZ's live payload exactly as the live layer would.
cp -a "$REPO_ROOT/overlay/." "$R/"
cp -a "$REPO_ROOT/image/live-owner/." "$R/"
chmod 0755 "$R/usr/lib/orez/orez-session-trace" 2>/dev/null || true

# Probe replaces the Plasma launcher in the disposable upper layer only.
cat > "$R/usr/bin/startplasma-wayland" <<'EOF'
#!/bin/sh
echo "PROBE_REACHED argv=[$*] uid=$(id -u) shell=$SHELL dbus=${DBUS_SESSION_BUS_ADDRESS:+set}"
exit 0
EOF
chmod 0755 "$R/usr/bin/startplasma-wayland"

mount --bind /dev "$R/dev"; mount --bind /dev/pts "$R/dev/pts"; mount -t proc proc "$R/proc"
chroot "$R" /usr/sbin/useradd -m -s /bin/bash -u 1000 orezprobe 2>/dev/null || chroot "$R" /usr/sbin/useradd -m -s /bin/bash orezprobe
mkdir -p "$R/run/user/1000"; chroot "$R" chown orezprobe:orezprobe /run/user/1000; chmod 0700 "$R/run/user/1000"

run_case() {
  local name=$1 cmd=$2 dbus=$3
  local envs=(HOME=/home/orezprobe USER=orezprobe LOGNAME=orezprobe SHELL=/bin/bash
    PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin LANG=C.UTF-8
    XDG_RUNTIME_DIR=/run/user/1000 XDG_SESSION_TYPE=wayland XDG_SESSION_CLASS=user
    XDG_SEAT=seat0 XDG_VTNR=2 XDG_SESSION_DESKTOP=KDE XDG_CURRENT_DESKTOP=KDE)
  [[ $dbus == yes ]] && envs+=(DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus)
  set +e
  env -i "${envs[@]}" chroot --userspec=orezprobe:orezprobe "$R" \
    /bin/sh -x /etc/sddm/wayland-session "$cmd" > "$OUT/$name.log" 2>&1 < /dev/null
  local rc=$?
  set -e
  echo "$name exit=$rc reached=$(grep -c PROBE_REACHED "$OUT/$name.log")" | tee -a "$OUT/SUMMARY.txt"
}
: > "$OUT/SUMMARY.txt"
PLASMA='/usr/lib/x86_64-linux-gnu/libexec/plasma-dbus-run-session-if-needed /usr/bin/startplasma-wayland'
run_case failing-image-exec-dbus-set "$PLASMA" yes
run_case failing-image-exec-dbus-unset "$PLASMA" no
run_case trace-wrapper-dbus-set '/bin/sh /usr/lib/orez/orez-session-trace' yes
run_case plain-true-dbus-set '/bin/true' yes
echo 'Probe complete. Logs are diagnostics, not boot or desktop qualification.' | tee -a "$OUT/SUMMARY.txt"
