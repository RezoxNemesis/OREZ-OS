#!/usr/bin/env bash
# Download the pinned Kubuntu 26.04.1 ISO and verify it against Ubuntu's signed
# SHA256SUMS with the pinned CD-signing fingerprint. Prints the verified path.
# Same trust rules as build-live.sh: HTTPS alone is not sufficient.
set -Eeuo pipefail
DEST=${1:?usage: fetch-verified-base.sh <directory>}
IMAGE='kubuntu-26.04.1-desktop-amd64.iso'
UPSTREAM='https://cdimage.ubuntu.com/cdimage/kubuntu/releases/26.04.1/release'
IMAGE_SHA256='831e4d4bb85098339ba43d3502cd6619b27e76daf37246a084cd68a6413090b8'
FPR='843938DF228D22F7B3742BC0D94AA3F0EFE21092'
mkdir -p "$DEST"; cd "$DEST"
for f in SHA256SUMS SHA256SUMS.gpg; do curl -fLsS --retry 3 "$UPSTREAM/$f" -o "$f"; done
curl -fLsS --retry 3 'https://archive.ubuntu.com/ubuntu/project/ubuntu-archive-keyring.gpg' -o keyring.gpg
gpgv --status-fd 1 --keyring ./keyring.gpg SHA256SUMS.gpg SHA256SUMS > verify.log 2>&1 || { cat verify.log >&2; exit 1; }
grep -Eq "^\[GNUPG:\] VALIDSIG $FPR([[:space:]]|$)" verify.log || { echo 'Not signed by pinned Ubuntu CD key' >&2; exit 1; }
grep -Fxq "$IMAGE_SHA256 *$IMAGE" SHA256SUMS || { echo 'Signed checksum differs from pinned image' >&2; exit 1; }
[[ -f $IMAGE ]] || curl -fL --retry 3 --retry-delay 5 -sS "$UPSTREAM/$IMAGE" -o "$IMAGE"
printf '%s  %s\n' "$IMAGE_SHA256" "$IMAGE" | sha256sum -c - >&2
echo "$DEST/$IMAGE"
