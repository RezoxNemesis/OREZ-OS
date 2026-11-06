# Connections, phone sharing and removable storage

Latest owner clarification (6 November 2026): use the official **native Linux Brave** browser. YouTube is optional for the first release; prioritize consented phone screen mirroring through scrcpy. KDE Connect handles pairing/transfers/controls, not Android screen mirroring by itself. Actual mirroring and phone audio remain unverified without the Realme connected.

The owner wants simple Wi-Fi/internet/Bluetooth controls, Android screen mirroring,
phone-to-PC internet sharing, and file transfers over the network, Bluetooth or
USB. Reuse native Linux services. Actual MSI radio, Realme phone and USB-device
qualification is still pending; this workspace has none of those devices.

## Visible paths and providers

| Task | Native path / component | Consent and limits |
|---|---|---|
| Wi-Fi or Ethernet | System Settings → Wi-Fi & Networking / Connections; `orezctl network`; NetworkManager + plasma-nm | Owner selects network and enters credentials locally; no automatic connections to unknown APs |
| Status | `orezctl network-status` | Read-only state/device types, no saved passwords or automatic network changes |
| Phone hotspot → PC | Enable hotspot on Realme; select it in PC Wi-Fi settings | Prefer supported WPA2/WPA3; data usage is the phone plan; test reconnect and metering |
| USB tethering | Connect a data-capable cable, enable Android USB tethering, select detected wired link | USB 2.0 is sufficient; no HDMI assumption and no automatic USB debugging |
| Bluetooth | System Settings → Bluetooth; `orezctl bluetooth`; BlueZ/Bluedevil | Compare pairing code on both devices, pair explicitly; discoverability is temporary |
| Bluetooth files | Native Bluetooth send-file UI + OBEX | Pair and accept transfer on receiver; slower than Wi-Fi; verify incoming-transfer controls and actual Realme compatibility |
| LAN files/notification controls | OREZ Connect / KDE Connect | Confirm pairing on both devices; per-plugin consent, progress, unpair/revoke. Clipboard and input controls are opt-in |
| USB stick | Dolphin → removable device; `orezctl files` | Browse/copy, verify completion, then safely eject. Never autoformat or autorun executables |
| Phone USB files | Android File Transfer/MTP mode + Dolphin/KIO | Owner unlocks phone and allows file access; cable must carry data; MTP is not a normal mounted POSIX filesystem |
| Screen mirroring | Optional official scrcpy, initiated by owner | Android debugging authorization is powerful and revocable. Start with view-only `scrcpy --no-control --no-audio`; remote input is an explicit separate choice |

The package suggests optional network/Bluetooth/MTP/scrcpy components; the full
OS image must verify its required package inventory before claiming these pages
work. The QA dependency image includes NetworkManager, plasma-nm, BlueZ,
Bluedevil, OBEX and KIO. Installing them alone does not establish a functional
system bus, radios or a successful connection. Native command shortcuts are
implemented; no new connection daemon, pairing protocol or privileged helper
was added.

Use the official KDE Connect Android app initially. Standard pairing remains
the initial tested target; do not claim a custom QR pairing flow exists. KDE
Connect can use a local network without internet, but hotspot/client isolation,
VPNs and firewalls can prevent peer discovery. Diagnose before changing rules.
Scope any required KDE Connect TCP/UDP 1714–1764 rule to a trusted LAN interface/
subnet; never expose it on a public network or silently open all firewall ports.
Use existing TLS pairing and visible device revocation.

scrcpy is **phone mirroring**, separate from running Android apps locally in a
PC emulator. It does not require USB-C video output. Never enable ADB over the
LAN without a visible owner action and supported authenticated pairing; never
bind unauthenticated ADB globally. Show how to stop mirroring and revoke the PC's
Android debugging authorization. Do not capture account/password entry.

## Acceptance matrix before claiming support

1. Record actual PCI/USB chipset IDs, firmware/driver versions and blocked-radio
   state. Test Wi-Fi 2.4/5 GHz where supported, Ethernet, DNS, IPv4/IPv6, captive
   portal, offline mode, suspend/resume and reconnect. Verify no credential logs.
2. Test Realme hotspot and USB tethering independently, including metered-network
   behavior, cable unplug/reconnect and switching back to home Wi-Fi. A phone
   hotspot is not the same feature as making the PC itself an access point.
3. Pair Bluetooth with a code comparison. Transfer small and 100 MiB files both
   ways where supported, cancel/resume where provided, compare SHA-256, unpair
   and verify rejected reconnection/transfer after revocation.
4. Pair KDE Connect, verify both-way LAN transfers and progress. Explicitly test
   clipboard, notifications, media/input permissions one at a time. Revoke them
   and verify the effects stop. No remote admin or default shared home folder.
5. Mirror over USB with owner consent; verify input is disabled in view-only
   mode. Test optional authorized remote control, rotation, audio policy,
   disconnect and reauthorization. A screenshot alone cannot prove control works.
6. Use a **separate expendable test USB drive**, never the Windows recovery USB
   or the 500 GB NVMe. Test existing FAT32/exFAT/NTFS media read/write as supported,
   Unicode/large-file behavior, full/read-only media, interrupted copy, checksums
   and safe eject. No formatting is needed for these checks. Test malicious-file
   handling without autorun; inserting a device must not grant administrator rights.

Record screenshots for each executed scenario, transfer hashes/timings, effective
permissions, failures and cleanup. Credentials and personal notifications stay
out of committed screenshots/logs. Hardware results remain **NOT TESTED** until
these actions actually run on the PC and phone.

References: [NetworkManager](https://networkmanager.dev/docs/),
[KDE Connect](https://userbase.kde.org/KDEConnect),
[BlueZ](https://www.bluez.org/), [scrcpy](https://github.com/Genymobile/scrcpy).
These provider references are implementation starting points; no new physical
compatibility verification is implied by linking their documentation.


Follow-up native evidence: network and Bluetooth pages now render and close in
an actual KWin/Plasma container session. Bluetooth explicitly reports no adapter.
The Wi-Fi editor exposes WPA2/WPA3 choices and user-only encrypted password
storage as a UI option; merely displaying that option does not prove credential
storage encryption or authenticate to an access point. The dummy-password and
settings-search test outcomes are recorded in CONTINUED_QA.md and AI_HANDOFF.md.
