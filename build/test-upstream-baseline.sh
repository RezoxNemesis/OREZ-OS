#!/usr/bin/env bash
# Unmodified Kubuntu visual control: no hard disk, network, installer, or host input.
set -Eeuo pipefail
[[ "$#" -eq 1 && -f "$1" ]] || { echo "Usage: $0 ORIGINAL_KUBUNTU.iso" >&2; exit 2; }
for tool in qemu-system-x86_64 xorriso socat timeout gzip sha256sum python3; do
  command -v "$tool" >/dev/null || { echo "Missing $tool" >&2; exit 2; }
done
ROOT="$(cd -- "$(dirname -- "$0")/.." && pwd -P)"
ISO="$(realpath "$1")"
SHA='831e4d4bb85098339ba43d3502cd6619b27e76daf37246a084cd68a6413090b8'
printf '%s  %s\n' "$SHA" "$ISO" | sha256sum -c - >/dev/null
OUT="$ROOT/dist/upstream-baseline"
mkdir -p -- "$OUT"
xorriso -osirrox on -indev "$ISO" -extract /casper/vmlinuz "$OUT/vmlinuz" >/dev/null 2>&1
xorriso -osirrox on -indev "$ISO" -extract /casper/initrd "$OUT/initrd" >/dev/null 2>&1
SERIAL="$OUT/guest-serial.log"
MON="$OUT/monitor.sock"
QMP="$OUT/qmp.sock"
rm -f -- "$SERIAL" "$MON" "$QMP"
# Diskless networkless guest with pure software VirtIO, same as OREZ VM test.
set +e
timeout --signal=TERM --kill-after=8s 800 qemu-system-x86_64 \
  -machine q35,accel=tcg -cpu max -m 4096 -smp 2 \
  -kernel "$OUT/vmlinuz" -initrd "$OUT/initrd" \
  -append 'boot=casper console=ttyS0,115200n8 loglevel=4 systemd.show_status=1' \
  -drive "file=$ISO,if=ide,index=1,media=cdrom,format=raw,readonly=on" \
  -net none -vga virtio -device qemu-xhci,id=orez-xhci \
  -device usb-tablet,bus=orez-xhci.0 -display none \
  -monitor "unix:$MON,server=on,wait=off" \
  -qmp "unix:$QMP,server=on,wait=off" \
  -serial "file:$SERIAL" -no-reboot &
pid=$!
set -e
cleanup() {
  if kill -0 "$pid" 2>/dev/null; then kill -TERM "$pid" 2>/dev/null || true; fi
  wait "$pid" 2>/dev/null || true
}
trap cleanup EXIT
# The pristine image has NO OREZ GUI diagnostic service, so its serial log
# will never contain the OREZ_GUI_PROCESSES kubuntu-installer-prompt marker.
# Inspect actual QEMU pixels instead. Do not click any unfamiliar frame.
selected=0
for attempt in $(seq 1 320); do
  if [[ -S "$MON" && -S "$QMP" ]] && (( attempt % 5 == 0 )); then
    frame="$OUT/try-before.ppm"
    if printf 'screendump %s\n' "$frame" | socat -t 10 - UNIX-CONNECT:"$MON" >/dev/null 2>&1 &&
       [[ -s "$frame" ]]; then
      if python3 "$ROOT/build/check-try-frame.py" "$frame" >/dev/null 2>&1; then
        rm -f -- "$OUT/last-screen.ppm"
        gzip -f -9 "$frame"
        if bash "$ROOT/build/qmp-try-live.sh" "$QMP" "$OUT/qmp-try.log"; then selected=1; break; fi
      else
        # Keep the most recent unmatched image for visual diagnosis.
        mv -f -- "$frame" "$OUT/last-screen.ppm"
      fi
    fi
  fi
  if ! kill -0 "$pid" 2>/dev/null; then break; fi
  sleep 2
done
report="$OUT/BASELINE_RESULT.txt"
if [[ "$selected" -ne 1 ]]; then
  if [[ -s "$OUT/last-screen.ppm" ]]; then gzip -f -9 "$OUT/last-screen.ppm"; fi
  echo 'BASELINE NOT QUALIFIED: safe Try transition was never completed (see last-screen screenshot)' | tee "$report"
  exit 1
fi
visible=0
for delay in 35 30; do
  sleep "$delay"
  kill -0 "$pid" 2>/dev/null || break
  frame="$OUT/frame-$delay.ppm"
  if printf 'screendump %s\n' "$frame" | socat -t 10 - UNIX-CONNECT:"$MON" >/dev/null 2>&1 && [[ -s "$frame" ]]; then
    if python3 "$ROOT/build/check-graphical-frame.py" "$frame" >> "$report" 2>&1; then visible=1; fi
    gzip -f -9 "$frame"
  fi
done
if [[ "$visible" -eq 1 ]]; then
  echo 'UPSTREAM VISIBLE: pristine Kubuntu renders a nonblank VM frame; inspect image manually' | tee -a "$report"
  exit 0
fi
echo 'UPSTREAM BLACK: pristine Kubuntu also cannot render a visible VM frame' | tee -a "$report"
exit 1
