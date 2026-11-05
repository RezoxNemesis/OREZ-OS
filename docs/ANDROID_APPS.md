# OREZ Android Apps — current implementation and qualification gates

Latest owner scope (5 November 2026): **finish the first PC release before Android emulation.** Native Brave/VLC/Linux games, explicitly authorized web YouTube, owner login, OREZ Calendar/Reuz, themes, AI permissions and connectivity take priority. See [FIRST_PC_RELEASE.md](FIRST_PC_RELEASE.md) for implementation, test limits and blocking gates. No installable release is approved. This supersedes older Android-first and web-YouTube-prohibited statements for the first release only.

The owner requires a real Play Store experience for Android YouTube and games,
starting with **free casual games**. This is a core requested capability, not a
browser mock-up. **Working consumer Play Store support is not yet delivered.**

## What is implemented now

The native **OREZ Android Apps** launcher opens a KDE dialog with status, optional
setup, start, stop, memory/graphics settings, logs, reset and removal. The backend
uses Python standard-library APIs, runs as the normal user and rejects root.
It is installed through the same explicit package/installer allowlist as OREZ's
other components. No Google software, APKs, credentials or system images are
bundled; no daemon, administrator rule, firmware change or autostart is added.

An **experimental development/testing provider** integrates Google's official
Android Emulator and the explicit package
`system-images;android-36;google_apis_playstore;x86_64`. A `google_apis` image alone
does not imply the Play Store. SDK bootstrap is pinned to the Linux command-line
tools archive `15859902` and the SHA-256 published on Google's download page;
the reviewed repository metadata also advertises newer tools, so this bootstrap
pin is an intentional reviewed snapshot, not a claim to be the newest release.
Further packages are downloaded/verified by SDK Manager; installed versions are
recorded rather than falsely described as a fully reproducible Android image.

**Licensing boundary:** Android SDK terms §3.1 grant use solely to develop apps
for compatible Android implementations; §3.4 restricts other use/redistribution.
Consequently this developer provider must not be presented as a blanket licence
for an everyday consumer Play Store built into a distributed OS. SDK setup
requires interactive licence acceptance and is not run silently by OREZ or CI.
No SDK/image was installed or booted in this session. A qualified/licensed
consumer provider remains a release blocker. Do not spoof Play Integrity,
certification or device identity to make a game appear supported.

## Visible controls

| Control | Location / behavior |
|---|---|
| Open manager | KDE launcher → OREZ Android Apps; `orez-android gui` |
| Status | Manager → Status; `orez-android status`; read-only, no installation |
| Setup | Manager → Setup; separate terminal shows official SDK terms and prompts |
| Start | Manager → Start; requires readable/writable `/dev/kvm`, existing profile; no silent CPU fallback |
| Stop | Manager → Stop; validates owned emulator PID, start time, executable and process group |
| Memory/graphics | Manager → Memory and graphics; 2/3/4 GiB, software or auto; default 2 GiB below 8 GiB host RAM, otherwise 3 GiB; 2 CPU/software |
| Storage/logs | `~/.local/share/orez/android/` by default; `config.json`, `sdk/`, `avd/`, `logs/`; honors `XDG_DATA_HOME` |
| Reset | Destructive confirmation; deletes only managed Android app/account data and recreates the profile |
| Remove | Destructive confirmation; removes managed SDK/guest data, retains settings/action logs |

CLI reset/removal additionally requires the exact phrase
`--confirm 'DELETE OREZ ANDROID DATA'`. It refuses symlink storage, unrecognized
directories and foreign process identities. Private state is mode 0700/0600.
ADB uses a dedicated localhost endpoint on port 5038; no network-wide ADB server
or host shared folder is requested. The runtime's actual socket bindings and
camera/microphone/clipboard defaults still need guest testing and explicit
controls before consumer qualification. Guest-account credentials never enter
OREZ settings or test logs. Stop screenshots during any real account login.

The proposed 3 GiB guest fits the owner's 16 GiB budget in principle. Actual
Ryzen 5600 KVM, NVIDIA graphics, RAM pressure, x86/ARM app compatibility and game
behavior remain untested. Start with conservative software graphics; qualify
GPU auto mode on the RTX 3050 separately. Enable SVM or KVM group access only
through a visible owner/admin action; the manager never performs those changes.

## Remaining product work

1. Select and review a consumer Android provider and a lawful Google Play
   distribution/personal-installation path. Compare a maintained Android VM
   against Waydroid's binder/shared-kernel requirements and its NVIDIA rendering
   constraints. Do not turn this into an unreviewed root service or quietly
   substitute untrusted Google-app bundles. Keep the optional SDK provider
   explicitly for permitted Android development/testing.
2. Obtain a KVM-capable environment and qualify an actual guest boot, console,
   app lifecycle, networking, Play Store availability and graceful recovery.
3. Let the owner sign into Google privately inside the guest. Download a chosen
   free casual game and Android YouTube through the actual Play Store. Record
   package/version, install/uninstall, input, rotation, playback, frame pacing,
   guest/host resource usage and data retention across restart. No purchases or
   account credentials are part of automated tests.
4. Verify no host-admin access, home/disk/USB sharing, inbound ADB or unexpected
   integration; add visible revocable clipboard/microphone/camera controls.
5. Test offline behavior, revoked permissions, interrupted downloads, storage
   exhaustion, safe reset and removal, isolation and recovery. ARM-only/DRM/
   emulator-restricted games must be listed individually as unsupported where
   observed; never promise all Play Store software will run.

## Official references checked on 5 November 2026

- [Android Emulator](https://developer.android.com/studio/run/emulator)
- [AVDs and Play Store images](https://developer.android.com/studio/run/managing-avds)
- [Linux/KVM acceleration](https://developer.android.com/studio/run/emulator-acceleration)
- [SDK Manager](https://developer.android.com/studio/command-line/sdkmanager)
- [Command-line tools and published checksum](https://developer.android.com/studio)
- [Android SDK terms](https://developer.android.com/studio/terms)
- [Official Play system-image metadata](https://dl.google.com/android/repository/sys-img/google_apis_playstore/sys-img2-1.xml)

## Store integration follow-up — 5 November 2026

Read [OREZ_STORE.md](OREZ_STORE.md). The Store now targets actual Android apps;
web shortcuts are removed. Official Linux editions are preferred unchanged.
The source adapter adds `app-status`, `open-app`, `store-page`, `app-settings`
with reviewed `--app` aliases and `--development-test`. It validates the owned
AVD and targets only dedicated loopback ADB/serial; no host browser substitution,
phone command, APK mirror or automatic purchase. Its controlled source tests
are not a real Android run. Consumer installation stays blocked. Direct keyboard
and mouse support without custom mapping is a per-app acceptance gate; it is
not guaranteed merely by running Android in an emulator.
