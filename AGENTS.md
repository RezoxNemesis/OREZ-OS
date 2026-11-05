# OREZ OS coding agent rules
1. Read `docs/AI_HANDOFF.md` and verify HEAD/CI status before changing anything.
2. Preserve Windows recovery USB, user data, firmware and existing boot entries. NEVER run disk-wiping commands as part of a build.
3. Never ship remote-access listeners, hidden root access, AI auth bypasses or privileged auto-start agents.
4. User-visible settings and removals required for every background component.
5. Distinguish source implemented, package built, ISO generated, VM boot verified, hardware tested, and install approved.
6. Keep the first milestone live-boot only. No public ISO release until redistribution and safety gates pass.
7. Update `docs/AI_HANDOFF.md` after a session, including commit, test evidence, unresolved blockers and next actions.
8. The owner requests screenshots for every executed test. Use the evidence runner for log/report captures, plus actual GUI frames for visual scenarios. Retain failed attempts, label browser/container/VM/hardware evidence accurately, and provide the gallery or bundle. Never fabricate an OS screenshot.
