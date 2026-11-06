# OREZ OS: first boot, everyday experience and evidence

Status: 6 November 2026. **Development components, not an install-ready release.**
The tour distinguishes actual native component tests, historical VM evidence,
planned behavior and blocked checks. No image in this tour proves physical-PC
compatibility. The 45 future ideas are in [EXPERIENCE_IDEAS.md](EXPERIENCE_IDEAS.md).

## What the finished installation should ask

1. The motherboard briefly shows its firmware logo. Select the separate OREZ
   USB's UEFI entry from the one-time boot menu. OREZ cannot replace the board's
   firmware splash simply through a desktop theme.
2. The intended media offers **Try OREZ**, **Install OREZ** and troubleshooting /
   safe graphics. These are operating modes of one OREZ edition, not a selection
   of Linux distributions. The current integrated image offers Try OREZ (installation unavailable)
   and safe graphics; its inherited boot splash still says Kubuntu.
3. Try mode runs a temporary live session. Current integrated owner enrollment asks
   twice on the local console for a temporary 12–128-character password before
   starting SDDM. The latest actual UEFI run concealed both entries and authenticated
   the new owner; this is not installation or broad security certification. Nothing should silently write to the internal SSD.
4. The intended installer asks language, keyboard, time zone, optional network,
   the owner's name/password, and a **clearly identified disk and partition
   plan**. Encryption and any dual-boot choice receive separate explanations.
   Show all deletions/resizes before a final destructive-action confirmation.
   The current OREZ installer launcher is deliberately blocked; this flow is
   a requirement, not an implemented successful installation.
5. After installation and USB removal, the PC boots OREZ. If disk encryption is
   enabled, expect an unlock prompt before the login screen unless a separately
   qualified unlock design is chosen. Do not promise a single password prompt.
6. The OREZ login theme says **“Welcome home. Your workspace. Your control.”**
   Choose the owner user and enter the local password. No Google or Microsoft
   account is needed. A desktop-session selector, when present, selects an
   installed desktop session, not another Linux distribution.
7. The approved paper-and-ink wallpaper, taskbar and launcher lead to the
   desktop. A future first-run guide should offer display scaling, network,
   phone pairing, backups, privacy controls and an optional tour. Skip/return
   must be available. The current welcome component is a local HTML help page,
   not a completed first-run wizard.

A password is created during the intended installation: OREZ does **not** wait
until later and leave the administrator unprotected. Root login stays locked.
Any future optional automatic desktop login must require deliberate owner
configuration and must not remove administrator authentication or encryption.
No vendor or AI receives an administrator identity.

**Account creation is separate from sign-in.** The installer/first setup must
create the selected local username and password before showing normal login.
Typing a new name/password into SDDM does not register an account; incorrect or
unknown credentials must be rejected without revealing unnecessary account
details. OREZ's visual design uses established Linux/PAM authentication rather
than a new online identity service. In the tour's test-mode screenshot, “No
desktop session found” concerns available session startup, not online account
registration. The live create-account and authenticate steps now have actual VM evidence.
A usable desktop and the installed-system sequence remain release gates.

## Internet and disk space

Offline core installation is a release requirement, **not yet a passed test**.
The final image must contain its core desktop, installer, recovery essentials
and approved preinstalled applications. A qualified offline NVIDIA driver path
is still required. Network is needed for YouTube, new downloads, updates and
cloud AI; local files, native games already installed, Calendar and Reuz should
work offline. Wi-Fi setup should be skippable and recoverable in Settings.

| Item | Measured or estimated size | Meaning |
| --- | --- | --- |
| Current integrated development ISO | 5,455,347,712 bytes, about 5.46 GB / 5.08 GiB | Measured; installer disabled; **not a release download** |
| Native-app SquashFS within that ISO | 383,488,000 bytes, about 383.5 MB | Measured; already included in the ISO size above |
| Finished installation | Provisional 25–35 GB engineering budget | **Estimate only** until an actual clean install is measured; not a minimum-size certification |
| Comfortable system allocation | Plan around 80–100 GB if existing data/layout permits | Recommendation allowing updates and apps; games, models, swap and backup/snapshot retention may need much more |
| Installation USB | Separate 16 GB or larger drive recommended | Planning allowance, not permission to erase any drive; preserve the Windows recovery USB |

ISO compression, installed files and free-space reserve are different quantities.
The app layer is already included in the ISO; neither size is installed disk usage.
The 500 GB SSD has about 466 GiB total capacity before existing partitions. No
allocation is chosen until its actual layout and backup status are reviewed.

## What makes it OREZ, and what it inherits

OREZ remains a Linux distribution. Linux supplies the kernel, process/memory
management, filesystems, driver framework and networking. Kubuntu/Ubuntu add
packages and maintenance infrastructure; KDE provides mature windows, desktop,
Dolphin, Settings and device integration. This is a strong foundation for a real
PC, but it does not finish OREZ's installer, permissions, update/recovery design,
NVIDIA/Secure Boot integration, phone workflow or target-hardware qualification.

Linux is software, not an outside administrator. It does not independently take
ownership of the PC. The kernel necessarily has control over hardware; trusted
system services, drivers and authorized package installation may run with root
privileges. Their bugs or compromise remain risks. OREZ must review dependencies,
verify updates, minimize services and preserve owner-controlled permissions.
“No vendor admin account” is different from “no upstream code is trusted.”
Public repository reading/forking does not grant write access or PC control.
The separate collaborator/access audit remains incomplete.

The personality is calm Japanese ink and handmade paper, restrained glass,
readable typography, deliberate motion, clear status and visible owner control.
The two owner-supplied wallpapers and Paper/Ink palettes exist now. The current
native tour still shows familiar KDE icons and layouts; an entirely original,
polished shell is not claimed. Effects should have accessible solid/reduced-
motion modes. The five new theme proposals are not implemented palettes.

| Experience | Familiar capability | OREZ distinction / remaining work |
| --- | --- | --- |
| Desktop | Windows, taskbar, launcher, search, multiple workspaces | OREZ art/palettes and own apps; broader shell polish remains |
| File manager | Folders, drives, copy, rename, trash, search | Dolphin also offers tabs/split views; physical USB/MTP still needs testing |
| Applications | Native installers/packages and optional stores | OREZ Store is a visible catalog/launcher with compatibility gates, not the exclusive installation route |
| Calendar/time | Local events, clocks, timers, stopwatch | Original OREZ Calendar and Reuz components; no mandatory cloud account |
| Video | Native VLC, playback controls and fullscreen | Local generated-video controls tested; NVIDIA decode, real speakers and online streaming unqualified |
| Games | Native Linux games; optional Steam/Proton later | SuperTux test only; anti-cheat/Windows/Android compatibility is per game |
| Phone | KDE Connect, Bluetooth, network/tethering tools | Unified consent/permissions direction; real phone transfers and mirroring still pending |
| AI/security | Ordinary permissions, authentication and updates | OREZ AI is disabled; no autonomous detection or privileged AI agent is installed |
| Recovery | Upstream recovery building blocks | OREZ signed releases, installer recovery and rollback must still be implemented/qualified |

Some Windows applications will require alternatives, Wine/Proton or a licensed
VM; compatibility is not universal. The native applications retain their own
interfaces. A lightweight desktop cannot guarantee no lag, buffering, hangs,
thermal throttling or crashes. Measure frame times, memory pressure, power and
recovery on the actual Ryzen/RTX machine before making performance comparisons.
6 GiB remains an unqualified target profile; the real computer has 16 GiB.

## Fullscreen and privacy

VLC normally supports fullscreen with F; games have their own display settings.
The current tour tests VLC's actual fullscreen state and SuperTux's actual
1440×900 window. Software-rendered container results are not GPU benchmarks.
Online buffering depends on network, service/CDN and codec/driver behavior.

Brave is a native Linux application, but its sandbox cannot start in this
workspace's restricted nested namespaces. That is recorded as **blocked**;
no sandbox was disabled to manufacture a browsing pass. YouTube playback is
therefore also unverified here. The owner now treats YouTube as optional for the first PC release and prefers
phone mirroring when useful. Use official native Linux Brave. scrcpy mirroring
requires explicit Android debugging authorization and a connected phone; KDE
Connect alone does not provide the phone screen. Phone audio/DRM behavior and
actual mirroring remain unverified. Consumer Android/Play Store and automatic game presets are deferred.
No APK downloads, Google login, real purchases or financial accounts are tested.

## Tour evidence rules

The downloadable tour provides a screen and a scope label for every included
stop. Actual native UI screenshots are separate from test-report screenshots.
A historical GRUB screen is explicitly dated and tied to the old unsafe ISO.
The installer stop shows the real safety blocker. The login stop is SDDM test
mode with no usable desktop session in this environment, not successful login.

Unimplemented features cannot honestly have a working screenshot or practical
pass. Their design, acceptance tests and blockers are documented instead. A
comprehensive component tour is not a claim to have tested every OS capability,
a completed install, target-PC hardware, power-loss recovery or malware immunity.


## Open the actual tour

[29-screen tour with a screenshot at every stop](https://github.com/RezoxNemesis/OREZ-OS/blob/8fabdcc81cb4e67aa98c6925a9ad8829c3d4ac1f/TOUR.md)
— [direct ZIP, 245 original PNGs and offline tour](https://github.com/RezoxNemesis/OREZ-OS/archive/8fabdcc81cb4e67aa98c6925a9ad8829c3d4ac1f.zip).
About 105.9 MB. The archive contains all failed attempts too. See
[evidence and verification](evidence/2026-11-06-experience-tour/README.md).
