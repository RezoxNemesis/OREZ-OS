# Publish the OREZ test environment

The VM helper recipe `environment/orez-vm-tools.Dockerfile` now includes
QEMU/OVMF plus optional private Xvfb/SDL/VirGL software graphics. Its latest
local image is `orez-vm-tools:20261106-virgl`, **737,968,451 bytes**,
ID `d169d643a3f43dbff1ef1113a22bae5bd8e1bb9aff0c5503f51538bf2ef4d25a`.
The previous headless-only image was 304,335,442 bytes. Both default to UID1500.
The new recipe has been built locally, not published. See
[LIVE_ASSEMBLY.md](../docs/LIVE_ASSEMBLY.md) for actual test scope.
Copy required harness files with canonical readable modes; the private checkout
is not automatically readable by another test UID.

For software 3D diagnostics run `build/probe-integrated-live.py --graphics virgl`
under `xvfb-run -a -s '-screen 0 1440x1000x24 -nolisten tcp'` inside the isolated
VM helper. Supply the same required ISO/hash/output/window arguments as 2D.
The harness verifies host llvmpipe, uses a private Xauthority cookie, and captures
the actual SDL window owned by its QEMU process. No cookie value is exported.
This supplies a virtual 3D interface, not hardware-accelerated GPU performance.
Both QMP and SDL capture failures are recorded without qualifying a frame. The
latest SDL timeout correction removes partial PNGs and continues; source tests
cover timeout/retry and refusal of an ambiguous window. It has not had another
full boot. All four current VM containers and the assembly helper are stopped
and removed after evidence collection; the two dependency image recipes/IDs and
packed build inputs remain.
QMP input should use immediate key down/up events; timed holds produced repeats
under TCG. Never infer password validity from a failed automation attempt.

For image construction, use the separate **239.7 MB** helper in
`environment/orez-image-tools.Dockerfile`. It was built locally as
`orez-image-tools:20261105`; it has APT/Python, dpkg, GnuPG, xorriso and SquashFS
tools, with no desktop. [Image-stage instructions](../docs/IMAGE_APPLICATIONS.md)
cover online resolution, offline chroot installation, metadata preservation and
storage limits. This avoids another full copy of the 4+ GB desktop QA image
under Docker VFS. Neither image was published by this session.

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

The recipe also includes `initramfs-tools-core` for independent initrd
extraction and archive inspection. This is a QA dependency, not a host boot
configuration change. The existing compact image must be rebuilt to include it.

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

## Owner-login and daily-app test dependencies

The recipe now includes PySide6 QtWidgets/QtTest, SDDM,
`plasma-session-wayland`, Plymouth and initramfs tools. These additions were
installed from signed Ubuntu repositories only in the disposable qa8 lab. The
retained compact dependency image has not been rebuilt or published. SDDM does
not list Wayland sessions without its render-device prerequisite; installing the
session package is insufficient. Do not create fake render devices.

Always use `build/stage-overlay.py` and root-owned archive/package metadata for
a disposable root overlay. Directly copying the checkout preserves its restrictive
umask and workspace UID, causing unreadable files or untrusted root directories.
The live ISO audit now checks metadata as well as file bytes. Never copy the live
overlay onto the real workstation.
