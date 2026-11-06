# Actual boot and installer-preparation tour

These are original guest captures. Read manifest.json for the exact scope, failures and remaining gates. For every report and frame, extract the archive and open index.html.

## Safe stop before reading a password

Actual earlier UEFI boot. Owner setup refused to read a password while the splash process still owned the console.

![Actual guest capture](images/805715997a76426167f64489b9ad4d68ec6579a9825ca8946d1e00c806f0a15d.png)

## Local owner creation

Actual diagnostic boot. Both observed enrollment entries are concealed. This temporary account requires no online account and changes no SSD.

![Actual guest capture](images/5afaac9d61d92b740ccb7ee2399cd4401102938bbea6fd974da04819d147eab1.png)

## Owner and administrator boundary

Actual owner shell: UID1000 and passwordless administrator access refused. A scoped check, not complete security certification.

![Actual guest capture](images/52d054135b9c9dc72b298d858c9e035474ebe71b1305a18d249e9b15967fd13d.png)

## Actual OREZ login

Actual SDDM in the older booted image, with the approved wallpaper. The inherited live-session selection was subsequently corrected in source.

![Actual guest capture](images/a49d7a983273ddd183b1788cac61d9f2e60702ba0ae0bf3843eabc3ec065733b.png)

## Incorrect password refused

Despite its historical filename, this frame shows the actual graphical authentication failure message.

![Actual guest capture](images/8493f476dfb5eb9da3d69ab20fbbdde52cd515368861e8c63606338ab1a6a9dc.png)

## Inherited startup flow discovered

Correct owner authentication reached the upstream live installer prompt on VT4. The new source uses a direct OREZ desktop entry instead. This is not an installation or desktop pass.

![Actual guest capture](images/640d9b0a15d425648d751749d57f4a6ab55cdf491969ba66a0479387dea718cc.png)

## Corrected image normal boot menu

Actual new-image UEFI menu. Read this run’s diagnostic for the final boot result; a menu is not desktop or installation qualification.

![Actual guest capture](images/4e169750691f3725722ba22b1234ea603b1fbd5443fc10b7803b4eb34e50f918.png)

## Normal boot enrollment completed

Actual corrected-image default boot, without edited kernel flags. Both password entries are concealed and enrollment completed. This is one observed timing, not broad race-condition certification.

![Actual guest capture](images/86e1b1de997dcfcc137efce45dd0466cc8483fb5703d4bd8f8145c38f31f978e.png)

## Corrected OREZ Desktop selection

Actual corrected-image SDDM with approved wallpaper and the dedicated OREZ Desktop entry. Correct authentication succeeded but this normal session then exited64; the desktop below comes from a separate diagnostic.

![Actual guest capture](images/524fceeb25450c4a400652ebb51c47393c3168e5a66d0b71ab77e9929ec03a94.png)

## Normal-session failure retained

Actual owner-authenticated diagnostic journal shows the normal session ending with exit64. This was not an incorrect-password rejection. Full cause remains unresolved.

![Actual guest capture](images/94a03660984f92cefc451db7814c5e4133b9f61adc3483431e8f04ddad3a49f8.png)

## Separate diagnostic: real native desktop

After the normal-session failure, the already-authenticated ordinary owner launched startplasma-wayland from tty3. This actual booted ISO eventually rendered the approved wallpaper, panel and system tray. Clicking Skip closed Welcome. No root or sandbox bypass; no normal-login or performance pass.

![Actual guest capture](images/8952d20c5c1da9586db9b3dfccc1fa50e71ce26476ad832f6a8eb7791e552bc7.png)

## Separate diagnostic: native Settings opens

Clicking the taskbar Settings icon opened real KDE Quick Settings inside the booted ISO. Search and device/settings routes are visible. No setting was changed, no radio was attached and no network, theme-switching or full settings-functionality pass is claimed. Inherited Kubuntu branding remains.

![Actual guest capture](images/b3c6055124859f7db8a576fb17f909546f188319d800fff19529c625d9ea24dd.png)
