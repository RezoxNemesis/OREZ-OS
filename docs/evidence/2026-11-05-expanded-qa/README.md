# Expanded QA evidence — 5 November 2026

`ledger.json` preserves all 16 local attempts, their exact source digest, command,
exit code and log SHA-256. Runs started from the previous commit with declared
working-tree changes. The final committed-source CI identity is in the handoff.

Four unmodified representative images are retained here. `visual-review.json`
records their original location, hash and evidence class. Scenario JSON records
actual APT/native/capability assertions. The complete gallery includes every
report page and UI screenshot, including failures, in the separately supplied
`OREZ-expanded-QA-screenshots.zip`. That workspace bundle is not an OS image.

- [Native desktop](native-desktop.png)
- [Native launcher and applications](native-launcher.png)
- [Desktop after restart, 2 GiB/one CPU](native-restart-2g.png)
- [Actual Blender CPU render](blender-cpu-render.png)

All native images come from a software-rendered isolated container, not an ISO
boot or NVIDIA hardware. The test-only scheduling-capability removal and all
remaining limits are described in [QA_SCENARIOS.md](../../QA_SCENARIOS.md).
