# Integrated ISO and real UEFI authentication — 6 November 2026

Current image is 5,455,347,712 bytes, SHA256
`e9d423a9d2425e292b2091deded5d50a1d9b34d4e58cb1741a883ae21f1ce04c`.
The actual original base, authenticated native-app delta, dpkg-owned OREZ
component layer and live-only owner policy are combined and independently audited.
38 component files plus four database records, 68 verified layer paths and
2,301 final installed package records. Whole-image reproducibility, updated
security baseline, signed redistribution and a safe installer remain unfinished.

The first two real UEFI boots exposed the first dummy enrollment password.
Ordering alone did not fix it. Both failures are preserved, and those offline
volatile guests and private credentials are destroyed. Current source waits for
Plymouth to exit and refuses unprotected getpass fallback. Third actual boot:
both entries concealed, setup completes, UID1000 console login works,
passwordless sudo is denied, explicit owner sudo succeeds, wrong SDDM credentials
are denied and cleared, and real SDDM/PAM authentication succeeds. Plasma starts
but no usable desktop was observed in that 2D run.

Timed QMP key holds inserted extra masked characters. Immediate key down/up
input yielded the expected 20-character length and successful authentication.
No product authentication bypass was used. One greeter restart, software-graphics
errors and splash timeout remain in the diagnostic record. Inactive-VT DRM
errors do not justify disabling authorization. QMP capture contention ended the
third run through a harness timeout; this is not proof of a guest kernel crash.
The fourth virtual-3D/SDL run used the same ISO. Owner setup concealed both
entries and tty2 login reached a shell (manual-console-login-v4.png); no usable
desktop was qualified. A scrot timeout at 1,627 seconds stopped the collector,
which sent SIGTERM to QEMU. All 74 decodable actual frames are included. One
truncated PNG remains in the raw local run and is recorded as invalid, excluded
from the downloadable gallery. All VM containers/private dummy credentials
were destroyed before publication. The final collector patch handles a timeout,
removes its partial frame and permits later captures; it has no further boot.

Source tests: 181 after assembly, 183 after fallback/PTY changes, 185 after the
Plymouth process-exit guard. Source CI 42162321776 on 7d6b323 passes 185,
38 package paths and 68 browser cases; full ISO job skipped. The last SDL timeout
regression brings local tests to 187. Its final commit/CI and archive identity
are recorded in AI_HANDOFF.md.

All attempts, not just successful commands, are retained. In particular:
qa11-07 cannot read the private checkout as the test UID; 14 uses the wrong
assessment path; 15 and 21 deliberately fail the acceptance gate for leaked
dummy passwords; 20 ends on a QMP collector timeout; 25 ends on an SDL capture timeout. Capturing images with a
zero exit does not turn any failed guest scenario into a pass. Each vm-result.json
is the assessment; result.json describes the capture/build command only.

No OS ISO is published by this evidence archive. Public images/report metadata
contain no real owner credentials or private data. Booted native application
workloads, full installation/reboot/recovery, physical NVIDIA/Secure Boot,
radios/phone/USB, enforced 6-GiB performance and active OREZ AI remain unqualified.
The Windows recovery USB and internal SSD are untouched.
