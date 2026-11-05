#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
out="${1:?Fresh evidence output directory required}"
mkdir "$out"
input="$(mktemp -d)"
container=''
trap '[[ -z "$container" ]] || docker rm -f "$container" >/dev/null 2>&1; rm -rf -- "$input"' EXIT
cp dist/orez-shell_0.1.0-1_all.deb "$input/orez-shell.deb"
cp build/integration/package-scenarios.py "$input/"
image="${OREZ_PACKAGE_IMAGE:-orez-package-test:20261105}"
docker image inspect "$image" --format '{{.Id}}' > "$out/container-image.txt"
sha256sum "$input"/* > "$out/test-inputs.sha256"
container="$(docker create --network none --memory 2g --pids-limit 256 --env OREZ_DISPOSABLE_TEST=1 "$image" python3 /input/package-scenarios.py)"
docker cp "$input/." "$container:/input"
set +e
docker start --attach "$container"
result=$?
set -e
docker inspect "$container" --format '{{json .State}}' > "$out/container-state.json"
docker cp "$container:/evidence/." "$out/"
exit "$result"
