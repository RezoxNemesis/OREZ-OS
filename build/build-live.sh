#!/usr/bin/env bash
# OREZ OS 0.1.0: Construct a NON-INSTALLABLE live candidate from a signed Kubuntu ISO.
# This script writes only within the configured cache/dist directories; no device access.
set -Eeuo pipefail
umask 022

REPO_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)"
OUTPUT_DIR="${OREZ_OUTPUT_DIR:-$REPO_ROOT/dist}"
CACHE_DIR="${OREZ_CACHE_DIR:-$REPO_ROOT/.cache/orez}"
WORK_DIR="${OREZ_WORK_DIR:-$CACHE_DIR/work}"
IMAGE='kubuntu-26.04.1-desktop-amd64.iso'
UPSTREAM='https://cdimage.ubuntu.com/cdimage/kubuntu/releases/26.04.1/release'
IMAGE_SHA256='831e4d4bb85098339ba43d3502cd6619b27e76daf37246a084cd68a6413090b8'
IMAGE_SIGNING_FPR='843938DF228D22F7B3742BC0D94AA3F0EFE21092'
OUTPUT="$OUTPUT_DIR/OREZ-OS-0.1-live-amd64.iso"

log() { printf '\n[OREZ] %s\n' "$*" >&2; }
fail() { printf '[OREZ ERROR] %s\n' "$*" >&2; exit 1; }
need() { command -v "$1" >/dev/null 2>&1 || fail "Missing tool: $1"; }

[[ "$(uname -s)" = 'Linux' && "$(uname -m)" = 'x86_64' ]] || fail 'This builder requires x86-64 Linux.'
for c in curl gpg gpgv sha256sum awk grep xorriso mksquashfs df stat; do need "$c"; done
[[ "$OUTPUT_DIR" != "$CACHE_DIR" && "$WORK_DIR" != "$OUTPUT_DIR" ]] || fail 'Output, cache and work directories must be separate.'
mkdir -p -- "$OUTPUT_DIR" "$CACHE_DIR" "$WORK_DIR"

# An upstream ISO (5.1 GB) and new output ISO must coexist. Refuse before network usage
# if the runner lacks space. Build intentionally does not auto-remove system software.
free_kib="$(df -Pk "$OUTPUT_DIR" | awk 'NR==2 {print $4}')"
[[ "$free_kib" =~ ^[0-9]+$ ]] || fail 'Cannot determine available disk space.'
if (( free_kib < 11534336 )); then
  fail "Need at least 11 GiB free to start; currently $((free_kib / 1048576)) GiB. Provision a larger runner."
fi

log 'Downloading authentic release metadata and Ubuntu signing keyring'
for f in SHA256SUMS SHA256SUMS.gpg; do
  curl -fLsS --retry 3 "$UPSTREAM/$f" -o "$WORK_DIR/$f"
done
curl -fLsS --retry 3 'https://archive.ubuntu.com/ubuntu/project/ubuntu-archive-keyring.gpg' -o "$WORK_DIR/ubuntu-archive-keyring.gpg"

# The keyring can contain multiple keys. Enforce one specific official CD signing
# fingerprint, including the signature that actually signed SHA256SUMS.
if ! gpg --show-keys --with-colons "$WORK_DIR/ubuntu-archive-keyring.gpg" 2>/dev/null | awk -F: '$1=="fpr" {print toupper($10)}' | grep -Fxq "$IMAGE_SIGNING_FPR"; then
  fail 'The expected Ubuntu CD signing key was not present in the keyring.'
fi
if ! gpgv --status-fd 1 --keyring "$WORK_DIR/ubuntu-archive-keyring.gpg" \
  "$WORK_DIR/SHA256SUMS.gpg" "$WORK_DIR/SHA256SUMS" > "$WORK_DIR/verification.log" 2>&1; then
  fail 'The upstream checksum signature could not be verified.'
fi
if ! grep -Eq "^\[GNUPG:\] VALIDSIG $IMAGE_SIGNING_FPR([[:space:]]|$)" "$WORK_DIR/verification.log"; then
  fail 'Checksums were not signed by the pinned Ubuntu CD key.'
fi
if ! grep -Fxq "$IMAGE_SHA256 *$IMAGE" "$WORK_DIR/SHA256SUMS"; then
  fail 'The official signed checksum no longer matches the locked upstream image.'
fi

SOURCE="${OREZ_UPSTREAM_ISO:-$CACHE_DIR/$IMAGE}"
if [[ ! -f "$SOURCE" ]]; then
  [[ -z "${OREZ_UPSTREAM_ISO:-}" ]] || fail "Provided upstream ISO not found: $SOURCE"
  log 'Downloading 5.1 GB official Kubuntu ISO (cached for later builds)'
  curl -fL --retry 3 --retry-delay 5 "$UPSTREAM/$IMAGE" -o "$SOURCE.part"
  mv -f -- "$SOURCE.part" "$SOURCE"
fi
log 'Verifying upstream ISO against pinned, signature-authenticated SHA-256'
printf '%s  %s\n' "$IMAGE_SHA256" "$SOURCE" | sha256sum -c - >/dev/null || fail 'ISO SHA-256 mismatch. Refusing to remix.'

log 'Inspecting ISO for a compatible casper boot configuration'
rm -f -- "$WORK_DIR/grub.cfg" "$WORK_DIR/zz-orez.squashfs"
xorriso -osirrox on -indev "$SOURCE" -extract /boot/grub/grub.cfg "$WORK_DIR/grub.cfg" >/dev/null 2>&1 || fail 'Cannot inspect upstream GRUB configuration.'
if grep -Eiq 'layerfs-path[= ]' "$WORK_DIR/grub.cfg"; then
  fail 'Explicit casper layering found; this fast remix must be reviewed for compatibility.'
fi
xorriso -indev "$SOURCE" -ls /casper > "$WORK_DIR/upstream-casper-list.txt" 2>&1 || fail 'Cannot inspect upstream casper files.'
grep -Fq 'filesystem.squashfs' "$WORK_DIR/upstream-casper-list.txt" || fail 'Expected casper/filesystem.squashfs missing. Stop rather than guessing.'

log 'Creating small, original OREZ filesystem layer'
stage_dir="$(mktemp -d "$WORK_DIR/overlay-stage.XXXXXX")"
python3 "$REPO_ROOT/build/stage-overlay.py" --source "$REPO_ROOT/overlay" --output "$stage_dir/root"
mksquashfs "$stage_dir/root" "$WORK_DIR/zz-orez.squashfs" -comp xz -all-root -noappend -no-progress > "$WORK_DIR/squashfs.log" 2>&1 || fail 'Failed to construct squashfs layer.'
rm -rf -- "$stage_dir"
[[ -s "$WORK_DIR/zz-orez.squashfs" ]] || fail 'Empty OREZ layer.'

log 'Creating separated OREZ installed-system payload (installer still disabled)'
bash "$REPO_ROOT/build/build-install-payload.sh" "$WORK_DIR/orez-install.squashfs"
[[ -s "$WORK_DIR/orez-install.squashfs" ]] || fail 'Missing installed-system candidate payload.'

log 'Replaying upstream EFI/BIOS boot metadata while adding OREZ layer'
rm -f -- "$OUTPUT.part"
xorriso -indev "$SOURCE" -outdev "$OUTPUT.part" \
  -map "$WORK_DIR/zz-orez.squashfs" /casper/zz-orez.squashfs \
  -map "$WORK_DIR/orez-install.squashfs" /casper/orez-install.squashfs \
  -boot_image any replay -commit > "$WORK_DIR/xorriso.log" 2>&1 \
  || fail "Remix failed. See $WORK_DIR/xorriso.log"
[[ -s "$OUTPUT.part" ]] || fail 'No output ISO written.'
mv -f -- "$OUTPUT.part" "$OUTPUT"

log 'Checking ISO structure and computing digest'
bash "$REPO_ROOT/build/check-iso.sh" "$OUTPUT"
( cd -- "$OUTPUT_DIR" && sha256sum "$(basename "$OUTPUT")" > "$(basename "$OUTPUT").sha256" )
{
  printf 'OREZ build: 0.1.0-dev\n'
  printf 'Stage: live candidate / NOT INSTALLER QUALIFIED\n'
  printf 'Upstream: %s\n' "$IMAGE"
  printf 'Upstream_SHA256: %s\n' "$IMAGE_SHA256"
  printf 'OREZ_SHA256: %s\n' "$(cut -d' ' -f1 "$OUTPUT.sha256")"
  printf 'Source_revision: %s\n' "${GITHUB_SHA:-$(git -C "$REPO_ROOT" rev-parse HEAD 2>/dev/null || printf unknown)}"
  printf 'VM_boot: NOT TESTED\n'
  printf 'Physical_boot: NOT TESTED\n'
} > "$OUTPUT_DIR/build-report.txt"
log "Candidate ISO generated: $OUTPUT"
log 'THIS IS NOT SAFE TO INSTALL. Test live USB or VM boot first.'
