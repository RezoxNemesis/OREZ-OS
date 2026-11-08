#!/usr/bin/env bash
# Build the OREZ 0.2 update payload on a disposable CI runner.
#
# The starting point is the exact OREZ 0.1 image (base + OREZ system layer),
# with the live-only packages removed the way the installer removes them, so the
# package plan matches an installed OREZ 0.1 PC. Ubuntu's signed InRelease files
# and package indexes are copied unchanged; only the .deb files the plan needs
# are added. On the PC, gpgv and apt verify everything against the Ubuntu
# archive keyring that is already installed — no new trust is introduced.
# Never touches block devices beyond read-only loop mounts.
#
# Usage: sudo bash build/ci-build-update.sh <OREZ-0.1.iso> <orez-shell.deb> <outdir>
set -Eeuo pipefail
ISO=$(realpath "$1"); DEB=$(realpath "$2"); OUT=$(realpath -m "$3")
REPO_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)"
[[ $(id -u) -eq 0 ]] || { echo 'Must run as root on a disposable builder.' >&2; exit 1; }
ARCHIVE=http://archive.ubuntu.com/ubuntu
SUITES=(resolute resolute-updates resolute-security)
COMPS=(main restricted universe multiverse)
ARCHES=(amd64 i386)
P=$OUT/payload/orez-update
M=$P/mirror
mkdir -p "$M" "$OUT"
LOGF=$OUT/update-build.log
log() { echo "$*" | tee -a "$LOGF"; }

W=$(mktemp -d /mnt/orez-update.XXXXXX); R=$W/root
mounts=()
domount() { mount "$@"; mounts+=("${@: -1}"); }
cleanup() { set +e; for ((i=${#mounts[@]}-1; i>=0; i--)); do umount -l "${mounts[$i]}" 2>/dev/null; done; }
trap cleanup EXIT
mkdir -p "$W"/{iso,base,layer,upper,work,root}
domount -o loop,ro "$ISO" "$W/iso"
domount -o loop,ro "$W/iso/casper/filesystem.squashfs" "$W/base"
domount -o loop,ro "$W/iso/casper/orez-apps.squashfs" "$W/layer"
domount -t overlay overlay -o "lowerdir=$W/layer:$W/base,upperdir=$W/upper,workdir=$W/work" "$R"
for d in dev dev/pts; do domount --bind "/$d" "$R/$d"; done
domount -t proc proc "$R/proc"; domount -t sysfs sysfs "$R/sys"
domount -t tmpfs tmpfs "$R/run"; domount -t tmpfs tmpfs "$R/tmp"
mkdir -p "$R/run/systemd/resolve"; cp -L /etc/resolv.conf "$R/run/systemd/resolve/stub-resolv.conf"
printf '#!/bin/sh\nexit 101\n' > "$R/usr/sbin/policy-rc.d"; chmod 0755 "$R/usr/sbin/policy-rc.d"
C() { chroot "$R" env -i PATH=/usr/sbin:/usr/bin:/sbin:/bin LANG=C.UTF-8 DEBIAN_FRONTEND=noninteractive "$@"; }

log "Start: $(grep PRETTY_NAME "$R/usr/lib/os-release") kernel $(ls "$R/lib/modules" | sort -V | tail -1)"

# 1. Emulate the installed system: remove what Calamares removes after installing.
mapfile -t LIVEONLY < <(C python3 - <<'PY'
import glob, yaml
names = set()
for f in glob.glob('/etc/calamares/modules/packages*.conf') + glob.glob('/usr/share/calamares/modules/packages*.conf'):
    try:
        conf = yaml.safe_load(open(f)) or {}
    except Exception:
        continue
    for op in conf.get('operations', []) or []:
        for key in ('remove', 'try_remove'):
            for p in op.get(key, []) or []:
                names.add(p if isinstance(p, str) else p.get('package', ''))
print('\n'.join(sorted(n for n in names if n)))
PY
)
log "Installer removes: ${LIVEONLY[*]:-none}"
if ((${#LIVEONLY[@]})); then
  installed=()
  for p in "${LIVEONLY[@]}"; do C dpkg-query -W -f='${db:Status-Status}' "$p" 2>/dev/null | grep -qx installed && installed+=("$p"); done
  ((${#installed[@]})) && C apt-get -y -q --purge remove "${installed[@]}" >> "$LOGF" 2>&1 || true
fi

# 2. Ubuntu's signed indexes, unchanged.
KEYRING=$R/usr/share/keyrings/ubuntu-archive-keyring.gpg
for s in "${SUITES[@]}"; do
  d=$M/dists/$s; mkdir -p "$d"
  curl -fsS --retry 3 -o "$d/InRelease" "$ARCHIVE/dists/$s/InRelease"
  gpgv --keyring "$KEYRING" "$d/InRelease" 2>>"$LOGF" || { echo "Bad signature on $s" >&2; exit 1; }
  for c in "${COMPS[@]}"; do for a in "${ARCHES[@]}"; do
    rel="$c/binary-$a/Packages.xz"
    line=$(awk -v f="$rel" '/^SHA256:/{s=1;next} /^[A-Za-z]/{s=0} s && $3==f {print $1, $2}' "$d/InRelease")
    [[ -n $line ]] || { log "missing $s/$rel in InRelease"; continue; }
    mkdir -p "$d/$c/binary-$a"
    curl -fsS --retry 3 -o "$d/$rel" "$ARCHIVE/dists/$s/$rel"
    [[ $(sha256sum < "$d/$rel" | cut -d' ' -f1) == "${line%% *}" ]] || { echo "Index hash mismatch $s/$rel" >&2; exit 1; }
  done; done
  log "Indexes for $s verified ($(grep -m1 '^Date:' "$d/InRelease"))"
done

# 3. Resolve with exactly the options the PC-side updater uses.
mkdir -p "$R/tmp/mirror"; domount --bind "$M" "$R/tmp/mirror"
mkdir -p "$R/tmp/apt/empty.d" "$R/tmp/apt/lists/partial" "$R/tmp/apt/archives/partial"
for s in "${SUITES[@]}"; do
  echo "deb [signed-by=/usr/share/keyrings/ubuntu-archive-keyring.gpg arch=amd64,i386] file:/tmp/mirror $s ${COMPS[*]}"
done > "$R/tmp/apt/sources.list"
echo "deb [signed-by=/usr/share/keyrings/claude-desktop-archive-keyring.asc arch=amd64] file:/tmp/claude stable main" >> "$R/tmp/apt/sources.list"
# Same private configuration file the PC-side updater writes (via APT_CONFIG, so
# /etc/apt/apt.conf.d is not read and only Packages indexes are fetched).
: > "$R/tmp/apt/empty.conf"
cat > "$R/tmp/apt/apt.conf" <<'EOF'
Dir::Etc::Main "/tmp/apt/empty.conf";
Dir::Etc::Parts "/tmp/apt/empty.d";
Dir::Etc::SourceList "/tmp/apt/sources.list";
Dir::Etc::SourceParts "/tmp/apt/empty.d";
Dir::State::Lists "/tmp/apt/lists";
Dir::Cache "/tmp/apt";
Dir::Cache::Archives "/tmp/apt/archives";
Acquire::Languages "none";
Acquire::By-Hash "no";
APT::Sandbox::User "root";
EOF
APTOPT=()
C() { chroot "$R" env -i PATH=/usr/sbin:/usr/bin:/sbin:/bin LANG=C.UTF-8 DEBIAN_FRONTEND=noninteractive APT_CONFIG=/tmp/apt/apt.conf "$@"; }

# Claude desktop app: Anthropic's signed apt repository, mirrored the same way.
CM=$P/claude; CLAUDE_REPO=https://downloads.claude.ai/claude-desktop/apt/stable
CLAUDE_FPR=31DDDE24DDFAB679F42D7BD2BAA929FF1A7ECACE
mkdir -p "$CM/dists/stable"
curl -fsS --retry 3 -o "$CM/key.asc" https://downloads.claude.ai/claude-desktop/key.asc
fpr=$(gpg --batch --no-default-keyring --with-colons --show-keys "$CM/key.asc" | awk -F: '/^pub/{p=1;next} p&&/^fpr/{print $10;p=0}')
[[ $fpr == "$CLAUDE_FPR" ]] || { echo "Unexpected Claude signing key: $fpr" >&2; exit 1; }
gpg --batch --yes --no-default-keyring --dearmor -o "$W/claude.gpg" "$CM/key.asc"
curl -fsS --retry 3 -o "$CM/dists/stable/InRelease" "$CLAUDE_REPO/dists/stable/InRelease"
gpgv --keyring "$W/claude.gpg" "$CM/dists/stable/InRelease" 2>>"$LOGF" || { echo 'Claude index signature invalid' >&2; exit 1; }
for f in main/binary-amd64/Packages.xz main/binary-amd64/Packages.gz main/binary-amd64/Packages; do
  line=$(awk -v f="$f" '/^SHA256:/{s=1;next} /^[A-Za-z]/{s=0} s && $3==f {print $1}' "$CM/dists/stable/InRelease")
  [[ -n $line ]] || continue
  mkdir -p "$CM/dists/stable/main/binary-amd64"
  curl -fsS --retry 3 -o "$CM/dists/stable/$f" "$CLAUDE_REPO/dists/stable/$f"
  [[ $(sha256sum < "$CM/dists/stable/$f" | cut -d' ' -f1) == "$line" ]] || { echo "Claude index hash mismatch $f" >&2; exit 1; }
done
ls "$CM/dists/stable/main/binary-amd64" | tee -a "$LOGF"
install -D -m 0644 "$CM/key.asc" "$R/usr/share/keyrings/claude-desktop-archive-keyring.asc"
mkdir -p "$R/tmp/claude"; domount --bind "$CM" "$R/tmp/claude"
log "Claude desktop repository verified (key $CLAUDE_FPR)"
C dpkg --add-architecture i386
C apt-get update 2>&1 | tail -4 | tee -a "$LOGF"
[[ ${PIPESTATUS[0]} -eq 0 ]] || { echo 'apt update against the mirror failed' >&2; exit 1; }

# NVIDIA: ask Ubuntu's own tool what it recommends for an RTX 3050 (GA107, 10de:2582).
mkdir -p "$R/tmp/fakesys/devices/pci0000:00/0000:01:00.0"
echo 'pci:v000010DEd00002582sv00001458sd00004139bc03sc00i00' > "$R/tmp/fakesys/devices/pci0000:00/0000:01:00.0/modalias"
echo 0x10de > "$R/tmp/fakesys/devices/pci0000:00/0000:01:00.0/vendor"
echo 0x030000 > "$R/tmp/fakesys/devices/pci0000:00/0000:01:00.0/class"
NV=$(chroot "$R" env -i PATH=/usr/sbin:/usr/bin:/sbin:/bin LANG=C.UTF-8 APT_CONFIG=/tmp/apt/apt.conf \
     UBUNTU_DRIVERS_SYS_DIR=/tmp/fakesys ubuntu-drivers devices 2>>"$LOGF" | tee -a "$LOGF" \
     | sed -nE 's/^driver *: nvidia-driver-([0-9]+(-open)?) .*recommended.*/\1/p' | head -1)
if [[ -z $NV ]]; then
  NV=$(C apt-cache pkgnames linux-modules-nvidia- | sed -nE 's/^linux-modules-nvidia-([0-9]+-open)-generic$/\1/p' | sort -V | tail -1)
  log "ubuntu-drivers gave no recommendation; newest open series with signed generic modules: $NV"
else
  log "ubuntu-drivers recommends: nvidia-driver-$NV"
fi
[[ -n $NV ]] || { echo 'No NVIDIA series found' >&2; exit 1; }
NVPKGS=("nvidia-driver-$NV" "linux-modules-nvidia-$NV-generic" "libnvidia-gl-${NV%-open}:i386")
BASE=(wine wine64 wine32:i386 winetricks lutris mangohud vulkan-tools libvulkan1:i386 mesa-vulkan-drivers:i386 libgamemode0:i386 gamemode)
STEAM=(steam-installer)
CLAUDE=(claude-desktop)
cp "$DEB" "$R/tmp/orez-shell.deb"
ALL=("${BASE[@]}" "${NVPKGS[@]}" "${STEAM[@]}" "${CLAUDE[@]}" /tmp/orez-shell.deb)

C apt-get -s install -y "${ALL[@]}" > "$OUT/plan.txt" 2>&1 || { tail -40 "$OUT/plan.txt"; echo 'Plan failed' >&2; exit 1; }
grep -E '^Inst (nvidia-dkms|dkms )' "$OUT/plan.txt" && { echo 'DKMS in plan' >&2; exit 1; }
grep -E '^Remv ' "$OUT/plan.txt" | tee -a "$LOGF" || true
log "Plan: $(grep -c '^Inst ' "$OUT/plan.txt") packages"
grep -E '^Inst (linux-image|linux-modules-nvidia|nvidia-driver|steam|wine|lutris|claude)' "$OUT/plan.txt" | tee -a "$LOGF"

# 4. Fetch exactly the planned .debs from Ubuntu into the mirror's pool, hash-checked.
C apt-get install -y --print-uris -qq "${ALL[@]}" > "$OUT/uris.txt"
total=0
while read -r uri name size hash; do
  uri=${uri//\'/}
  if [[ $uri == file:/tmp/mirror/pool/* ]]; then rel=${uri#file:/tmp/mirror/}; dst=$M/$rel; src=$ARCHIVE/$rel
  elif [[ $uri == file:/tmp/claude/pool/* ]]; then rel=${uri#file:/tmp/claude/}; dst=$CM/$rel; src=$CLAUDE_REPO/$rel
  else continue; fi
  mkdir -p "$(dirname "$dst")"
  curl -fsS --retry 3 -o "$dst" "$src"
  [[ $(sha256sum < "$dst" | cut -d' ' -f1) == "${hash#SHA256:}" ]] || { echo "Hash mismatch for $rel" >&2; exit 1; }
  total=$((total+size))
done < "$OUT/uris.txt"
log "Fetched $(grep -c pool/ "$OUT/uris.txt") packages, $((total/1048576)) MiB"

# 5. The finished mirror must satisfy every option the owner can choose, offline.
rm -rf "$R/tmp/apt/lists" && mkdir -p "$R/tmp/apt/lists/partial"
C apt-get update > /dev/null
for set in "base" "base+nvidia" "base+steam" "base+claude" "base+nvidia+steam+claude"; do
  pk=("${BASE[@]}" /tmp/orez-shell.deb)
  [[ $set == *nvidia* ]] && pk+=("${NVPKGS[@]}")
  [[ $set == *steam* ]] && pk+=("${STEAM[@]}")
  [[ $set == *claude* ]] && pk+=("${CLAUDE[@]}")
  C apt-get install -y --download-only "${pk[@]}" > "$OUT/check-$set.txt" 2>&1 \
    || { tail -20 "$OUT/check-$set.txt"; echo "Offline mirror incomplete for $set" >&2; exit 1; }
  log "Offline check passed: $set"
  rm -f "$R"/tmp/apt/archives/*.deb
done

# Steam licence question names (asked of the owner in the OREZ Update window).
STEAMDEB=$(find "$M/pool" -name 'steam-installer_*_amd64.deb' | head -1)
mkdir -p "$W/steamctl"; dpkg-deb -e "$STEAMDEB" "$W/steamctl"
DEBCONF=$(python3 - "$W/steamctl/templates" <<'PY'
import json, re, sys
out = []
try:
    blocks = open(sys.argv[1]).read().split('\n\n')
except OSError:
    blocks = []
for b in blocks:
    t = re.search(r'^Template: (\S+)', b, re.M); ty = re.search(r'^Type: (\S+)', b, re.M)
    if not t or not ty: continue
    if ty.group(1) == 'select':
        ch = re.search(r'^(?:__)?Choices(?:-C)?: (.+)$', b, re.M)
        agree = [c.strip() for c in ch.group(1).split(',')] if ch else []
        agree = [c for c in agree if 'AGREE' in c.upper() and 'DECLINE' not in c.upper() and 'NOT' not in c.upper()]
        if agree: out.append(f'steam-installer {t.group(1)} select {agree[0]}')
    elif ty.group(1) in ('note', 'boolean') and 'license' in t.group(1):
        out.append(f'steam-installer {t.group(1)} {ty.group(1)} ' + ('true' if ty.group(1) == 'boolean' else ''))
print(json.dumps(out))
PY
)
log "Steam debconf answers: $DEBCONF"

# 6. Payload: OREZ files, manifest, checksums.
cp "$DEB" "$P/"
install -m 0644 "$REPO_ROOT/overlay/usr/lib/orez/update_apply.py" "$REPO_ROOT/overlay/usr/lib/orez/update_ui.py" "$P/"
KNEW=$(grep -oE '^Inst linux-image-[0-9][^ ]*' "$OUT/plan.txt" | sed 's/^Inst linux-image-//' | head -1)
python3 - "$P/update.json" "$NV" "$(basename "$DEB")" "$DEBCONF" "${KNEW:-unchanged}" "${BASE[*]}" "${NVPKGS[*]}" "${STEAM[*]}" "${OREZ_SOURCE_COMMIT:-unknown}" "${CLAUDE[*]}" <<'PY'
import json, sys
path, nv, deb, debconf, kernel, base, nvp, steam, commit, claude = sys.argv[1:]
m = {
 'schema': 1, 'version': '0.2', 'from_versions': ['0.1'],
 'suites': ['resolute', 'resolute-updates', 'resolute-security'],
 'components': ['main', 'restricted', 'universe', 'multiverse'],
 'packages': base.split(), 'nvidia_packages': nvp.split(), 'nvidia_series': nv,
 'steam_packages': steam.split(), 'claude_packages': claude.split(), 'steam_debconf': json.loads(debconf), 'orez_shell': deb,
 'kernel_after_update': kernel, 'source_commit': commit,
 'summary': [
  'Windows games and apps: Steam with Proton, Wine (double-click .exe files) and Lutris for Epic, EA, Ubisoft and Rockstar launchers',
  f'NVIDIA RTX graphics driver {nv} (Canonical-signed, works with Secure Boot), plus 32-bit game libraries',
  'Game tools: GameMode performance mode and the MangoHud FPS overlay',
  'Claude desktop app (official from Anthropic: chat, Cowork and Claude Code; later versions arrive with normal system updates)',
  'OREZ Update: install future OREZ updates from a USB in one window',
  'Latest Ubuntu security fixes for the updated components' + (f' and Linux kernel {kernel}' if kernel != 'unchanged' else ''),
 ]}
open(path, 'w').write(json.dumps(m, indent=1) + '\n')
PY
cat > "$P/README.txt" <<'EOF'
OREZ OS 0.2 update
==================
1. On your installed OREZ OS 0.1 PC, plug in this USB and open it once in Dolphin.
2. Open Konsole and run:
       python3 /media/$USER/OREZ_UPDATE/orez-update/update_ui.py
3. Choose the options, press "Install update", enter your password, then restart.
After this update, future updates open from the menu: OREZ Update.
EOF
(cd "$P" && find . -type f ! -name SHA256SUMS -printf '%P\n' | LC_ALL=C sort | xargs -d '\n' sha256sum) > "$OUT/SHA256SUMS.tmp"
mv "$OUT/SHA256SUMS.tmp" "$P/SHA256SUMS"
du -sh "$P" | tee -a "$LOGF"
cat "$P/update.json" | tee -a "$LOGF"
