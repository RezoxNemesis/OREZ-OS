# OREZ OS — development live image

**A real 5.46 GB integrated Linux ISO exists. It is not an approved installer or public OS release.**

The image contains the Kubuntu foundation, native Brave/VLC/SuperTux/Qt,
dpkg-owned OREZ Calendar/Reuz/Store components, approved wallpapers and local
owner enrollment. [Exact build inputs, hashes and scope](docs/LIVE_ASSEMBLY.md).
Observed UEFI tests concealed both enrollment password entries,
authenticated the new owner at the console and graphical login, and refused
passwordless sudo. A usable desktop in the booted image is still unqualified;
software graphics and startup remain unresolved. Installation stays disabled.

[Start with the verified handoff](docs/AI_HANDOFF.md). It distinguishes source,
package, image, actual boot, desktop, installation and physical-hardware results.
[Draft development PR](https://github.com/RezoxNemesis/OREZ-OS/pull/1).

[CI on 56af0a2](https://github.com/RezoxNemesis/OREZ-OS/actions/runs/42172398708)
passes **210 source tests, the 38-file package audit and 68 browser cases**.
The full ISO job is skipped; these checks do not certify an installed OS.

## Scope and personality

OREZ is a Linux distribution with a calm sumi-e/paper/glass identity and visible
owner control. It inherits Linux hardware/process/filesystem/network support
and KDE's mature desktop, while developing its own integrated experience.
It does not replace Android or guarantee every application or physical device.

The first PC release prioritizes boot, safe installation, owner login, settings,
native applications, performance measurement, security and recovery. Official
Linux Brave is preferred; YouTube is optional and consented phone mirroring is
planned. Android/Play Store emulation is deferred. OREZ AI remains disabled
until its permission system is implemented and tested. No vendor/AI admin identity,
shipped owner password or unattended installation is added.

- [Single master blueprint](docs/MASTER_BLUEPRINT.md)
- [First PC release and remaining gates](docs/FIRST_PC_RELEASE.md)
- [Boot, account creation and everyday experience](docs/FIRST_BOOT_AND_TOUR.md)
- [Owner control](docs/OWNER_CONTROL.md) and [security architecture](docs/SECURITY.md)
- [Reliability, privacy and performance contract](docs/RELIABILITY_AND_CONTROL.md)
- [Installation and recovery hold](docs/INSTALL_AND_RECOVERY.md)
- [Testing and screenshot rules](docs/TESTING_AND_SCREENSHOTS.md)

## Evidence and downloads

There is **no safe installation download yet**. Do not install development media
on the owner's SSD or overwrite the Windows recovery USB. No physical disk,
firmware or real credential is used by the disposable VM tests.

The [previous 29-screen component tour](https://github.com/RezoxNemesis/OREZ-OS/blob/8fabdcc81cb4e67aa98c6925a9ad8829c3d4ac1f/TOUR.md)
has [245 original PNGs in a direct ZIP](https://github.com/RezoxNemesis/OREZ-OS/archive/8fabdcc81cb4e67aa98c6925a9ad8829c3d4ac1f.zip).
It labels native-container, test-mode, report and historical VM evidence.
[Current integrated-image evidence: 355 original PNGs, about 67 MB](https://github.com/RezoxNemesis/OREZ-OS/archive/564b9298062ff811b3955c976aecf74e90b03a9e.zip)
contains 26 local runs and all six failed commands. [Actual five-screen boot tour](https://github.com/RezoxNemesis/OREZ-OS/blob/564b9298062ff811b3955c976aecf74e90b03a9e/TOUR.md).
Every image hash/PNG decode was verified after downloading the GitHub ZIP;
[verification and scope](docs/evidence/2026-11-06-integrated-live/README.md).

The [phone-friendly preview](preview/README.md) is a separate browser/PWA
prototype. `npm run preview:build` exports its portable HTML. Preview screenshots
are never evidence of an installed or booted desktop.

## Building and testing

Use a Linux x86-64 builder; allow at least 80 GiB workspace for full image,
installation and recovery work. The current 32 GiB lab requires careful staging
cleanup and cannot qualify complete installed-disk scenarios.

Follow [the image assembly instructions](docs/LIVE_ASSEMBLY.md) and
[dependency-stage instructions](docs/IMAGE_APPLICATIONS.md). The canonical builder
requires verified native app and dpkg-owned component layers through
`OREZ_APP_LAYER`, `OREZ_COMPONENT_LAYER` and `OREZ_COMPONENT_REPORT` before it
verifies the signed upstream image. It deliberately refuses missing inputs.
The old manual full-image workflow still needs dependency-job integration;
triggering it repeatedly will not provide those inputs.

[Environment recipes](environment/README.md) cover small image/VM tools and
larger native-desktop QA dependencies. VM tests use ordinary-user QEMU,
private display/control sockets and disposable storage only. Installing tools
does not create KVM, an NVIDIA GPU, working radios or enforced host cgroups.

**Licensing:** Modified casper hooks and retained originals are GPL-2.0-or-later;
see [source and notices](third_party/casper/README.md). Original OREZ source and
wallpaper remain owner-reserved; every upstream licence still applies. Complete
redistribution/source obligations and signed-release gates before distributing
binaries. Keep the repository public until the owner's actual PC-readiness gates pass.
