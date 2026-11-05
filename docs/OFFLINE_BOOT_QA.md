# Offline live startup and initrd verification

This follow-up fixes a concrete boot delay, not the remaining desktop, installer
or owner-authentication release gates. See AI_HANDOFF.md for exact commits,
executed checks, screenshots and the latest VM outcome.

## Cause and bounded correction

The actual pinned Kubuntu initrd's `41apt_build_cache_cdrom` deletes `.sources`
fragments other than `cdrom.sources` in a temporary overlay, but leaves the
legacy `/etc/apt/sources.list` active. That file contains Internet repositories.
The earlier diskless, network-disabled guest waited on DNS/APT retries during
“Generating APT cache for cdrom”. Both forms of source configuration are read
by APT; removing just fragments does not select local media alone.

The explicitly modified GPL hook in `image/initramfs/scripts/casper-bottom/`
selects `cdrom.sources` and disables fragment discovery for this one command.
It keeps signature verification, bounds optional cache generation to 90 seconds
plus a five-second termination grace, and warns/continues if the source is
missing or the command fails. Normal repository files are not deleted, replaced
or rewritten. This is a boot hook, not a new background service. Its description
and warnings appear in boot logs; the source is the visible configuration point
for this early development milestone. It does not install packages or change
sudo, Polkit, credentials, networking or remote-access settings.

The actual ISO embeds a one-time public signing key in `cdrom.sources`. The
rootless APT fixture must preserve this key. Substituting the ordinary Ubuntu
archive keyring correctly fails with `NO_PUBKEY`; do not bypass signatures to
make a fixture pass. The corrected fixture performs an authenticated update
against extracted actual ISO indexes and verifies unchanged repository bytes.

## Archive and media integrity

`build/patch-live-initrd.py` accepts one pinned upstream initrd SHA-256. It keeps
the first three early archives (67,781,012 bytes, including microcode) unchanged,
replaces exactly one regular root-owned 0755 hook inside the last newc archive,
and recompresses only that final archive with single-thread zstd. Replacing the
new hook with the retained GPL original must recover the exact original CPIO
SHA-256. The verifier bounds input size, decompression output and decoder time;
it never executes archive contents or extracts paths. Other upstream versions
fail closed pending review. See `third_party/casper/` for source and licences.

Initial appended-archive experiments failed independent standard extraction and
were rejected. Their reports remain in the evidence ledger. The final strategy
passes standard `unmkinitramfs` extraction and byte comparisons of the new hook
and both unchanged authentication hooks. It does not depend on extraction tools
honoring a second CPIO trailer inside a concatenated compression stream.

`build/update-media-checksums.py` refreshes the legacy media-error list for the
initrd, its provenance JSON and the two OREZ SquashFS layers. Every unrelated
entry is preserved. MD5 is used only because casper uses that format for media
corruption checks; signed upstream SHA-256 verification and output SHA-256 are
still required. `check-iso.sh` verifies the patch and the four media entries in
addition to the existing payload/disabled-installer checks.

Canonical `build-live.sh` incorporates these changes. A local derivative test
may reuse the previously authenticated OREZ ISO, changing only those boot files;
record its parent digest, patch source revision, resulting digest and size. Such
a derivative is not evidence of a fresh canonical build or release reproduction.
No public ISO or physical installation is approved.

## Owner-authentication blocker

The read-only `build/audit-live-initrd.py` checks the actual extracted hooks.
The pinned initrd contains all three findings: blank live-user password,
`NOPASSWD: ALL` in `25adduser`, and wildcard Polkit grants in
`44pk_allow_ubuntu`. They are unchanged by the boot-delay fix. The audit's
nonzero result is an expected release blocker; a clean pattern scan would still
not prove effective runtime policy. Before sensitive use, implement a reviewed
local owner setup/authentication flow, remove inherited broad grants, and test
sudo/Polkit allow/deny/cancel paths. Never add an AI/vendor bypass or hard-coded
password to get a boot test working.

## References

- [APT source formats](https://manpages.ubuntu.com/manpages/noble/man5/sources.list.5.html)
- [Ubuntu custom APT configuration](https://ubuntu.com/pro-client/docs/en/docs/howtoguides/use_custom_apt_config/)
- [Linux initramfs buffer format](https://www.kernel.org/doc/Documentation/early-userspace/buffer-format.txt)
- [Upstream casper project](https://launchpad.net/casper)

The actual pinned ISO/initrd bytes, independent extraction and recorded runtime
results take precedence over assumptions inferred only from documentation.
