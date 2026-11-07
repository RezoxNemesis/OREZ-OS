#!/usr/bin/env bash
# Build the OREZ system layer on a disposable CI builder (GitHub-hosted runner).
#
# The verified Kubuntu SquashFS stays read-only and unmodified. Packages are
# installed through overlayfs with a disk-backed upper directory; only that
# upper directory (additions, replacements and overlay whiteouts) is packed as
# /casper/orez-apps.squashfs. casper stacks it above filesystem.squashfs.
# Runs as root on a throwaway VM; never touches block devices beyond loop mounts.
#
# Usage: sudo bash build/ci-build-layer.sh <verified.iso> <orez-shell.deb> <outdir>
set -Eeuo pipefail
ISO=$(realpath "$1"); DEB=$(realpath "$2"); OUT=$(realpath -m "$3")
REPO_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)"
[[ $(id -u) -eq 0 ]] || { echo 'Must run as root on a disposable builder.' >&2; exit 1; }
[[ ! -e $OUT/orez-apps.squashfs ]] || { echo 'Refusing to replace an existing layer.' >&2; exit 1; }
mkdir -p "$OUT"
W=$(mktemp -d /mnt/orez-layer.XXXXXX)
R=$W/root
mounts=()
domount() { mount "$@"; mounts+=("${@: -1}"); }
cleanup() {
  set +e
  for ((i=${#mounts[@]}-1; i>=0; i--)); do umount -l "${mounts[$i]}" 2>/dev/null; done
}
trap cleanup EXIT
mkdir -p "$W"/{iso,base,upper,work,root}
domount -o loop,ro "$ISO" "$W/iso"
domount -o loop,ro "$W/iso/casper/filesystem.squashfs" "$W/base"
domount -t overlay overlay -o "lowerdir=$W/base,upperdir=$W/upper,workdir=$W/work" "$R"
domount --bind /dev "$R/dev"
domount --bind /dev/pts "$R/dev/pts"
domount -t proc proc "$R/proc"
domount -t sysfs sysfs "$R/sys"
domount -t tmpfs tmpfs "$R/run"
domount -t tmpfs tmpfs "$R/tmp"
mkdir -p "$R/run/systemd/resolve"
cp -L /etc/resolv.conf "$R/run/systemd/resolve/stub-resolv.conf"

# Never start services inside the build root.
printf '#!/bin/sh\nexit 101\n' > "$R/usr/sbin/policy-rc.d"; chmod 0755 "$R/usr/sbin/policy-rc.d"
C() { chroot "$R" env -i PATH=/usr/sbin:/usr/bin:/sbin:/bin LANG=C.UTF-8 DEBIAN_FRONTEND=noninteractive "$@"; }

KVER=$(ls "$R/lib/modules" | sort -V | tail -1)
echo "Live kernel: $KVER" | tee "$OUT/layer-build.log"

# Brave official repository: require the reviewed signing fingerprints.
curl -fsSL https://brave-browser-apt-release.s3.brave.com/brave-browser-archive-keyring.gpg -o "$W/brave.gpg"
python3 - "$REPO_ROOT/image/desktop-packages.json" "$W/brave.gpg" <<'PY'
import json,subprocess,sys
want=set(json.load(open(sys.argv[1]))['brave_key_fingerprints'])
lines=subprocess.check_output(['gpg','--show-keys','--with-colons',sys.argv[2]],text=True).splitlines()
# Primary-key fingerprints are the fpr records immediately after each pub record.
primary={lines[i+1].split(':')[9] for i,l in enumerate(lines[:-1]) if l.startswith('pub:') and lines[i+1].startswith('fpr:')}
if not primary or not primary <= want: sys.exit('Unreviewed Brave primary key(s): '+', '.join(sorted(primary-want)))
print('Brave primary keys verified:', ', '.join(sorted(primary)))
PY
install -D -m 0644 "$W/brave.gpg" "$R/usr/share/keyrings/brave-browser-archive-keyring.gpg"
cat > "$R/etc/apt/sources.list.d/brave-browser-release.sources" <<'EOF'
Types: deb
URIs: https://brave-browser-apt-release.s3.brave.com/
Suites: stable
Components: main
Architectures: amd64
Signed-By: /usr/share/keyrings/brave-browser-archive-keyring.gpg
EOF

C apt-get update 2>&1 | tail -5 | tee -a "$OUT/layer-build.log"

mapfile -t PROFILE < <(python3 -c "import json;print('\n'.join(json.load(open('$REPO_ROOT/image/desktop-packages.json'))['packages']))")
# OREZ performance profile: on-demand game tuning, power profiles, compressed RAM swap.
FEATURES=(gamemode power-profiles-daemon systemd-zram-generator ubuntu-drivers-common)

# NVIDIA: Canonical-built, Canonical-signed kernel modules for the exact live
# kernel (works with Secure Boot; no DKMS, no .run installer). Prefer the open
# kernel modules NVIDIA recommends for Turing/Ampere (RTX 3050 is Ampere).
NV=$(C apt-cache search --names-only "^linux-modules-nvidia-[0-9]+(-open)?-${KVER//./\\.}\$" | awk '{print $1}' \
     | sed -E "s/^linux-modules-nvidia-([0-9]+)(-open)?-.*/\1 \2/" | sort -k1,1n -k2,2r | awk '{print $1 $2}' \
     | grep -v server | tail -1 || true)
NVPKGS=()
if [[ -n $NV ]]; then
  NVPKGS=("linux-modules-nvidia-${NV}-${KVER}" "nvidia-driver-${NV}")
  echo "NVIDIA driver selected: ${NV} for ${KVER}" | tee -a "$OUT/layer-build.log"
else
  echo 'WARNING: no signed NVIDIA modules for this kernel in the archive' | tee -a "$OUT/layer-build.log"
fi

cp "$DEB" "$R/tmp/orez-shell.deb"
set +e
C apt-get install -y --no-install-recommends "${PROFILE[@]}" "${FEATURES[@]}" "${NVPKGS[@]}" /tmp/orez-shell.deb 2>&1 | tee -a "$OUT/apt-install.log" | tail -40
rc=${PIPESTATUS[0]}
set -e
[[ $rc -eq 0 ]] || { echo "apt-get install failed ($rc)"; tail -80 "$OUT/apt-install.log"; exit 1; }
if grep -q 'nvidia-dkms\|Building initial module' "$OUT/apt-install.log"; then
  echo 'DKMS path detected; expected prebuilt signed modules only' >&2; exit 1
fi

# Record the exact package state, then strip build-only state.
C dpkg-query -W -f='${Package} ${Version}\n' > "$OUT/filesystem.manifest"
C dpkg --audit | tee "$OUT/dpkg-audit.txt"
[[ ! -s $OUT/dpkg-audit.txt ]] || { echo 'dpkg audit not clean' >&2; exit 1; }
C apt-get clean
rm -f "$R/usr/sbin/policy-rc.d" "$R/tmp/orez-shell.deb"
rm -rf "$R"/var/lib/apt/lists/* "$R"/var/cache/apt/*.bin "$R"/var/log/apt/* "$R"/var/log/dpkg.log "$R"/root/.cache
# Machine identity must not be baked into the image.
[[ ! -s $R/etc/machine-id ]] || : > "$R/etc/machine-id"

# Unmount everything above the overlay, then the overlay itself, before packing.
for ((i=${#mounts[@]}-1; i>=2; i--)); do umount "${mounts[$i]}"; done
mounts=("${mounts[@]:0:2}")
rm -rf "$W/upper/run" "$W/upper/tmp" "$W/upper/proc" "$W/upper/sys" "$W/upper/dev"
du -sh "$W/upper" | tee -a "$OUT/layer-build.log"
mksquashfs "$W/upper" "$OUT/orez-apps.squashfs" -noappend -no-progress -comp xz -xattrs \
  -all-time 1793923200 -mkfs-time 1793923200 >> "$OUT/layer-build.log"
sha256sum "$OUT/orez-apps.squashfs" | tee "$OUT/orez-apps.squashfs.sha256"
ls -l "$OUT/orez-apps.squashfs"
rm -rf "$W/upper" "$W/work"
