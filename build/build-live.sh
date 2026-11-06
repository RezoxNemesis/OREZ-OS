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
for c in curl gpg gpgv sha256sum awk grep xorriso mksquashfs unsquashfs zstd df stat python3; do need "$c"; done
[[ "$OUTPUT_DIR" != "$CACHE_DIR" && "$WORK_DIR" != "$OUTPUT_DIR" ]] || fail 'Output, cache and work directories must be separate.'
mkdir -p -- "$OUTPUT_DIR" "$CACHE_DIR" "$WORK_DIR"
# App/component layers are separately built in the isolated offline pipeline.
# Refuse a source-only image: successful assembly must include native apps and
# the actual dpkg-owned OREZ transaction. Check before any large download.
for variable in OREZ_APP_LAYER OREZ_COMPONENT_LAYER OREZ_COMPONENT_REPORT; do
  [[ -n "${!variable:-}" && -f "${!variable}" ]] || fail "Set $variable to the reviewed build input; see docs/LIVE_ASSEMBLY.md."
done
[[ ! -e "$OUTPUT" && ! -L "$OUTPUT" ]] || fail 'Refusing to replace an existing ISO.'
python3 - "$REPO_ROOT" "$OREZ_APP_LAYER" "$OREZ_COMPONENT_LAYER" "$OREZ_COMPONENT_REPORT" <<'PY_INPUTS'
import sys
sys.path.insert(0, sys.argv[1] + '/build')
from live_assembly import verify_components
verify_components(*sys.argv[2:])
print('Exact native application and dpkg-owned OREZ layers verified.')
PY_INPUTS

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

log 'Assembling exact base, native apps, dpkg-owned OREZ and owner-enrollment layers'
export OREZ_SOURCE_COMMIT="${GITHUB_SHA:-$(git -C "$REPO_ROOT" rev-parse HEAD)}"
python3 "$REPO_ROOT/build/assemble-live.py" --iso "$SOURCE" \
  --apps "$OREZ_APP_LAYER" --components "$OREZ_COMPONENT_LAYER" \
  --component-report "$OREZ_COMPONENT_REPORT" --output "$OUTPUT"

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
