package com.orez.usb;

import java.util.Locale;

/**
 * SHA-256 values of OREZ OS images the owner's CI built and tested end to end in a VM
 * (live session, full Calamares install, installed boot). A match here is the built-in
 * "official" checksum; anything else still requires the checksum to be pasted by hand.
 * Add a new line only after that build's VM evidence exists.
 */
public final class OrezReleases {
    private OrezReleases() {}

    public static final String DOWNLOAD_PAGE =
        "https://github.com/RezoxNemesis/OREZ-OS/actions/runs/42455290923/artifacts/13608167739";

    private static final String[][] KNOWN = {
        {"cbd1435e4422a1e6c2300c2839aaae46943bf3cb606fe97d6c216e7d875769bb",
         "OREZ OS 0.1 · build 42455290923 (VM-tested live + install)"},
    };

    /** Human label for a known OREZ build, or null if the hash is not a known OREZ image. */
    public static String label(String sha256) {
        if(sha256==null) return null;
        String h=sha256.trim().toLowerCase(Locale.ROOT);
        for(String[] k:KNOWN) if(k[0].equals(h)) return k[1];
        return null;
    }
}
