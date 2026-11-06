# Installation disabled on experimental live media

**Why:** OREZ OS 0.1 has NOT passed its graphical, signed update, installed-layer persistence, data preservation, LUKS2, rollback or target-PC tests. Launching Calamares on an unqualified live ISO could install unbranded Kubuntu or overwrite the wrong SSD partition.

The live-media overlay replaces `/usr/bin/calamares` with a **visible safety notice**. The OREZ installer launcher opens that warning and exits with status 78 instead of touching storage. This override is active only in the experimental live ISO. If you inspect the image, it is visible at `/usr/bin/calamares`; it is not a hidden privileged service.

**Important:** The standalone `orez-shell` Debian package explicitly EXCLUDES the two live-only installer override files. Installing the OREZ shell package on an existing qualified KDE Linux machine will never overwrite its actual Calamares binary or launcher.

Until a tested replacement installer is available, use OREZ only in a disposable VM or live USB environment. Ordinary Linux root users can still access other partitioning utilities; this guard prevents the obvious unqualified installer path, but is not a universal disk-write prohibition. Keep your Windows recovery USB separate.
