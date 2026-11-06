#!/usr/bin/env bash
# Isolated tests; no device access or bind mounts. Outbound network is opt-in.
set -euo pipefail
cd "$(dirname "$0")/.."
out="${1:?Fresh evidence output directory required}"
mkdir "$out"
image="${OREZ_DESKTOP_IMAGE:-orez-qa:20261105-compact}"
docker image inspect "$image" --format '{{.Id}}' > "$out/container-image.txt"
docker info --format '{"memory_limits_supported":{{.MemoryLimit}},"cgroup_driver":"{{.CgroupDriver}}","warnings":{{json .Warnings}}}' > "$out/resource-enforcement.json"
if [[ "${OREZ_REQUIRE_RESOURCE_LIMITS:-0}" == 1 ]] && ! python3 -c 'import json,sys;sys.exit(not json.load(open(sys.argv[1]))["memory_limits_supported"])' "$out/resource-enforcement.json"; then
  echo 'BLOCKED: Docker cannot enforce memory limits. This environment cannot qualify a RAM profile.'
  exit 2
fi
input="$(mktemp -d)"
container=''
cleanup() {
  if [[ -n "$container" ]]; then docker rm -f "$container" >/dev/null 2>&1 || true; fi
  rm -rf -- "$input"
}
trap cleanup EXIT
cp "$(python3 build/package-info.py path)" "$input/orez-shell.deb"
cp build/integration/desktop-scenarios.sh "$input/"
cp build/integration/desktop-session.sh "$input/"
cp build/integration/desktop-interactions.py "$input/"
cp build/integration/tour-desktop.py "$input/"
cp build/integration/capabilities.py "$input/"
cp build/integration/everyday.py "$input/"
cp build/integration/everyday-browser.mjs "$input/"
cp build/integration/connectivity.py "$input/"
cp build/integration/native-upgrade.py "$input/"
if [[ "${OREZ_SCENARIO:-desktop}" == native-upgrade ]]; then
  cp "${OREZ_PREVIOUS_PACKAGE:?Set the previous verified OREZ .deb for an upgrade test}" "$input/previous.deb"
fi
network="${OREZ_TEST_NETWORK:-none}"
[[ "$network" == none || "$network" == bridge ]] || { echo 'Test network must be none or bridge'; exit 2; }
sha256sum "$input"/* > "$out/test-inputs.sha256"
container="$(docker create --user 0 --network "$network" --pids-limit 512 --memory "${OREZ_TEST_MEMORY:-4g}" \
  --cpus "${OREZ_TEST_CPUS:-2}" --shm-size 256m \
  --tmpfs /scratch:rw,nosuid,nodev,noexec,size=16m,mode=1777 \
  -e OREZ_DISPOSABLE_TEST=1 -e OREZ_SCENARIO="${OREZ_SCENARIO:-desktop}" \
  -e OREZ_RENDERER="${OREZ_RENDERER:-software}" \
  -e OREZ_CAPABILITY_FILTER="${OREZ_CAPABILITY_FILTER:-}" \
  -e OREZ_PRESSURE_MB="${OREZ_PRESSURE_MB:-0}" \
  -e OREZ_EVERYDAY_FILTER="${OREZ_EVERYDAY_FILTER:-}" \
  "$image" bash /input/desktop-scenarios.sh)"
docker cp "$input/." "$container:/input"
printf '%s\n' "$container" > "$out/container-id.txt"
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
