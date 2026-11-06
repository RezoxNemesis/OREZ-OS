# Offline installer candidate — inactive

The current ISO still blocks installation. This work prepares reviewed Calamares
configuration; it does not install OREZ or qualify an SSD download. The graphical
desktop, disk selection, installation, reboot, encryption and recovery gates
remain open. See [installation gates](INSTALL_AND_RECOVERY.md).

## Actual-source inspection

`build/inspect-installer-source.py` reads the integrated ISO by verified byte
extents, without extracting a second 4.38 GB base filesystem. It checks the
base/app/component integrity, extracts the actual Calamares configurations,
records their hashes, and compares the live installer guard to source. The old
payload-collision wrapper now invokes this inspector: the integrated component
layer intentionally includes four reviewed dpkg database files as well as its
38 payload paths. It must not be judged as the obsolete payload-only layer.

The actual base has Calamares **3.3.14-0ubuntu25** and a stock unpack configuration
that copies only the original base. That would omit the native application and
OREZ component layers. The inherited live AppArmor override must also be
excluded from an installed system. Successful inspection reports these blockers;
it never turns them into an installation pass.

## Candidate generation

`image/installer/profile.json` pins 30 actual source configuration hashes, the
original filesystem identity, Calamares and the already-installed UEFI bootloader
packages. `build/prepare-installer-profile.py` verifies these inputs and writes
eight changed configuration files into a **new staging directory**. It refuses
stale/ambiguous changes, existing outputs, symlink destinations and system
configuration destinations. Generated output hashes must match the reviewed
profile. No installer activation helper is supplied.

Changes prepared:

- Copy base, native apps, then dpkg-owned OREZ components; exclude the known
  live AppArmor override. Do not copy the live owner/installer-blocking layer.
- Remove optional package selection, mirror changes, online bootloader package
  selection, language downloads and GeoIP lookup from this offline candidate.
  Retain the actual UEFI bootloader packages already present. Initial timezone
  is UTC and remains editable. Internet is not a prerequisite in this profile;
  an actual disconnected installation still has to prove it.
- Create the owner's local account with 12–128 character password requirements,
  home directory mode 0700 and root password login disabled. Initial autologin
  is off. Calamares's `doAutologin` controls the initial checkbox, not an
  immutable prohibition. No domain enrollment is offered.
- Start with no partitioning choice selected. Btrfs is the default filesystem;
  manual choice and upstream LUKS2 options remain. The unencrypted boot warning
  is visible. Btrfs swap, subvolumes and encrypted reboot are still unqualified.
- Remove only eight exact live/installer packages. Preserve `cifs-utils` for
  Windows/SMB network shares. Do not use broad package-removal regular expressions.
- Set the default desktop executable to `startplasma-wayland`.

The provisional 32 GiB disk and 2 GiB installer-memory checks are **not** a
measured installed footprint or a performance promise. Original installer
branding and installed OREZ login-theme packaging still need integration.

Example, on an isolated builder with the recorded inputs:

```bash
python3 build/inspect-installer-source.py --iso /path/candidate.iso \
  --sha256 ACTUAL_RECORDED_SHA256 --output dist/installer-source-new
python3 build/prepare-installer-profile.py --source dist/installer-source-new \
  --base-status /path/original-base-status --output dist/installer-profile-new
python3 build/check-installer-removals.py --status /path/final-layer-status \
  --sha256 ACTUAL_STATUS_SHA256 \
  --packages-conf dist/installer-profile-new/etc/calamares/modules/packages.conf \
  --output dist/installer-removal-new
```

The last command requires `python3-apt`; use the image-tools container with
`--network none`, read-only input mounts and a separate writable staging mount.
It uses only the actual installed dependency graph in a temporary APT root.
It never updates repositories, fetches packages, commits a transaction or runs
maintainer scripts. Any extra removal, install/change or broken dependency
refuses qualification. A successful simulation is not an installation result.

## Verified preparation and remaining gates

6 November 2026: actual-source extraction captured 30 configuration identities.
The final dependency simulation against all **2,301 installed records** scheduled
only the eight intended removals, with zero broken dependencies. Source/native
boot/package/runtime gates are tracked separately in the handoff. A failed local
test-launch command is retained alongside the successful corrected run.

`build/audit-installed-root.py --owner OWNER --strict` also checks unique owner
UID, root UID/password lock, a configured owner password hash, known admin groups,
shadow permissions and known passwordless-sudo tags. It never prints password
hashes. This is scoped static inspection: SSH/PAM/Polkit, custom sudo includes,
privileged services and effective permissions require runtime tests.

Next: integrate branding and installed authentication/theme packaging, qualify
the usable live desktop, then exercise this configuration in an explicitly
identified disposable-disk VM. Check cancellation/non-target disk preservation,
generated fstab/crypttab, owner permissions, package database, native apps,
UEFI boot without the ISO, LUKS unlock, update failure and recovery. Never
activate this profile on the owner's SSD or infer success from its generation.

Upstream references:

- [Calamares users configuration, v3.3.14](https://github.com/calamares/calamares/blob/v3.3.14/src/modules/users/users.conf)
- [Calamares partition configuration, v3.3.14](https://github.com/calamares/calamares/blob/v3.3.14/src/modules/partition/partition.conf)
- Modified distribution configuration and all bundled dependencies retain their
  licence/source obligations; release clearance is still a separate gate.
