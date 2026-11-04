#!/usr/bin/env bash
# Headless, diskless QEMU boot check: verifies a guest running casper can see the OREZ overlay.
# This direct-kernel test does NOT verify UEFI/GRUB/graphics or installer.
set -Eeuo pipefail
[[ "$#" -eq 1 && -f "$1" ]] || { echo 'Usage: test-casper-vm.sh OREZ.iso' >&2; exit 2; }
for tool in qemu-system-x86_64 xorriso timeout grep tail mktemp; do command -v "$tool" >/dev/null || { echo "Missing $tool" >&2; exit 2; }; done
ISO="$(realpath "$1")"
REPO_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)"
EVIDENCE_DIR="${OREZ_BOOT_EVIDENCE_DIR:-$REPO_ROOT/dist/boot-evidence}"
mkdir -p -- "$EVIDENCE_DIR"
mkdir -p -- "$EVIDENCE_DIR/extracted"
LOG="$EVIDENCE_DIR/casper-serial.log"
rm -f -- "$LOG"
# The ISO must contain the same kernel and initrd being tested.
xorriso -osirrox on -indev "$ISO" -extract /casper/vmlinuz "$EVIDENCE_DIR/extracted/vmlinuz" >/dev/null 2>&1
xorriso -osirrox on -indev "$ISO" -extract /casper/initrd "$EVIDENCE_DIR/extracted/initrd" >/dev/null 2>&1
# No writable hard disk, network interface, host port forwarding or external serial endpoints.
# There is no KVM assumption: Github-hosted VMs commonly lack /dev/kvm.
set +e
timeout --signal=TERM --kill-after=10s "${OREZ_QEMU_TIMEOUT:-330}" \
  qemu-system-x86_64 -machine q35,accel=tcg -cpu max -m 4096 -smp 2 \
    -kernel "$EVIDENCE_DIR/extracted/vmlinuz" \
    -initrd "$EVIDENCE_DIR/extracted/initrd" \
    -append 'boot=casper orez.verify=1 console=ttyS0,115200n8 loglevel=4 systemd.show_status=1' \
    -drive "file=$ISO,if=ide,index=1,media=cdrom,format=raw,readonly=on" \
    -net none -display none -monitor none -serial "file:$LOG" -no-reboot
qemu_exit=$?
set -e
if grep -Fq 'OREZ_BOOT_PROOF=CASPER_AND_OREZ_LAYER_PRESENT' "$LOG"; then
  echo "PASS: live casper guest booted and OREZ overlay was visible (QEMU exit=$qemu_exit)" | tee "$EVIDENCE_DIR/RESULT.txt"
  exit 0
fi
echo "FAIL: casper guest did not report the OREZ overlay (QEMU exit=$qemu_exit)" | tee "$EVIDENCE_DIR/RESULT.txt" >&2
tail -80 "$LOG" >&2 || true
exit 1
