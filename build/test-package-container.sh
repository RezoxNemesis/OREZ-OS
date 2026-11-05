#!/usr/bin/env bash
# Test a prebuilt package in a disposable Ubuntu image. No host disk devices/mounts.
set -euo pipefail
root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "$root"
out="${1:?Pass a fresh output directory}"
mkdir "$out"
image="${OREZ_PACKAGE_IMAGE:-orez-package-test:20261105}"
docker image inspect "$image" --format '{{.Id}}' > "$out/container-image.txt"
input="$(mktemp -d)"
container=''
cleanup() {
    if [[ -n "$container" ]]; then docker rm -f "$container" >/dev/null 2>&1 || true; fi
    rm -rf -- "$input"
}
trap cleanup EXIT
cp dist/orez-shell_0.1.0-1_all.deb "$input/orez-shell.deb"
cp image/installer/installed-files.txt "$input/installed-files.txt"
cp build/integration/package-lifecycle.sh build/integration/capture-native.sh "$input/"
sha256sum "$input"/* > "$out/test-inputs.sha256"
container="$(docker create --network none --pids-limit 256 --memory 3g \
    --env OREZ_DISPOSABLE_TEST=1 --env OREZ_CAPTURE_NATIVE=1 "$image" bash /input/package-lifecycle.sh)"
docker cp "$input/." "$container:/input"
set +e
docker start --attach "$container"
result=$?
set -e
docker inspect "$container" --format '{{json .State}}' > "$out/container-state.json"
docker cp "$container:/evidence/." "$out/" || { echo 'Failed to preserve container evidence'; exit 1; }
if (( result != 0 )); then
    for log in "$out"/*.log "$out"/native/*.log; do
        [[ -f "$log" ]] || continue
        printf '\nLast lines of %s\n' "$log"
        tail -20 "$log"
    done
fi
exit "$result"
