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

# The live base lists file:/cdrom as a package source. Use a filtered copy of
# the sources in /tmp (tmpfs, not packed) so the image's own files stay as-is.
mkdir -p "$R/tmp/apt-parts"
for f in "$R"/etc/apt/sources.list.d/*; do
  grep -qi 'cdrom' "$f" || cp "$f" "$R/tmp/apt-parts/"
done
grep -vi '^deb.*cdrom' "$R/etc/apt/sources.list" > "$R/tmp/apt-sources.list" 2>/dev/null || : > "$R/tmp/apt-sources.list"
APTOPT=(-o Dir::Etc::SourceList=/tmp/apt-sources.list -o Dir::Etc::SourceParts=/tmp/apt-parts)
ls "$R/tmp/apt-parts" | tee -a "$OUT/layer-build.log"
C apt-get "${APTOPT[@]}" update 2>&1 | tail -5 | tee -a "$OUT/layer-build.log"
[[ ${PIPESTATUS[0]} -eq 0 ]] || { echo 'apt-get update failed' >&2; exit 1; }

mapfile -t PROFILE < <(python3 -c "import json;print('\n'.join(json.load(open('$REPO_ROOT/image/desktop-packages.json'))['packages']))")
# OREZ performance profile: on-demand game tuning, power profiles, compressed RAM swap.
FEATURES=(gamemode power-profiles-daemon systemd-zram-generator ubuntu-drivers-common)

# NVIDIA: Canonical-built, Canonical-signed kernel modules for the exact live
# kernel (works with Secure Boot; no DKMS, no .run installer).
# The archive moves driver series forward faster than an ISO's kernel, so also
# offer the ISO's own package pool (covered by the signed SHA256SUMS check of
# the whole ISO). apt must find a complete, DKMS-free set before we use it.
mkdir -p "$R/tmp/iso"; mount --bind "$W/iso" "$R/tmp/iso"; mounts+=("$R/tmp/iso")
ls "$W/iso/pool" 2>/dev/null | tee -a "$OUT/layer-build.log"
find "$W/iso/pool" -name '*nvidia*' -printf '%f\n' 2>/dev/null | sort | tee "$OUT/iso-pool-nvidia.txt" | head -40
SUITE=$(sed -n 's/^Suite: //p' "$W/iso/dists/"*/Release 2>/dev/null | head -1)
COMPS=$(sed -n 's/^Components: //p' "$W/iso/dists/"*/Release 2>/dev/null | head -1)
if [[ -n $SUITE && -n $COMPS ]]; then
  # trusted=yes is justified only because the entire ISO, including this pool,
  # was verified against Ubuntu's signed SHA256SUMS before this script ran.
  printf 'Types: deb\nURIs: file:/tmp/iso\nSuites: %s\nComponents: %s\nTrusted: yes\n' "$SUITE" "$COMPS" > "$R/tmp/apt-parts/iso-pool.sources"
  C apt-get "${APTOPT[@]}" update 2>&1 | tail -3 | tee -a "$OUT/layer-build.log"
fi
NVPKGS=()
mapfile -t CANDS < <(C apt-cache "${APTOPT[@]}" search --names-only "^linux-modules-nvidia-[0-9]+(-open)?-${KVER//./\\.}\$" \
  | awk '{print $1}' | sed -E "s/^linux-modules-nvidia-(.*)-${KVER//./\\.}\$/\1/" | grep -v server | sort -t- -k1,1nr)
echo "Signed module series for ${KVER}: ${CANDS[*]:-none}" | tee -a "$OUT/layer-build.log"
for NV in "${CANDS[@]}"; do
  try=("linux-modules-nvidia-${NV}-${KVER}" "nvidia-driver-${NV}")
  if C apt-get "${APTOPT[@]}" -s install --no-install-recommends "${try[@]}" > "$OUT/nvidia-sim-${NV}.txt" 2>&1 \
     && ! grep -q '^Inst nvidia-dkms' "$OUT/nvidia-sim-${NV}.txt"; then
    NVPKGS=("${try[@]}")
    echo "NVIDIA driver selected: ${NV} with Canonical-signed modules for ${KVER}" | tee -a "$OUT/layer-build.log"
    grep -E '^Inst (nvidia-driver|linux-modules-nvidia|nvidia-kernel-common|libnvidia-gl)' "$OUT/nvidia-sim-${NV}.txt" | tee -a "$OUT/layer-build.log"
    break
  fi
  echo "series ${NV}: no DKMS-free set ($(grep -m1 -E '^E:|unmet|not available' "$OUT/nvidia-sim-${NV}.txt"))" | tee -a "$OUT/layer-build.log"
done
[[ ${#NVPKGS[@]} -gt 0 ]] || echo 'WARNING: no DKMS-free signed NVIDIA set for the live kernel; first-boot driver setup will install it' | tee -a "$OUT/layer-build.log"

cp "$DEB" "$R/tmp/orez-shell.deb"
set +e
C apt-get "${APTOPT[@]}" install -y --no-install-recommends "${PROFILE[@]}" "${FEATURES[@]}" "${NVPKGS[@]}" /tmp/orez-shell.deb 2>&1 | tee -a "$OUT/apt-install.log" | tail -40
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
