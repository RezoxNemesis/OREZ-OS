# OREZ Store and native input evidence — 5 November 2026

Implementation: `7fafddf4764528278e6c095e2e52a0c44c5f109d`, branch
`feature/orez-live-foundation-20261104`, draft PR #1. This is a component feature,
not a completed Android runtime, full ISO rebuild or installation release.

## Verified final results

- Exact-commit [CI 42067954280](https://github.com/RezoxNemesis/OREZ-OS/actions/runs/42067954280)
  passes 119 source tests, 28 package payload paths, preview production build and
  68 desktop/mobile browser checks. Decoded job logs `127387318281` verified;
  full ISO job skipped. CI artifact 13434794412 is 210,517,939 bytes, digest
  `bda9b7e8ec65e107b723e6ade0ab9cbf3a288225c851480863e19fe08dd88934`,
  expires 19 November 2026 at 16:49:19 UTC. Metadata/logs verified; artifact ZIP
  not independently downloaded. It contains additional CI screenshots.
- Final native Store: nine scenarios pass with ten catalog entries, search and
  empty state, six Android pending entries, runtime/publisher cancellation,
  installed-native detection, actual ordinary-user VLC launch, local activity,
  close/reopen. Actual Qt widgets and screenshots, not browser simulation.
- Native VLC 3.0.23-1: generated local video advances; default Space pauses and
  resumes; actual right-click menu Pause changes observed playback state; F
  toggles fullscreen and Ctrl+Q exits. No custom mapping or upstream code
  modification. Software decoding only; no physical audio/GPU/full-OS claim.
- Native Brave 1.98.63: official package present, but browser sandbox namespace
  creation is denied by this environment. App does not run; captured log/report
  is a blocker, not browsing proof. No sandbox bypass or host policy weakening.
- Actual final local artifact upgrade 0.1.0-2 → 0.1.0-3 preserves a dummy project,
  disabled wallpaper preference and Android configuration. Ordinary-user dpkg
  denied; privileged operations confined to disposable package test container.
  `dpkg --verify` and audit clean. Final package 278,796 bytes, SHA-256
  `5613fe2cd8a235183697274ffd0d69acdccc40052166f7f056cb40a09f17b0bd`.
- Actual CLI checks confirm no installed/running Android guest or KVM. YouTube
  requests refuse before contacting devices. Mocked adapter tests validate
  bounded commands/identities; they are not real Android playback/game tests.

## Historical attempts and failures

Twenty local attempts are retained. Runs 01–10 include the rejected web-first
proposal; their UI is superseded. Runs 11–14 target real Android, before the
owner requested preference for unchanged Linux browsers. Runs 15–20 implement
that preference. Final GUI binary code is unchanged after run 17; run 20's final
package only corrects the bundled controls documentation wording.

Four command-level failures are preserved:

1. 06: native GUI fixture file unreadable by ordinary test user. Earlier upgrade
   checks inside the same run passed; fixing fixture permissions enabled run 07.
2. 09: APT same-version reinstall failed its local filename resolution. Exact
   local artifact installation and later true version upgrade were tested.
3. 17: nine Store scenarios passed; VLC test wrongly expected `QMenu` in the
   X11 window title. Screenshot showed the actual context menu. Run 18 changes
   the assertion to a real mouse click plus observed paused state and passes.
   Brave also reports a separate sandbox/environment blocker in run 17.
4. 19: minimized container excludes `/usr/share/doc`, causing dpkg verification
   to find two missing documentation files. Run 20 explicitly includes OREZ
   documentation during disposable installation and verifies the final package.

Run 10 compares the same 28 file paths against the retained ISO base with no
collisions, and confirms missing PySide6. It predates final catalog bytes and
must not be called a final image payload/content audit. Source tests were run
before committing; recorded dirty-tree digests and exact-commit CI distinguish
those identities. Both retained ISOs remain unchanged and predate this Store.

## Download and scope

[Download all 232 original PNGs](https://github.com/RezoxNemesis/OREZ-OS/archive/adf0e375b95a18e16813c57046a443ac25dc0952.zip)
from `downloads/screenshots-2026-11-05-store`. The public ZIP is 83,148,334 bytes;
SHA-256 `8876aad72144cf8838cf3d0ba21e2e8e9be74f53be3b258f5b73f82028ce1cdc`.
Downloaded and all 232 hashes matched. Exact duplicates are stored once, with
all 1,000 capture references mapped in the manifest. Open index.html after
extracting. Gallery prominently labels superseded proposals, browser previews,
rendered reports and actual native captures. No real account credentials used.

Local complete evidence: `dist/evidence/qa7-*`; local bundle
`dist/OREZ-store-development-screenshots.zip`, 82,952,924 bytes, SHA-256
`597dbf1b0638e84a6e7abf0575492290c916f0d5c04ef39562c57cff77524241`.
Original outputs and available fixture versions stay local; publication contains
images/gallery/metadata. Final script copies are in `qa7-session-inputs` and are
labelled as final versions, not falsely attributed to earlier attempts.

The temporary QA container was removed after evidence preservation; about
9.9 GiB workspace space recovered/available. Qt dependency changes remain in
`environment/orez-qa.Dockerfile`; no new environment image was published. KVM,
physical graphics, effective resource limits and browser namespace support
remain host requirements. No physical SSD, USB, firmware or owner account used.

The owner later supplied a BlueStacks/Free Fire example. Its documented preset
input translation explains the expected convenience, but does not qualify a
Linux runtime. The owner has now confirmed automatic, visible presets with no manual setup
for Android games. These are planned, not implemented or tested. Native Linux
apps keep their existing controls. See [OREZ_STORE.md](OREZ_STORE.md) for architecture and next gates.
