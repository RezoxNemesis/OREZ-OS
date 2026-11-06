# Installer preparation and actual native desktop diagnostic — 6 November 2026

**Normal graphical login remains blocked; no installation release.** A separate
ordinary-owner console launch renders real native desktop elements and Settings.
A screenshot proves the visible state, not every capability in that window.

## Exact download and scope

[Download all 301 original PNGs](https://github.com/RezoxNemesis/OREZ-OS/archive/090a5014051e3d230a4a04300d3395f58dedf7a4.zip)
(57,778,908 bytes; about 58 MB).
[12-screen actual guest tour](https://github.com/RezoxNemesis/OREZ-OS/blob/090a5014051e3d230a4a04300d3395f58dedf7a4/TOUR.md).
Extract the ZIP and open `index.html` for every captured report/frame. The archive
maps 512 references across 21 runs; exact duplicate images are stored once.
Its two failed commands and failed guest acceptance checks remain visible.

GitHub ZIP SHA256: `772797e4e22546baf877b04581959c922bf083689b97345c9831d22e84de924d`.
Every downloaded PNG hash and decode matched the manifest. The subsequent
qa12-22 verification runs after the frozen archive; its
[report screenshot](download-verification.png), [result](github-download.json)
and [run identity](download-verification-result.json) are separate evidence.
The local ZIP has different packaging/metadata; [local identity](local-bundle.json)
is not the GitHub download hash. Neither archive contains an OS installer.

## Implementation and actual outcomes

Image source `56af0a24133985d225ac22c2e85a6f3cb050f483`, ISO SHA256
`6ca85cf37d48beeb8ac0fd6ffa99e94cc9806949584a970916024ddf30d80ac6`,
5,455,347,712 bytes. [Assembly identity](iso-direct-session.json).
It selects the direct native OREZ Desktop session instead of the inherited live
installer-prompt wrapper. The original filesystem, native-app and dpkg-owned
component layers remain independently checked. This is a development-parent
reconstruction, not fresh signed/security-updated release qualification.

Normal default-menu UEFI boot (qa12-17, no changed kernel flags) concealed both
enrollment entries and completed owner setup. Real SDDM refused an incorrect
password and accepted the correct one. The selected session then exited **64**
and restarted the greeter. Authentication succeeded; full desktop startup did
not. [Selected actual journal](guest-journal-excerpt.json) and
[final exact run scope](qa12-17-vm-result.json). Exit64 alone is not a generic
GPU diagnosis; the [official source review](startup-source-review.json) does not
establish the runtime cause. Actual distro wrappers/profiles were also inspected.

Separate later diagnostic: an ordinary authenticated owner shell ran
`startplasma-wayland` with no root, compositor override or authentication/sandbox
bypass. Actual KWin, Plasma and Welcome processes appeared; no systemd jobs
remained at the inspected instant. The real wallpaper, icons, panel/system tray
and clock eventually rendered. Clicking Skip closed Welcome; clicking native
Settings opened its actual Quick Settings window. Search, Bluetooth, Wi-Fi,
display and accessibility routes are visible. No setting was changed and no
network or radio was exercised. Inherited Kubuntu icons and themes remain.
Normal login, whole-desktop lifecycle, apps/games, performance, installation and
recovery are not qualified by this separate diagnostic.

The VM used ordinary-user QEMU, 6 GiB guest RAM, 2 vCPU, TCG and virtio-vga 2D;
no network, writable guest disk or host device. 212 actual qa12-17 PNGs decode.
Only private random disposable credentials were used. A tty test-driver timeout
partly echoed one dummy credential as a new username; that failure is retained.
Missed OCR and OCR-timeout attempts are also retained, with later successful
prompt-observed retries. These are not established guest kernel crashes. The
bounded observation ended through harness cleanup. All task containers, QEMU
processes and temporary credentials were destroyed before publication. No owner
SSD, firmware, Windows recovery USB or real credential was accessed.

Earlier [qa12-02](qa12-02-vm-result.json) stopped safely before reading a password
because the splash process did not exit; [qa12-08](qa12-08-vm-result.json) reached
the inherited live installer prompt, with no usable Plasma qualification. Their
capture-command success does not change those guest acceptance outcomes.

Installer inspection reads 30 actual pinned configurations. The
[inactive candidate](inactive-profile.json) includes app/component layers and
owner-account policy, excludes live-only security overrides and avoids optional
network downloads. Final [offline removal simulation](removal-plan.json) removes
only eight requested live/installer packages; `cifs-utils` remains. The earlier
nine-package proposal is retained in the archive as superseded. No package
maintainer script, partitioning or disk installation was executed.

Latest implementation `02acdac3acbd64472d73c5d4ea4320c6afef9bd3` fixes a static
shadow-audit false pass by checking root ownership, safe mode and target-root
group access. [CI 42176829799](https://github.com/RezoxNemesis/OREZ-OS/actions/runs/42176829799)
passes 214 source tests, 38 package paths and 68 browser-preview cases; full ISO
job skipped. [Artifact identity](ci-shadow-audit.json). CI captures are separate
in that Actions artifact and expire on 20 November 2026. Source tests, package
checks and preview images do not establish effective installed-system security.

The parallel [reliability contract](../../RELIABILITY_AND_CONTROL.md) maps the
owner's reference complaints to implementation gaps and unexecuted acceptance
cases. Update recovery, privacy/service inventory, drivers, background resources,
settings, whole-system security and target-PC performance remain release gates.

## Local command ledger

`result.json` describes the command, while `vm-result.json` separately assesses
observed guest behavior. “Passed” below never overrides a blocked guest result.
qa12-12 failed because its temporary helper was absent; qa12-20 failed on an
inspected symlink. Their corrected retries and original report PNGs are retained.
[Full run identities](local-runs.json).

| Run | Command result | Report PNGs |
| --- | --- | ---: |
| qa12-01-graphics-preflight | passed | 1 |
| qa12-02-qpaint-uefi | passed | 1 |
| qa12-03-actual-installer-source | passed | 2 |
| qa12-04-source-regression | passed | 11 |
| qa12-05-complete-installer-source | passed | 2 |
| qa12-06-owner-installer-regressions | passed | 11 |
| qa12-07-slow-splash-iso | passed | 3 |
| qa12-08-nosplash-qpaint-uefi | passed | 3 |
| qa12-09-prepare-installer-profile | passed | 2 |
| qa12-10-installer-profile-regressions | passed | 12 |
| qa12-11-offline-removal-plan | passed | 2 |
| qa12-12-offline-installer-final | failed | 1 |
| qa12-13-offline-installer-final-retry | passed | 3 |
| qa12-14-final-source-regressions | passed | 12 |
| qa12-15-direct-session-regressions | passed | 12 |
| qa12-16-direct-session-iso | passed | 3 |
| qa12-17-direct-session-default-uefi | passed | 3 |
| qa12-18-shadow-policy-regressions | passed | 12 |
| qa12-19-session-source-inspection | passed | 5 |
| qa12-20-login-profiles | failed | 2 |
| qa12-21-login-profiles-retry | passed | 11 |
| qa12-22-published-download | passed | 1 |

All native frames are captured displays. Report PNGs reproduce test output;
browser-preview CI captures remain labelled previews. No signed ISO, installed
footprint, physical NVIDIA/radio/Secure Boot, power/FPS, Android or autonomous AI
qualification is claimed. The installer remains guarded and the PR remains draft.
