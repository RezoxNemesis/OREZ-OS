# Publish the OREZ test environment

These are **development dependencies**, not a release ISO or a promise that
hardware capabilities can be created inside a container. The owner authorized
installing missing test tools and intends to publish the environment. No cloud
environment publication API is available in this session; publish this definition
through the environment's configuration UI. Do not silently publish an image or
change host security policy.

## Build once, reuse the layers

From the repository root on a Docker-enabled Linux x86-64 builder:

```bash
docker build -f build/integration/Dockerfile -t orez-package-test:20261105 .
docker build -f build/integration/Desktop.Dockerfile -t orez-desktop-test:20261105 .
docker build --secret id=qa_ca_bundle,src=/etc/ssl/certs/ca-certificates.crt -f build/integration/Everyday.Dockerfile -t orez-everyday-test:20261105 .
docker build --secret id=qa_ca_bundle,src=/etc/ssl/certs/ca-certificates.crt -f environment/orez-qa.Dockerfile -t orez-qa:20261105 .
```

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

Image `orez-qa:20261105` built successfully in qa3-25 with ID
`sha256:3d500a65817e2d44d70a90d63ffab2db8fb0d3688a7c0bb66eae7af4c5215308`
and about 4.22 GB logical size. It defaults to `orez-test`; pass
`--workdir /home/orez-test` at runtime if desired. Build preflight and exact package
versions are in `/opt/orez-qa/`. QEMU and Java executables ran, but no KVM/GPU
exists in the builder. The final image is retained locally, not published.

The 32 GiB VFS host has insufficient remaining storage to start another copy of
this image. Native Wi-Fi/Bluetooth dialog/password/search checks remain pending
on the larger host. Do not repeatedly retry the same disk-limited operation.
