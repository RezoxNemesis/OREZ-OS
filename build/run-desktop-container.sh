#!/usr/bin/env bash
# Isolated desktop/capability tests; no device access, bind mounts, or network.
set -euo pipefail
cd "$(dirname "$0")/.."
out="${1:?Fresh evidence output directory required}"
mkdir "$out"
image="${OREZ_DESKTOP_IMAGE:-orez-desktop-test:20261105}"
docker image inspect "$image" --format '{{.Id}}' > "$out/container-image.txt"
input="$(mktemp -d)"
container=''
cleanup() {
  if [[ -n "$container" ]]; then docker rm -f "$container" >/dev/null 2>&1 || true; fi
  rm -rf -- "$input"
}
trap cleanup EXIT
cp dist/orez-shell_0.1.0-1_all.deb "$input/orez-shell.deb"
cp build/integration/desktop-scenarios.sh "$input/"
cp build/integration/desktop-session.sh "$input/"
cp build/integration/desktop-interactions.py "$input/"
cp build/integration/capabilities.py "$input/"
sha256sum "$input"/* > "$out/test-inputs.sha256"
container="$(docker create --network none --pids-limit 512 --memory "${OREZ_TEST_MEMORY:-4g}" \
  --cpus "${OREZ_TEST_CPUS:-2}" --shm-size 256m \
  --tmpfs /scratch:rw,nosuid,nodev,noexec,size=16m,mode=1777 \
  -e OREZ_DISPOSABLE_TEST=1 -e OREZ_SCENARIO="${OREZ_SCENARIO:-desktop}" \
  -e OREZ_RENDERER="${OREZ_RENDERER:-software}" \
  -e OREZ_CAPABILITY_FILTER="${OREZ_CAPABILITY_FILTER:-}" \
  "$image" bash /input/desktop-scenarios.sh)"
docker cp "$input/." "$container:/input"
docker inspect "$container" --format '{{json .HostConfig}}' > "$out/container-runtime-config.json"
set +e
docker start --attach "$container"
result=$?
set -e
docker inspect "$container" --format '{{json .State}}' > "$out/container-state.json"
docker cp "$container:/evidence/." "$out/" || { echo 'Failed to copy desktop evidence'; exit 1; }
if (( result != 0 )); then
  for log in "$out"/*.log; do [[ ! -f "$log" ]] || { printf '\n%s\n' "$log"; tail -30 "$log"; }; done
fi
exit "$result"
