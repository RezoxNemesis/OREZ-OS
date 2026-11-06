# OREZ OS — actual screen tour

29 labeled stops. Native component captures are not an installed OS. Download/extract the ZIP and open index.html for the phone-friendly version. The 45 future ideas are in [EXPERIENCE_IDEAS.md](EXPERIENCE_IDEAS.md); boot/password/storage answers are in [FIRST_BOOT_AND_TOUR.md](FIRST_BOOT_AND_TOUR.md).

## 1. The current boot menu

**Historical VM — not a new boot test**

Historical 5 November VM capture of the retained old development ISO. Kubuntu labels remain; this image predates owner hardening and must not be installed. A final OREZ boot menu is still required.

![The current boot menu](images/3a93997e3b1c0810682c0e765a137faaab2c3c45b5fbc3bacaf00d37568604c9.png)

## 2. Installation is currently blocked

**Native component — isolated container**

The actual live-media guard displays why installation is unavailable and exits 78. No installer or disk write was performed.

![Installation is currently blocked](images/26e314c88dc960b06e42599c6efcc3a6e009f9c9bc0c4f25bc3567fad5a14a22.png)

## 3. Welcome home: login theme

**Actual SDDM test mode**

Actual SDDM theme test mode. The environment has no usable desktop session, so sign-in is unavailable. This is not a successful boot or authentication test.

![Welcome home: login theme](images/d8c2d5989fb17d005d81717861eb8ec47170d07ae89943fc25cf79f9fbc1f3bc.png)

## 4. Password field

**Actual SDDM test mode**

Dummy text is masked in the real login field. The completed installer must create your local owner password; no Google or Microsoft login is required.

![Password field](images/7f19797fcf24eab279896236698d6acf1cd3b6d81c87335789c136a434169868.png)

## 5. Current welcome document

**Actual local document — browser render**

The shipped local help document rendered in host Chromium from its source, at desktop and phone widths. Native Brave/file-URL launch is not tested by this render. A first-run setup wizard remains planned.

![Current welcome document](images/d301a6ed2db4bdb4862a1d9f5cd7f585bdfc207eeb70acc8fa7a41e43bd3506b.png)

## 6. Your desktop

**Native component — isolated container**

Actual nested Plasma desktop with the approved Rest wallpaper. The test account retains its demo palette. KDE taskbar/icons are still visible; this is not the final polished shell or a booted ISO.

![Your desktop](images/4d98664eecb38c340725c358158134d701ea97af6d606efbdbda7012e0de402c.png)

## 7. Find OREZ applications

**Native component — isolated container**

Actual launcher search shows Store, Connect, Settings, Calendar, hardware tools and Welcome. Android entries exist but their consumer runtime remains deferred.

![Find OREZ applications](images/322a448677cbb198666da1466e91c419271edf8d497a02f86d01e244967ffdf0.png)

## 8. Searchable Settings

**Native component — isolated container**

Typed Bluetooth into native Settings; matching results appeared. Clearing the query and closing Settings also passed.

![Searchable Settings](images/3bf24156a1bcd6acbc1acecc908c381ebf2b858d27943fe360b6320c5257114e.png)

## 9. Network settings

**Native component — isolated container**

Native NetworkManager settings open and close. This offline container has no physical Wi-Fi radio; no connection or hotspot claim.

![Network settings](images/c4e1148ec53c1154f9205d545b9e0fa099040264857fcb1dd1a50e40b6c3865f.png)

## 10. Wi-Fi password controls

**Native component — isolated container**

A dummy wireless credential was masked, revealed, remasked, cleared and cancelled. No connection was saved. This does not test actual Wi-Fi authentication.

![Wi-Fi password controls](images/fed2d9516cc164d219282c444f6e3dc75462da75bdf9a022985d6274d6c845cb.png)

## 11. Bluetooth settings

**Native component — isolated container**

The actual page correctly reports no Bluetooth adapter in the container. Target-PC pairing, audio and file transfer are pending.

![Bluetooth settings](images/6b340efffa22865cc5df0727ae80f392bc3a5ac77593641dc22c286722a9c586.png)

## 12. Phone connection

**Native component — isolated container**

Real KDE Connect window, no paired phone. KDE Connect handles transfers/control; scrcpy provides separate consented screen mirroring. No Realme mirroring session was fabricated.

![Phone connection](images/f69b107d9cf58440761754b83f3b845dc6d0b784ce842f966dc36227f0f43d27.png)

## 13. File operations

**Native component — isolated container**

A disposable text file was copied, renamed, moved to Trash and restored with Undo through the real Dolphin UI. The original and restored bytes matched. No user data or physical drive was touched.

![File operations](images/9d6898881a99f2faf344cda0682352b84398d2b99be4663ae59358c5add4670e.png)

## 14. Tabs and split view

**Native component — isolated container**

Real Dolphin tabs and two panes, showing the restored renamed file. Split/tabs visually confirmed; nested function-key automation was replaced with actual menu/button input.

![Tabs and split view](images/160ab5ce3862857e0b636a2d4f1cb8c7fd89286e57ef4d011d3fa449acfdd702.png)

## 15. OREZ Store

**Native component — isolated container**

The native Store detects installed Brave, VLC and SuperTux. VLC launched from its button. Android app entries are explicitly pending, not functional Play Store downloads.

![OREZ Store](images/192e1ce0dc2283f58f376a69bb8e908a151c3ac9a7107e3b01b887613665c983.png)

## 16. OREZ Calendar

**Native component — isolated container**

Actual local event creation/editing, SQLite persistence, ICS export and cancellable deletion passed. No cloud account or remote request.

![OREZ Calendar](images/57db73c228b59c941f3b2f6ebdb76686010bca30a53f189cad7d7272c0c8b333.png)

## 17. Reuz clock

**Native component — isolated container**

Native timezone and 12/24-hour preferences saved without changing the system clock. This is the current OREZ Reuz component, not a claim about another repository release.

![Reuz clock](images/29112006c6dfa735d49603e0b1ee0cf5c98cac1eaefc9cdee11f5199df1d5ceb.png)

## 18. Reuz countdown

**Native component — isolated container**

Start, pause, resume and completion passed. It is an application timer; suspended-PC wake and physical alarm audio are not verified.

![Reuz countdown](images/c367d2baae2c1e33161829a347f6bdb90138b4f882b0b85f6bc1e3d6f4d12523.png)

## 19. Reuz stopwatch

**Native component — isolated container**

Start/pause, lap and reset passed. Closing active work asks for confirmation and cancellation keeps the app open.

![Reuz stopwatch](images/e41f58bc0124ec4d67891b6d4b8731d49f901ef37aed34bfe6f4f24af6ffe897.png)

## 20. OREZ Ink palette

**Native component — isolated container**

Real Reuz rendering with the packaged Ink palette. Both Paper and Ink were applied; the five proposed future themes are not implemented.

![OREZ Ink palette](images/f5fe07eed8174327ce36f84011a12f0bbfa584ebd2872379b7c4e6842301799b.png)

## 21. Horizon wallpaper

**Native component — isolated container**

Your second supplied wallpaper applied in the real desktop, then restored to Rest. A wallpaper change is not a new OS edition.

![Horizon wallpaper](images/139b0ebaa51f5b3da6eacb956bcb643a1a523254187c62676b2c59020974730e.png)

## 22. Fullscreen VLC

**Native component — isolated container**

Generated local video played. Actual Space pause/resume, mouse menu, F fullscreen on/off and Ctrl+Q passed. GPU decoding, physical audio and streaming were not tested.

![Fullscreen VLC](images/f27a1a4411aaf095ec51746c5649473e23c2be98b5a4ec7d47ae191c3a9de6bc.png)

## 23. Fullscreen native game

**Native component — isolated container**

SuperTux rendered at 1440×900. Captures show the player moving from x≈96 to x≈482 after Right input. This is software rendering, not an RTX benchmark, Android emulation or universal game compatibility.

![Fullscreen native game](images/24c010ad86d6623237a3c98a7a5aa1dd8b3c9cb77aa12ff4d3eb2bd6c72abb4f.png)

## 24. Game pause menu

**Native component — isolated container**

Escape opened the actual game pause menu. Only the disposable native game session was stopped.

![Game pause menu](images/69c645128cdbc6198993caf05abc1daab43f34d86d84c89f6143c05db7506c61.png)

## 25. Files and terminal together

**Native component — isolated container**

Dolphin and Konsole arranged side by side. Minimize and restore also passed. Ordinary user UID 1500, not a privileged desktop session.

![Files and terminal together](images/7b67940c048393c5bade7ff632b29f1c3c0a12e79e49e7329fdf917743b97e2c.png)

## 26. A second workspace

**Native component — isolated container**

KWin created a second workspace, switched to it, returned and removed the test workspace. The windows stayed on their original workspace.

![A second workspace](images/b5e06b07e2e480e61ae240a22267f2a9e8c61129d4d96ac69baf6621d0242f32.png)

## 27. Restart the panel, preserve the work

**Native component — isolated container**

A controlled Plasma shell restart brought the panel back while the existing Dolphin/Konsole processes remained alive. This is not kernel-crash, power-loss or disk-recovery qualification.

![Restart the panel, preserve the work](images/54a55a01bd44b31cfda5249cedb9743af5fe800b9a433029f7fb35871745eaac.png)

## 28. Brave: honest environment limit

**Test report — not a browser window**

The official native Linux browser was attempted. Its sandbox could not create required nested namespaces. This report records BLOCKED, even though the vendor wrapper returned zero; no working browser or YouTube is claimed.

![Brave: honest environment limit](images/3e46090153d0fae50b518422ac7b12b8ed79e34a8cae1b5f455bf8269046343d.png)

## 29. AI status is visible

**Native component — isolated container**

orezctl ai explicitly reports NOT ENABLED. No AI/MCP root or remote action broker is installed. Future AI must use ordinary permissions and explicit owner approval.

![AI status is visible](images/7b67940c048393c5bade7ff632b29f1c3c0a12e79e49e7329fdf917743b97e2c.png)
