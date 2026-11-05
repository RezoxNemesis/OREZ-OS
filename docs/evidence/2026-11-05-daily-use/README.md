# Daily-use evidence

All recorded attempts, including failures, appear in ledger.json. Exact commands,
working-tree digests, exit status and logs identify each check. Native scenario
JSON and two original screenshots are retained here; the full local bundle also
contains all report/browser/native captures. See ../../DAILY_USE_QA.md.

- [Actual VLC playback](vlc-playback.png): software video and virtual audio;
  physical audio, GPU acceleration and ISO boot are not established.
- [Actual Settings restored](settings-restored.png): native KDE, owner wallpaper.
- SuperTux raw harness success is limited to process/window/input delivery.
  Manual frame review shows level introduction only, not certified gameplay.
- Rootless Docker did not enforce requested memory/CPU profiles. Historical
  profile names remain original labels; no low-RAM certification is claimed.

Source 3aef3fe plus the recorded dirty-tree digest identifies local attempts;
committed-source CI is recorded separately in the latest AI_HANDOFF checkpoint.

Final committed-source validation: [CI 42001391558](https://github.com/RezoxNemesis/OREZ-OS/actions/runs/42001391558)
passed on `4bb77b1149461b3dc1a72b29432970d91f92324b`: 74 source cases,
23-file package audit, production build and 60 browser cases. ISO job skipped.

All local screenshots: OREZ-daily-use-QA-screenshots.zip, 105857301 bytes,
SHA-256 dff73929ec712251d79c6dd93215c28f1493472520d4e693cf1ffb750468b6a9.
340 unique PNGs cover 551 capture references and 25 attempts. Every unique
capture hash is verified in the bundle. Failed qa3-21 report capture was
recovered from its original result/log after storage was reclaimed; 41 report
images are now present. It remains a failed build attempt.

## Direct GitHub download

[Download all 340 original PNG screenshots](https://github.com/RezoxNemesis/OREZ-OS/archive/7dbd3dbd9ded644c644b1af7bce0a8835a2c94a9.zip).
The isolated evidence snapshot includes PNGs, gallery and manifest, without raw
logs. The downloaded ZIP was verified against every original image SHA-256.
See github-download.json for the exact snapshot and observed download details.
