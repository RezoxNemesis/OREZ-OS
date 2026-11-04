#!/usr/bin/env bash
# Headless, diskless QEMU boot check: verifies a guest running casper can see the OREZ overlay.
# This direct-kernel test does NOT verify UEFI/GRUB/graphics or installer.
set -Eeuo pipefail
[[ "$#" -eq 1 && -f "$1" ]] || { echo 'Usage: test-casper-vm.sh OREZ.iso' >&2; exit 2; }
for tool in qemu-system-x86_64 xorriso timeout grep tail mktemp socat gzip; do command -v "$tool" >/dev/null || { echo "Missing $tool" >&2; exit 2; }; done
ISO="$(realpath "$1")"
REPO_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)"
EVIDENCE_DIR="${OREZ_BOOT_EVIDENCE_DIR:-$REPO_ROOT/dist/boot-evidence}"
mkdir -p -- "$EVIDENCE_DIR"
mkdir -p -- "$EVIDENCE_DIR/extracted"
LOG="$EVIDENCE_DIR/casper-serial.log"
MONITOR="$EVIDENCE_DIR/casper-monitor.sock"
QMP="$EVIDENCE_DIR/casper-qmp.sock"
rm -f -- "$LOG" "$MONITOR" "$QMP" "$EVIDENCE_DIR/gui-screen.ppm.gz" "$EVIDENCE_DIR/try-prompt-before.ppm.gz"
# The ISO must contain the same kernel and initrd being tested.
xorriso -osirrox on -indev "$ISO" -extract /casper/vmlinuz "$EVIDENCE_DIR/extracted/vmlinuz" >/dev/null 2>&1
xorriso -osirrox on -indev "$ISO" -extract /casper/initrd "$EVIDENCE_DIR/extracted/initrd" >/dev/null 2>&1
# Optional hardware acceleration on compatible CI runners; keep pure TCG fallback.
# This changes ONLY test VM performance, never target PC boot or security.
if [[ -c /dev/kvm && -r /dev/kvm && -w /dev/kvm ]] && command -v qemu-system-x86_64 >/dev/null; then
  export OREZ_VM_ACCEL=kvm OREZ_VM_CPU=host
  echo 'OREZ VM accelerator: KVM available'
else
  export OREZ_VM_ACCEL=tcg OREZ_VM_CPU=max
  echo 'OREZ VM accelerator: TCG fallback (can be very slow)'
fi
# No writable hard disk, network interface, host port forwarding or external serial endpoints.
# There is no KVM assumption: Github-hosted VMs commonly lack /dev/kvm.
# Stop the VM as soon as the overlay witness appears; do not waste runner time.
set +e
timeout --signal=TERM --kill-after=10s "${OREZ_QEMU_TIMEOUT:-420}" \
  qemu-system-x86_64 -machine "q35,accel=${OREZ_VM_ACCEL:-tcg}" -cpu "${OREZ_VM_CPU:-max}" -m 4096 -smp 2 \
    -kernel "$EVIDENCE_DIR/extracted/vmlinuz" \
    -initrd "$EVIDENCE_DIR/extracted/initrd" \
    -append 'boot=casper orez.verify=1 console=ttyS0,115200n8 loglevel=4 systemd.show_status=1' \
    -drive "file=$ISO,if=ide,index=1,media=cdrom,format=raw,readonly=on" \
    -net none -vga std -device qemu-xhci,id=orez-xhci -device usb-tablet,bus=orez-xhci.0 -display none \
    -monitor "unix:$MONITOR,server=on,wait=off" \
    -qmp "unix:$QMP,server=on,wait=off" \
    -serial "file:$LOG" -no-reboot &
qemu_timeout_pid=$!
set -e
try_sent=0
for ((attempt=0;attempt<210;attempt++)); do
  # The Kubuntu live image launches a Try/Install welcome process BEFORE Plasma.
  # Only on a disposable guest (no disk/network), click the left-hand Try button.
  if [[ "${OREZ_REQUIRE_GUI:-0}" == 1 && "$try_sent" -eq 0 && -S "$QMP" && -s "$LOG" ]] &&
      grep -Fq 'kubuntu-installer-prompt' "$LOG"; then
    # Require the actual known 1280x800 Try/Install framebuffer before clicking.
    if [[ -S "$MONITOR" ]] &&
        printf 'screendump %s\n' "$EVIDENCE_DIR/try-prompt-before.ppm" |
          socat -t 12 - UNIX-CONNECT:"$MONITOR" >/dev/null 2>&1 &&
        [[ -s "$EVIDENCE_DIR/try-prompt-before.ppm" ]] &&
        python3 "$REPO_ROOT/build/check-try-frame.py" "$EVIDENCE_DIR/try-prompt-before.ppm"; then
      try_sent=1
      gzip -f -9 "$EVIDENCE_DIR/try-prompt-before.ppm"
      bash "$REPO_ROOT/build/qmp-try-live.sh" "$QMP" "$EVIDENCE_DIR/qmp-try-result.log" || {
        echo 'QMP Try transition failed; GUI gate remains mandatory' >&2
      }
    else
      rm -f -- "$EVIDENCE_DIR/try-prompt-before.ppm"
    fi
  fi
  if [[ -s "$LOG" ]] && grep -Fq 'OREZ_BOOT_PROOF=CASPER_AND_OREZ_LAYER_PRESENT' "$LOG"; then
    if [[ "${OREZ_REQUIRE_GUI:-0}" != 1 ]] || grep -Fq 'OREZ_GUI_PROOF=PLASMA_PROCESS_AND_DISPLAY_MANAGER_ACTIVE' "$LOG"; then
      break
    fi
  fi
  if ! kill -0 "$qemu_timeout_pid" 2>/dev/null; then break; fi
  sleep 2
done
if [[ -S "$MONITOR" ]] && kill -0 "$qemu_timeout_pid" 2>/dev/null; then
  if printf 'screendump %s\n' "$EVIDENCE_DIR/gui-screen.ppm" | socat -t 12 - UNIX-CONNECT:"$MONITOR" >/dev/null 2>&1 && [[ -s "$EVIDENCE_DIR/gui-screen.ppm" ]]; then
    gzip -f -9 "$EVIDENCE_DIR/gui-screen.ppm"
  fi
fi
if kill -0 "$qemu_timeout_pid" 2>/dev/null; then kill -TERM "$qemu_timeout_pid" 2>/dev/null || true; fi
set +e
wait "$qemu_timeout_pid"
qemu_exit=$?
set -e
if grep -Fq 'OREZ_BOOT_PROOF=CASPER_AND_OREZ_LAYER_PRESENT' "$LOG"; then
  echo "PASS: live casper guest booted and OREZ overlay was visible (QEMU exit=$qemu_exit)" | tee "$EVIDENCE_DIR/RESULT.txt"
  if grep -Fq 'OREZ_GUI_PROOF=PLASMA_PROCESS_AND_DISPLAY_MANAGER_ACTIVE' "$LOG"; then
    echo 'PASS: Plasma Shell and display manager active (visual review still needed)' | tee "$EVIDENCE_DIR/GUI_RESULT.txt"
  else
    echo 'BLOCKED: Plasma graphical session not proven' | tee "$EVIDENCE_DIR/GUI_RESULT.txt"
    [[ "${OREZ_REQUIRE_GUI:-0}" != 1 ]] || exit 1
  fi
  exit 0
fi
echo "FAIL: casper guest did not report the OREZ overlay (QEMU exit=$qemu_exit)" | tee "$EVIDENCE_DIR/RESULT.txt" >&2
tail -80 "$LOG" >&2 || true
exit 1
