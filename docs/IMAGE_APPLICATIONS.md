# Actual image application layer — 6 November 2026

Brave, VLC, SuperTux and PySide6 now install successfully **inside a temporary
root extracted from the actual retained ISO base**. The resulting additive
SquashFS is built and independently verified. It is **not integrated into a
new full ISO**, boot-tested or approved for installation. QA-container software
and this staged image filesystem are separate artifacts.

## Verified result

| Check | Result |
| --- | --- |
| Base inventory | 2,283 installed packages; the requested browser/player/game/QtWidgets were missing |
| Download transaction | 17 authenticated additions; 342,396,222 bytes; zero existing-package upgrades/removals |
| Offline installation | Actual dpkg unpack/configure succeeds; dependency simulation and final dpkg audit pass; 2,300 installed packages |
| Native application versions | Brave 1.99.55, VLC 3.0.23-1, SuperTux 0.6.3-5, PySide6 6.10.2-6ubuntu1 |
| Filesystem delta | 5,549 changed paths; 5,624 paths including directory ancestors |
| Packed app layer | **383,488,000 bytes**; SHA-256 `22e04836b2e2d0570f248f42306e0a86654202fd5f37561b0d6a0e9d8fbdfd51` |
| Independent extraction | Every captured file hash, link target, numeric owner/group, permission mode and xattr matches |
| Original capabilities | All seven capability-bearing base files excluded from the delta; no original xattrs shadowed, including ancestors |
| Owner policy | No account, sudo/PAM/Polkit, boot or service-policy changes in this transaction; no new file capabilities |
| Native Qt components | Actual Calendar persistence, clock preferences, Paper/Ink rendering and countdown lifecycle pass using the installed image dependencies |

The Qt captures use the **offscreen** backend as ordinary UID 1500. Sources and
palettes are copied under `/run` for the fixture; this does not establish that
the OREZ component package or desktop integration is installed in the new ISO.
Buttons are activated through Qt signals, not physical keyboard/mouse input.
Brave's actual executable, VLC and SuperTux return verified version records.
This is not browsing, YouTube playback, VLC playback or gameplay qualification.
SuperTux needs its documented `SUPERTUX2_DATA_DIR` in this `/proc`-less fixture;
Brave's shell wrapper needs `/dev/fd`, so the final version check deliberately
uses the executable and does not qualify the wrapper or browser sandbox.

Native network packages already present in the base include NetworkManager,
plasma-nm, BlueZ, OBEX, Bluedevil and KDE Connect. Their presence does not test
the MSI wireless hardware, phone pairing, screen mirroring or transfer speed.

## Build components and trust boundaries

1. `environment/orez-image-tools.Dockerfile` supplies a small pinned-base builder:
   Python/APT, dpkg, GnuPG, xorriso and SquashFS tools. Built locally at
   `sha256:e3e83bc9229c3a52afff4df5a701b1ff5ace3c0df14ffdb17c68bfa495378508`,
   **239,706,361 bytes**. It contains no desktop and was not published.
2. `image/desktop-packages.json` is the reviewed build target set, key pins and
   1 GiB download budget. It is not a runtime allowlist or a restriction on the
   owner's software choices. Android/Play and large AI models are deferred.
3. `build/resolve-image-apps.py` resolves against the actual base dpkg status in
   a separate APT root. Ubuntu archive keys come from that base; Brave keys must
   match all three reviewed official primary fingerprints. HTTPS, signed
   repository metadata, payload SHA-256 and APT's `_apt` download sandbox remain
   enabled. The resolver never installs packages or updates the host.
4. `build/stage-image-root.py` accepts a new direct child of `/work` only inside
   a rootless disposable Docker container. It checks the caller-specified ISO
   hash, SquashFS offset and free space before extraction. **A hash passed by a
   caller is not release-signature authentication.** The production outer
   builder must first verify the official signed upstream checksum.
5. `build/install-image-apps.py` requires the separate container to have only
   loopback networking (`--network none`). It verifies the exact base status,
   package hashes and actual Debian control identities, runs read-only APT
   dependency simulation, then dpkg without dependency-forcing flags. Temporary
   `policy-rc.d` prevents service startup and is restored on completion/failure.
   Exact final package state and filesystem policy checks must pass.
6. `build/pack-app-layer.py` rechecks local before/after inventories and original
   ISO identity. It reads original SquashFS xattr metadata directly, refuses to
   shadow any omitted original attribute, packs with fixed timestamps, then
   independently extracts and compares contents/metadata. It does **not** use
   `-all-root`: real package ownership such as `man:man` must survive.

These manifest verifiers consume outputs of the trusted local build. They are
not a signed update protocol and must not accept a downloaded manifest as its
own proof of authenticity. Authenticated packages can still contain vulnerable
or malicious publisher code; package scripts run as root **inside the isolated
builder**, so repository trust and build isolation remain material boundaries.
Do not mount user homes, signing secrets, physical disks, Docker sockets or host
networking into that builder. No privileged container or sandbox bypass is used.

The temporary root omits `/dev`, `/proc`, `/sys`, `/run`, `/tmp` and original
xattrs because this is a constrained build workspace. Normal container null and
urandom devices are bound only at their conventional paths for package tools.
**Never ship this entire staging root as a replacement base.** The unchanged
original SquashFS remains the lower layer. Runtime trees, build logs and APT
caches are excluded from the app delta. Deletions and inode-type replacements
are rejected rather than approximated with untested overlay semantics.

## Repeatable development procedure

Provision at least 80 GiB workspace storage for complete ISO/VM work. Check all
arguments with `--help`; each output path must be new. The verified local layout
is `/work/base-audit` (status/keys), `/work/app-packages-v4` (authenticated pool),
`/work/app-root-v2` (temporary root), `/work/apps-installed-v2` (inventories and
delta), and `/work/app-layer-packed` (packed artifact/report).

```bash
docker build --secret id=qa_ca_bundle,src=/etc/ssl/certs/ca-certificates.crt \
  -f environment/orez-image-tools.Dockerfile -t orez-image-tools:20261105 .
```

Mount only the task work directory at `/work` and the hash-verified input ISO
read-only. Copy the Python build modules/profile into `/work`. Use the online
builder solely to resolve/download; run the installation in a separate rootless
container with `--network none`, the same task directory, and standard null/random
device binds into the new chroot. No host admin capabilities should be added.
In-container invocation sequence (paths refer to those verified inputs):

```bash
python3 /work/resolve-image-apps.py --status /work/base-audit/status \
  --ubuntu-keyring /work/base-audit/ubuntu-archive-keyring.gpg \
  --brave-keyring /work/base-audit/brave-browser-archive-keyring.gpg \
  --profile /work/desktop-packages.json --output /work/new-app-packages
python3 /work/stage-image-root.py --iso /input/orez.iso \
  --expected-iso-sha256 "$VERIFIED_INPUT_SHA256" --offset "$VERIFIED_BASE_OFFSET" \
  --output /work/new-app-root
python3 /work/install-image-apps.py --root /work/new-app-root \
  --bundle /work/new-app-packages --profile /work/desktop-packages.json \
  --output /work/new-installed-apps
python3 /work/pack-app-layer.py --installed /work/new-installed-apps \
  --marker /work/new-app-root.orez-build.json --iso /input/orez.iso \
  --epoch 1793923200 --output /work/new-packed-layer
```

Copy/extract the actual status and keys under those names; do not substitute
the builder's package status. The retained development input used this turn is
`8ec11599942f871759d7a2950b26430c8cb51a35d068283d09f348c2771e40e9`,
with base offset 9,394,176 and base status
`397f502b98cc8fe7721e6e09553d3887b8e0da1f5e231153b3534ceda0531b29`.
It is an old development ISO, not a newly authenticated upstream release.
The expanded root/layer/roundtrip directories were removed after verification to
recover storage. The packed artifact/report, authenticated package pool,
before/after inventories, marker and all evidence remain. Recreate a new root
for further runtime tests; do not assume the old root is still running.
For production, use the upstream signature workflow in BUILD_AND_RELEASE.md
and derive/verify the actual base offset; do not assume offsets remain stable.

APT repositories currently float. Exact versions/hashes/index hashes are
retained, but archive snapshots and source retention are still needed for full
rebuild reproducibility. Fixed SquashFS timestamps alone do not prove two clean
builds produce identical OS images. A failed installation must preserve its
root/logs; do not silently regenerate a baseline from a half-configured root.

## Visible updates, ownership and licensing

Brave updates use the scoped, readable
`/etc/apt/sources.list.d/brave-browser-release.sources` and
`/etc/apt/preferences.d/orez-brave-scope`. Only `brave-browser` and `brave-keyring`
may come from that vendor origin. Ubuntu sources remain unchanged. The owner
can inspect or disable the source through Software Sources or authenticated
editing (`Enabled: no`), and uninstall through normal package management.
OREZ's central settings wrapper and signed OREZ update service remain unfinished.
Disabling a source stops its future security updates; it does not undo code
already installed. Package removal may leave dependencies/preferences behind.

The actual Brave package retains its official root-owned `4755` Chromium sandbox
helper. This is security-sensitive privileged code, **not** a Brave administrator
account. No browser sandbox runtime pass is claimed. No other new set-ID path or
file capability is allowed by this stage. Enterprise management is unconfigured:
no management group/key, configuration opt-in or set-ID management executable.
The packaged cron script's first executable command is `exit 0`; its later
legacy repository code is unreachable in this version. Future vendor changes
need renewed review. Brave's AppArmor profile is present but could not be loaded
in the chroot; actual enforcement must be tested after boot.

Retain each package's copyright/licence records, source package version, required
corresponding sources/offers and browser redistribution notices before publishing
an ISO. This turn publishes **source and screenshots only**, no third-party
package pool or app layer. A public repository does not grant desktop admin
rights; source visibility and software licensing remain separate concerns.

## Remaining first-PC gates

- Bind the app layer to the exact upstream filesystem and package state in the
  production ISO builder; verify casper layer order, package manifests and media
  checksums. Combine the current owner-initrd/live payload and dpkg-owned OREZ
  package. The current `build-live.sh` does not yet consume this app layer.
- Boot offline UEFI through owner enrollment, SDDM and usable Plasma on a
  supported graphical VM host. Test native launchers, Brave sandbox, YouTube,
  VLC playback, games, AppArmor and visible settings in that exact image.
- Complete disposable-disk installation/reboot, non-target preservation,
  encryption, rollback and independent restore. Keep the installer guard enabled.
- Apply and test current base security updates separately; this application's
  no-upgrade policy does not qualify the inherited OS security patch level.
- Complete target hardware, actual 6/16 GiB resource/performance measurements,
  AI permissions, updates, release signing, licence/source obligations and
  repository access audit. The public-to-private transition is still premature.

Official references checked 6 November 2026:
[Brave Linux installation](https://brave.com/linux/),
[Brave signing keys](https://brave.com/signing-keys/),
[Ubuntu apt-secure](https://manpages.ubuntu.com/manpages/resolute/man8/apt-secure.8.html).
SuperTux's installed official man page documents `SUPERTUX2_DATA_DIR`.
See [the evidence ledger](evidence/2026-11-06-image-apps/README.md) and AI_HANDOFF.md.
