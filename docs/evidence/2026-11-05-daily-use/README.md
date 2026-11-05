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
