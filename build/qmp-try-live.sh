#!/usr/bin/env bash
# Test-only click on "Try Kubuntu" in isolated QEMU live welcome screen.
# No disk, network, administrator access, host input or installation.
set -Eeuo pipefail
[[ "$#" -eq 2 && -S "$1" ]] || { echo 'Usage: qmp-try-live.sh QMP_SOCKET OUTPUT_LOG' >&2; exit 2; }
command -v socat >/dev/null || { echo 'socat is required' >&2; exit 2; }
socket="$1"
out="$2"
# In the 1280x800 standard VGA test framebuffer, Try is centered near (350,640).
# QEMU tablet absolute events use normalized coordinates; x=27.3%, y=80.0%.
# Never click the Install button (located right of center).
# The action is allowed ONLY in an isolated diskless VM with a known prompt.
{
  printf '{"execute":"qmp_capabilities"}\n'
  sleep 0.3
  printf '%s\n' '{"execute":"input-send-event","arguments":{"events":[{"type":"abs","data":{"axis":"x","value":8959}},{"type":"abs","data":{"axis":"y","value":26214}}]}}'
  sleep 0.4
  printf '%s\n' '{"execute":"input-send-event","arguments":{"events":[{"type":"btn","data":{"button":"left","down":true}}]}}'
  sleep 0.25
  printf '%s\n' '{"execute":"input-send-event","arguments":{"events":[{"type":"btn","data":{"button":"left","down":false}}]}}'
  sleep 0.2
} | socat -t 8 - UNIX-CONNECT:"$socket" > "$out"
returned="$(grep -c '"return"' "$out" || true)"
if (( returned < 4 )) || grep -q '"error"' "$out"; then
  echo 'QMP did not confirm all four commands; desktop transition unverified' >&2
  cat "$out" >&2
  exit 1
fi
echo 'QEMU test input: clicked Try on the live welcome screen (no disk/installer available)'
