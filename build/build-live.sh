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
SOURCE="${OREZ_UPSTREAM_ISO:-$CACHE_DIR/$IMAGE}"

log() { printf '\n[OREZ] %s\n' "$*" >&2; }
fail() { printf '[OREZ ERROR] %s\n' "$*" >&2; exit 1; }
need() { command -v "$1" >/dev/null 2>&1 || fail "Missing tool: $1"; }

[[ "$(uname -s)" = 'Linux' && "$(uname -m)" = 'x86_64' ]] || fail 'This builder requires x86-64 Linux.'
for c in curl gpg gpgv sha256sum awk grep xorriso mksquashfs zstd df stat; do need "$c"; done
[[ "$OUTPUT_DIR" != "$CACHE_DIR" && "$WORK_DIR" != "$OUTPUT_DIR" ]] || fail 'Output, cache and work directories must be separate.'
mkdir -p -- "$OUTPUT_DIR" "$CACHE_DIR" "$WORK_DIR"

# Reserve 11 GiB for both images and scratch space, less already allocated input
# bytes (capped at 5 GiB). A partial download is untrusted until the full signed
# digest passes, but its existing bytes need not be allocated twice on resume.
free_kib="$(df -Pk "$OUTPUT_DIR" | awk 'NR==2 {print $4}')"
[[ "$free_kib" =~ ^[0-9]+$ ]] || fail 'Cannot determine available disk space.'
input_credit_kib=0
cached_input=''
if [[ -f "$SOURCE" ]]; then cached_input="$SOURCE"
elif [[ -z "${OREZ_UPSTREAM_ISO:-}" && -f "$SOURCE.part" ]]; then cached_input="$SOURCE.part"
fi
# Credit only allocated bytes on the SAME filesystem as the output. A sparse
# file or a cache on another volume must not weaken the output-space reserve.
if [[ -n "$cached_input" && "$(stat -c %d "$cached_input")" == "$(stat -c %d "$OUTPUT_DIR")" ]]; then
  input_credit_kib=$(( $(stat -c %b "$cached_input") / 2 ))
  (( input_credit_kib <= 5242880 )) || input_credit_kib=5242880
fi
required_kib=$((11534336 - input_credit_kib))
if (( free_kib < required_kib )); then
  fail "Need ${required_kib} KiB free after cached-input credit; currently ${free_kib} KiB. Provision a larger runner."
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

if [[ ! -f "$SOURCE" ]]; then
  [[ -z "${OREZ_UPSTREAM_ISO:-}" ]] || fail "Provided upstream ISO not found: $SOURCE"
  log 'Downloading 5.1 GB official Kubuntu ISO (cached for later builds)'
  # Standard HTTP range resume; a server refusing it is an error. Never bypass
  # TLS, substitute a mirror or trust the partial file without the final digest.
  curl -fL --continue-at - --retry 3 --retry-delay 5 "$UPSTREAM/$IMAGE" -o "$SOURCE.part"
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

log 'Applying pinned initrd fix for local-only live APT cache generation'
initrd_stage="$(mktemp -d "$WORK_DIR/initrd-stage.XXXXXX")"
xorriso -osirrox on -indev "$SOURCE" -extract /casper/initrd "$initrd_stage/original" >/dev/null 2>&1
python3 "$REPO_ROOT/build/patch-live-initrd.py" --input "$initrd_stage/original" \
  --output "$initrd_stage/patched" --report "$initrd_stage/orez-initrd.json"

xorriso -osirrox on -indev "$SOURCE" -extract /md5sum.txt "$initrd_stage/original-md5sum.txt" >/dev/null 2>&1
python3 "$REPO_ROOT/build/update-media-checksums.py" --source "$initrd_stage/original-md5sum.txt" \
  --output "$initrd_stage/md5sum.txt" --initrd "$initrd_stage/patched" \
  --metadata "$initrd_stage/orez-initrd.json" --live "$WORK_DIR/zz-orez.squashfs" \
  --install "$WORK_DIR/orez-install.squashfs"

log 'Replaying upstream EFI/BIOS boot metadata while adding OREZ layer'
rm -f -- "$OUTPUT.part"
xorriso -indev "$SOURCE" -outdev "$OUTPUT.part" \
  -map "$WORK_DIR/zz-orez.squashfs" /casper/zz-orez.squashfs \
  -map "$WORK_DIR/orez-install.squashfs" /casper/orez-install.squashfs \
  -map "$initrd_stage/md5sum.txt" /md5sum.txt \
  -map "$initrd_stage/patched" /casper/initrd \
  -map "$initrd_stage/orez-initrd.json" /casper/orez-initrd.json \
  -boot_image any replay -commit > "$WORK_DIR/xorriso.log" 2>&1 \
  || fail "Remix failed. See $WORK_DIR/xorriso.log"
[[ -s "$OUTPUT.part" ]] || fail 'No output ISO written.'
mv -f -- "$OUTPUT.part" "$OUTPUT"
cp -- "$initrd_stage/orez-initrd.json" "$OUTPUT_DIR/orez-initrd.json"
rm -rf -- "$initrd_stage"

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
