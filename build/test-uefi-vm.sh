#!/usr/bin/env bash
# UEFI/OVMF screenshot capture from the actual OREZ ISO. Manual visual review required.
set -Eeuo pipefail
[[ "$#" -eq 1 && -f "$1" ]] || { echo 'Usage: test-uefi-vm.sh OREZ.iso' >&2; exit 2; }
for tool in qemu-system-x86_64 socat gzip; do command -v "$tool" >/dev/null || { echo "Missing $tool" >&2; exit 2; }; done
ISO="$(realpath "$1")"
REPO_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)"
EVIDENCE_DIR="${OREZ_BOOT_EVIDENCE_DIR:-$REPO_ROOT/dist/boot-evidence}"
mkdir -p -- "$EVIDENCE_DIR"
CODE=''; VARS=''
for suffix in _4M ''; do
  if [[ -r "/usr/share/OVMF/OVMF_CODE${suffix}.fd" && -r "/usr/share/OVMF/OVMF_VARS${suffix}.fd" ]]; then
    CODE="/usr/share/OVMF/OVMF_CODE${suffix}.fd"
    VARS="/usr/share/OVMF/OVMF_VARS${suffix}.fd"
    break
  fi
done
[[ -n "$CODE" ]] || { echo 'OVMF firmware files missing' >&2; exit 1; }
TMP="$(mktemp -d)"; vm_pid=''
cleanup() {
  if [[ -n "$vm_pid" ]] && kill -0 "$vm_pid" 2>/dev/null; then kill -TERM "$vm_pid" 2>/dev/null || true; wait "$vm_pid" 2>/dev/null || true; fi
  rm -rf -- "$TMP"
}
trap cleanup EXIT
cp -- "$VARS" "$TMP/vars.fd"
# Disposable OVMF variables, no writable disk image, host devices or network.
qemu-system-x86_64 -machine q35,accel=tcg -cpu max -m 4096 -smp 2 \
  -drive "if=pflash,format=raw,unit=0,readonly=on,file=$CODE" \
  -drive "if=pflash,format=raw,unit=1,file=$TMP/vars.fd" \
  -drive "if=ide,index=1,media=cdrom,format=raw,readonly=on,file=$ISO" \
  -boot order=d -vga std -display none \
  -monitor "unix:$TMP/qemu-monitor.sock,server=on,wait=off" \
  -serial "file:$EVIDENCE_DIR/uefi-serial.log" -net none -no-reboot &
vm_pid=$!
for ((i=0;i<30;i++)); do [[ -S "$TMP/qemu-monitor.sock" ]] && break; sleep 1; done
[[ -S "$TMP/qemu-monitor.sock" ]] || { echo 'UEFI VM monitor never appeared' >&2; exit 1; }
sleep "${OREZ_UEFI_CAPTURE_AFTER:-90}"
if ! kill -0 "$vm_pid" 2>/dev/null; then echo 'UEFI VM stopped unexpectedly' >&2; exit 1; fi
printf 'screendump %s\n' "$EVIDENCE_DIR/uefi-screen.ppm" | socat -t 10 - UNIX-CONNECT:"$TMP/qemu-monitor.sock" >/dev/null
[[ -s "$EVIDENCE_DIR/uefi-screen.ppm" ]] || { echo 'UEFI screenshot missing' >&2; exit 1; }
gzip -f -9 "$EVIDENCE_DIR/uefi-screen.ppm"
# Second screenshot to distinguish slow boot splash from a full desktop.
sleep "${OREZ_UEFI_EXTRA_WAIT:-145}"
if ! kill -0 "$vm_pid" 2>/dev/null; then echo 'UEFI guest exited before later frame' >&2; exit 1; fi
printf 'screendump %s\n' "$EVIDENCE_DIR/uefi-screen-later.ppm" | socat -t 12 - UNIX-CONNECT:"$TMP/qemu-monitor.sock" >/dev/null
[[ -s "$EVIDENCE_DIR/uefi-screen-later.ppm" ]] || { echo 'Second screenshot missing' >&2; exit 1; }
gzip -f -9 "$EVIDENCE_DIR/uefi-screen-later.ppm"
{
  echo 'Two UEFI screenshots captured under OVMF (unmodified source ISO).'
  echo 'Screen content NOT automatically verified; requires visual review.'
  echo 'No physical boot, Secure Boot certification, or installer proof.'
} > "$EVIDENCE_DIR/UEFI_RESULT.txt"
cat "$EVIDENCE_DIR/UEFI_RESULT.txt"
