# Live-boot follow-up evidence

Read ../../VM_GRAPHICS_QA.md and the latest ../../AI_HANDOFF.md first.

The ledger covers all 19 local attempts: 13 completed checks/captures and six
failed executions. **This is not 13 OS acceptance passes.** qa5-12 completed
capture but never qualified a desktop. qa5-18 successfully identified a live
privilege-policy concern; it did not establish secure effective permissions.

The new screenshot archive contains 80 original PNGs and all 200 capture
references, with exact duplicates stored once. Its gallery includes failures,
actual VM/host display frames and rendered textual test reports. It contains no
OS image. See github-download.json for the verified delivery URL and hashes.

The development ISO was built from 82183ea; its signature/digest and static
guards pass. Final diagnostic source d8193b7 passed CI 42027937005. The unchanged
OS payload has not passed usable live desktop, actual installation, recovery,
Secure Boot, NVIDIA or owner-only privilege qualification. CI preview screenshots
are separate from the local VM evidence and expire on the date in ci.json.

Failures: qa5-03 unreadable temporary fixture; qa5-05/07 truncated HTTP transfers;
qa5-09/10 transient QMP readback surface unavailable; qa5-13 SDL capture timeout.
No failed run was overwritten or relabelled. Test harness fixes and the manual
host-window positioning adjustment are documented in VM_GRAPHICS_QA.md.
