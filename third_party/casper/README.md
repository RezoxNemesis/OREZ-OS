# Ubuntu casper boot-hook modification

`image/initramfs/scripts/casper-bottom/41apt_build_cache_cdrom` is an explicitly
modified version of Ubuntu casper's hook, licensed GPL-2.0-or-later. COPYRIGHT
preserves the notice supplied in the pinned Kubuntu filesystem. COPYING is the
complete GPL version 2 text. This licence applies to the derived hook regardless
of the repository's licence for original OREZ components.

The adjacent `41apt_build_cache_cdrom` is the unchanged original used to verify
that repacking alters exactly one hook. Both original and modified hook retain
this upstream licence.

Input: official Kubuntu 26.04.1 amd64 ISO, SHA-256
`831e4d4bb85098339ba43d3502cd6619b27e76daf37246a084cd68a6413090b8`.
Unmodified initrd SHA-256:
`0d34300a307d5dd3fbb0ff61e5b43ee3887bcc2d0f6523d600714767f6df4092`.
Unmodified hook SHA-256:
`fd3768b7b303b61cefe52fb00c9452738f7f83e98ebe4834f9dc61092f7a66fa`.

OREZ change, 5 November 2026: select `cdrom.sources` for this one APT update,
disable other source fragments for that command, remove unnecessary overlay
mounts/repository deletion, and bound this optional cache update to 90 seconds
plus a five-second termination grace. Missing/bad media cache warns and allows
startup to continue. No signature checks, normal update repositories, sudo or
Polkit permissions are weakened or changed by this patch.

Ubuntu source project: https://launchpad.net/casper
The matching source package/version must be included in the release source
inventory before binary redistribution. This repository supplies the modified
hook source; no complete OREZ binary release is currently approved.
