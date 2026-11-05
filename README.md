# OREZ Store development: original PNG evidence

232 unique PNG images / 1000 capture references / 20 local attempts. Exact duplicates are stored once; manifest.json maps every capture. Extract this ZIP and open index.html for the gallery. All four failed attempts are retained.

IMPORTANT: qa7-01 through qa7-10 include the superseded web-first proposal. It was rejected and removed. qa7-11 through qa7-14 adopt real Android targets. qa7-15 onward prefer official Linux versions unchanged, per the owner's latest request. Android YouTube, Instagram and games have NOT run. A Store card or browser preview is not an Android app screenshot.

Current results: 119 source tests, 28-path package audit, 68 browser preview checks, nine native Qt Store scenarios. Real native VLC 3.0.23-1 local video/default Space/mouse pause/fullscreen/quit checks pass with no custom mapping. Native Brave 1.98.63 cannot start its sandbox in this workspace; no security bypass was applied. The final exact 0.1.0-2 to 0.1.0-3 component upgrade preserves test-user state and denies an unprivileged package install.

These are source, preview and native Xvfb/container checks. No full ISO was rebuilt, no consumer Android emulator booted, and no physical PC, SSD or Windows recovery USB was accessed. Retained ISOs predate the Store and lack its Qt dependency. Live authentication/installer/driver/runtime gates remain unresolved.

Implementation: 7fafddf4764528278e6c095e2e52a0c44c5f109d, draft PR https://github.com/RezoxNemesis/OREZ-OS/pull/1 . Exact-commit CI is separate: https://github.com/RezoxNemesis/OREZ-OS/actions/runs/42067954280 . Check its live status; local screenshots are not copies of CI results. See source branch docs/OREZ_STORE.md and docs/AI_HANDOFF.md.

This public archive contains original images, gallery and metadata only. Raw logs and fixture scripts remain local. No real account credentials are used. Selected real screenshots: selected-screenshots.json.
