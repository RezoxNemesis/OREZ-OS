# Publish the OREZ test environment

These are **development dependencies**, not a release ISO or a promise that
hardware capabilities can be created inside a container. The owner authorized
installing missing test tools and intends to publish the environment. No cloud
environment publication API is available in this session; publish this definition
through the environment's configuration UI. Do not silently publish an image or
change host security policy.

## Build once, reuse one dependency image

From the repository root on a Docker-enabled Linux x86-64 builder:

```bash
docker build --secret id=qa_ca_bundle,src=/etc/ssl/certs/ca-certificates.crt -f environment/orez-qa.Dockerfile -t orez-qa:20261105-compact .
```

The canonical recipe starts directly from pinned Ubuntu and installs dependencies
in one filesystem layer. This matters with Docker VFS, which copies ancestor
filesystems instead of sharing overlay extents. It replaces the former four-image
chain locally; smaller integration Dockerfiles remain in the opt-in CI workflow,
which explicitly selects those image names to avoid installing unused tools. Native test
runners default to the compact image. They explicitly use container root only
for isolated package/service fixtures and run desktop applications as UID 1500.
They grant no host devices, mounts, host networking or extra capabilities.

For an ordinary network the optional CA secret can be omitted. In the managed
workspace it supplies the **existing trusted public CA bundle** to curl/APT/npm
only during their build steps. Mode 0444 lets APT's `_apt` user read it. TLS and
APT signature verification remain enabled; no private key, proxy credential or
session CA file is copied into an image layer. Preserve the environment's proxy
configuration. Do not use host networking or disable TLS to get around a denial.

The completed image contains Plasma/KWin, native settings/files/terminal tools,
VLC, SuperTux, Brave from its scoped signed official repository, FFmpeg, Blender,
C++/Git/SQLite tools, Java 21, QEMU, OVMF, virtual TPM tools, ISO/SquashFS tools
and diagnostics, plus NetworkManager/KDE connection settings, BlueZ/Bluedevil,
OBEX and KIO file access. Hardware pairing remains untested. It defaults to a normal user and starts no remote-access service.
It includes no Google SDK/system image, Google login or OREZ user data.

Ubuntu base digest is pinned; installed APT versions and final image IDs are
recorded. The dependency repositories are not frozen snapshots, so rebuilding
later is not guaranteed byte-identical. All bundled software retains its own
licence; comply with attribution/source requirements when distributing a
published dependency image. Owner wallpaper assets are not part of this base.

## Publisher host requirements

- Linux x86-64 with hardware virtualization enabled and **actual `/dev/kvm`
  access for the normal test user**. For the owner's AMD machine this means
  firmware SVM plus Linux KVM access. Configure through the host/provider UI;
  scripts never create a fake device, change groups or alter firmware.
- Prefer 8 CPU threads, 16 GiB RAM and at least 80 GiB workspace storage for
  full ISO/VM work. The current 32 GiB workspace is too tight for retaining
  multiple images, large ISO builds and Android guests together. Separate
  6 GiB and 16 GiB VM profiles are needed for meaningful full-OS comparison.
- GPU-backed graphical VM support or a usable render node for accelerated
  desktop tests; actual NVIDIA access/toolkit is separately required for CUDA
  and RTX qualification. A software renderer or the presence of `vulkaninfo`
  is not hardware acceleration.
- Enforced cgroup v2 resource limits. This workspace reports `MemoryLimit=false`,
  `CgroupDriver=none`, rootless Docker without cgroups. Earlier 2/4/6 GiB
  requests were **not enforced**. Configure supported host delegation through
  the provider; never claim a RAM budget from Docker arguments alone. Set
  `OREZ_REQUIRE_RESOURCE_LIMITS=1` when qualifying a bounded-memory profile.
- A supported normal-user browser sandbox. The current nested container rejects
  Brave's namespace creation. Do not use `--no-sandbox`, privileged containers,
  disabled seccomp/AppArmor, or extra broad host privileges to force a pass.
- Preserve HTTPS proxy/CA settings. YouTube is currently denied by the platform
  proxy despite an unrestricted HTTP policy snapshot. Request the supported
  provider configuration/allowance if available; do not route around the proxy.
- Shared desktop is declared by the provider, but its runtime state was unknown
  and no desktop-start tool was exposed. Publication must verify actual GUI
  access; a declaration alone is not a successful desktop session.

The current environment plugin reports runtime context only. It cannot edit
the environment draft or publish it. Editing `/etc/codex/network-policy.json`
would not grant network access and is not part of setup.

## Software-backed VM display diagnostics

The recipe now explicitly installs `qemu-system-gui` and
`qemu-system-modules-opengl`. `qemu-system-x86` with no recommended packages had
only `none`/`curses` display backends in the original compact image. Adding those
signed Ubuntu modules in a disposable lab exposes SDL/GTK/OpenGL; it does not
upgrade the already-built compact image automatically.

Normal-user Xvfb + Mesa llvmpipe + QEMU SDL `gl=on` with `virtio-vga-gl` successfully
initialized in qa5-04. Host `glxinfo` explicitly says **Accelerated: no**. This is
a different rendering path from the earlier headless 2D tests, suitable for
functional diagnostics only. It neither creates a render device nor qualifies
RTX, CUDA, Vulkan, game performance, 6 GiB workloads or power consumption.
Use the opt-in harness in [VM diagnostics](../docs/VM_GRAPHICS_QA.md); no security
policy change, privileged container, public display port or physical disk is needed.

## Run and preserve proof

Run `python3 environment/preflight.py` as the actual test user. Feed that through
`build/run-with-evidence.py` when recording a check. Use the native orchestration
commands in `docs/QA_SCENARIOS.md` and the newer daily-use report. Runtime tests
default to no network; `OREZ_TEST_NETWORK=bridge` explicitly permits outbound
networking without publishing a listening port, host mounts or devices.

No Google SDK licence is accepted automatically. Its development-only use
restriction is documented in `docs/ANDROID_APPS.md`; a consumer Play Store
provider still needs qualification. Install a qualified guest only after those
conditions are satisfied, with the owner's Google sign-in private and uncaptured.

## Verified local image checkpoint

Compact image `orez-qa:20261105-compact` built in qa4-04:
`sha256:e6427926838b638347acca36ea9ba9a168f4f0e95059391c17c1f94d4e73da3d`,
4,173,178,310 logical bytes. It defaults to `orez-test`; pass
`--workdir /home/orez-test` at runtime if desired. Build preflight and exact package
versions are in `/opt/orez-qa/`. QEMU and Java executables ran, but no KVM/GPU
exists in the builder. The image is local and has not been published.

The previous image chain exhausted the 32 GiB VFS workspace. Before removing
only disposable QA images, the old desktop/dependency images were saved to
`/dev/shm/orez-qa-work/desktop-images.tar.gz` (1,492,430,996 bytes) and all 31
referenced content blobs were SHA-256 checked by `check-image-backup.py`.
That RAM-backed archive is temporary and will not survive environment shutdown.
The older final QA image can be rebuilt from its committed recipe; it was removed
to recover space. Screenshots, source and owner data were retained. The compact
replacement recovered enough disk for native container tests. Full ISO/Android
work still needs the larger supported host described above.
