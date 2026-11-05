# Live ISO and virtual graphics diagnostics — 5 November 2026

This work targets the unresolved live-desktop gate. Source/package/native
container success is distinct from a booted, usable OS. Installation remains
disabled. Follow the latest AI_HANDOFF.md for reviewed results and exact commits.

## Implemented behavior

The new `build/probe-virgl-vm.py` boots a checksum-verified regular ISO file as an
ordinary user with TCG, 4 GiB guest RAM, two virtual CPUs and software-backed
VirGL. It supports both direct-kernel diagnostics and actual OVMF/UEFI boot.
Only UEFI mode tests the ISO boot chain. Its disposable firmware variable file
is the only writable firmware storage. No hard disk, NIC, host share, physical
device, remote display port or installer action is attached.

Xvfb starts on an allocated local display with TCP disabled. Host OpenGL must
identify llvmpipe. The harness retains real guest readback and full SDL-window
screenshots every 20 seconds, logs, ISO/firmware hashes and the exact invocation.
An OpenGL modeset may return QMP's specific `GenericError: no surface`; the
harness then captures the sole visible window belonging to its QEMU process.
Other QMP errors and disconnections fail the run. No synthetic screenshot is used.
The SDL window is moved to the host display's origin without resizing: its
initial centered position clipped 1280×800 captures to 1040×740 when the guest
changed modes. qa5-15 confirmed and corrected that position in the running
diagnostics; the final harness performs the same correction automatically.

Automatic input is restricted to the **left Try button** after the existing
1280×800 pinned welcome-screen recognizer matches an unscaled frame. Unknown
dimensions, missing surfaces and unmatched layouts receive no click. There is
no installer selection. An end-of-capture result means
`captured_requires_visual_review`, never automatic desktop qualification.

The QA dependency recipe includes the missing graphical QEMU modules. The live
builder now resumes interrupted ISO downloads using standard HTTP ranges while
keeping TLS, the pinned signing key and final whole-file digest checks. Disk
preflight credits existing allocated input blocks on the same filesystem, capped
at 5 GiB, against its 11 GiB starting reserve. Sparse files and separate cache
volumes cannot falsely reduce the output-space reserve. No files are removed to
force the build through a space shortage.

## Reproduce on a supported Linux builder

Install the dependencies in environment/orez-qa.Dockerfile. Run as a normal user,
using an existing verified ISO and a fresh output directory for every attempt:

```bash
python3 build/probe-virgl-vm.py \
  --iso /absolute/path/to/OREZ-OS-0.1-live-amd64.iso \
  --sha256 EXPECTED_64_CHARACTER_SHA256 \
  --output /absolute/path/to/new-uefi-evidence \
  --boot uefi --seconds 660
```

For the untouched upstream control, use `--boot direct`, the pinned Kubuntu
ISO and its checksum in build/build-live.sh. Wrap checks with
`build/run-with-evidence.py` to preserve report screenshots and failures. The
harness rejects root, block/character devices, unsafe comma-delimited paths,
digest mismatch and missing dependencies. `--ram-mib 6144` defines guest memory;
TCG/software rendering still cannot qualify the owner's 6 GiB performance goal.

Review `vm-result.json`, `serial.log`, `qemu.log`, `glxinfo.txt` and PNGs together.
Nonblank firmware, GRUB, a welcome screen or a splash is **not a desktop pass**.
Require a rendered desktop and actual launcher, terminal, files, Settings and
window interactions before recording functional live-desktop success. Require
separate target-PC tests for NVIDIA, radios, display modes, suspend, Secure Boot
and performance. Do not present this private development ISO as install-ready.

## Current image provenance

The rebuilt development ISO uses source `82183ea8fbc5c1a759576a5ff0b814b936402bed`.
It is **5,073,338,368 bytes** (5.073 GB / 4.725 GiB), SHA-256
`8ec11599942f871759d7a2950b26430c8cb51a35d068283d09f348c2771e40e9`.
The original Kubuntu digest passed after two truncated downloads were resumed.
Static ISO structure, the separate installation payload and disabled live
installer guard pass in qa5-08. These are not boot/installation acceptance.

Initial qa5-09/10 captures stopped at the QMP missing-surface error. qa5-10
reaches OVMF/GRUB; it also reproduces the previously recorded
`can't find command grub_platform` message. qa5-14 extracts GRUB configuration
from **both actual ISOs**: they are byte-identical, SHA-256
`3759b158b9857fac5edbbfca65f37d3396440ea2df67a3c951ce90bf45dcaf2d`, and each has
the stray bare command at line 23. This warning is inherited from upstream;
it is not proof of the cause of the graphics problem. Corrected SDL capture runs and their reviewed outcomes
are recorded in the handoff; do not interpret the initial runs as desktop proof.

## Engineering reference

[QEMU's official VirtIO GPU documentation](https://www.qemu.org/docs/master/system/devices/virtio/virtio-gpu.html)
distinguishes the 2D device from the VirGL backend and describes guest OpenGL
translation to host OpenGL. This experiment uses the installed QEMU 10.2.1 and
virglrenderer 1.2.0 packages, with Mesa 26.0.8 llvmpipe. It does not request Vulkan
Venus, host blobs or GPU passthrough. Hardware acceleration remains unavailable.
