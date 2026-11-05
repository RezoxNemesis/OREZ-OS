# Tests and screenshots

The owner requests screenshots for every test run, including failures. Preserve failed attempts and label each evidence class. A screenshot is evidence of the captured view, not proof of disk safety or security.

## Evidence classes

| Class | What it proves | What it cannot prove |
|---|---|---|
| Source report | Command, assertions, exit status and output | Runtime OS behavior |
| Browser preview | Actual React rendering and browser interaction | Linux boot, Android hardware, native desktop or phone pairing |
| Package container | Actual APT/dpkg operations in an isolated Ubuntu root | Calamares, reboot, EFI, GPU or disk recovery |
| Native container desktop/window | Actual KWin Wayland/Plasma or KDE application rendering and the specific recorded interactions | A booted ISO, production login/session policy, hardware acceleration or RTX compatibility |
| VM framebuffer | Pixels displayed by that VM | Physical compatibility or untested install paths |
| Hardware capture | The particular recorded real-machine state | Other configurations or absolute security |

## Local checks

Use Node 24, Python 3 and `npm ci --ignore-scripts`. Install the Playwright Chromium browser with `npx playwright install --with-deps chromium` on a disposable development host. `OREZ_CHROMIUM` can select an existing browser executable. Never alter managed browser policies to make tests pass.

```sh
python3 build/run-with-evidence.py --name 'Source checks' --kind source --output dist/evidence/source-01 -- python3 -m unittest discover -s tests -v
python3 build/run-with-evidence.py --name 'Preview build' --kind browser-preview --output dist/evidence/build-01 -- npm run preview:build
python3 build/run-with-evidence.py --name 'Browser checks' --kind browser-preview --output dist/evidence/browser-01 -- npm run preview:test
python3 build/collect-evidence.py dist/evidence
```

Use a new output directory for each run. The runner records the parent commit, a digest of tracked and nonignored working-tree source, timestamps, command, exit status and log hash. It captures **every page** of the actual test log, even after failure or timeout. A capture failure fails the wrapper; it does not silently turn a failed check green. Commands must be safe to log; never capture credentials or personal device data.

Playwright additionally captures every test at 1440×960 and 412×915, plus full pages and failure traces. The wrapper passes `OREZ_EVIDENCE_DIR` so these go into that unique run's `ui/` and `playwright-report/` directories. Earlier local runs were copied into their run directories before rerunning. Direct invocation without the wrapper uses replaceable default directories; use the wrapper when retaining evidence. CI preserves the full directory with `if: always()`. Use the gallery to inspect both failed and corrected results.

## Native package integration

Build the package through the evidence wrapper. Then provision the test-only image using `docker build -f build/integration/Dockerfile -t orez-package-test:20261105 .`. The image pins the Ubuntu base digest; APT dependencies are current repository versions, not a reproducible snapshot. Its image ID and package versions are evidence, not a claim of byte-identical builds.

```sh
python3 build/run-with-evidence.py --name 'Package integration' --kind package-container --output dist/evidence/package-01 --timeout 300 -- bash build/test-package-container.sh dist/evidence/package-details-01
```

The orchestrator creates a disposable container without network, host devices, privileged mode or bind mounts. It copies in the `.deb` and allowlist, checks APT install, 16 dpkg-owned files, ordinary-user controls, reinstall, a native KDE Settings window, purge, and preservation of unrelated user data/dependency applications. It copies out logs/screenshots and removes the container on exit. Root is used only inside this test container for package operations. Xvfb software rendering is test-only; no compositor policy changes are shipped to users.

`--no-download` hit an APT internal pathname error on this Ubuntu version. The harness uses ordinary APT with the container's network disabled instead; it never uses `--force-depends`. The later [expanded scenario suite](QA_SCENARIOS.md) tests real upgrade/downgrade mechanics using local synthetic package versions. Signed update channels and whole-system rollback remain unqualified.

The official minimal Ubuntu image excludes `/usr/share/doc/*`. Initial runs therefore installed only 14 of 16 files. The fixture now supplies explicit dpkg path-includes for OREZ's documentation, matching a non-minimized desktop while retaining the 16-file assertion. This is test configuration, not a change to user machines. The current welcome HTML resides under documentation; move runtime UI assets into a dedicated application-data directory before supporting minimized hosts, and requalify the changed installer allowlist against upstream.

The ordinary-user check also caught restrictive checkout modes being copied into the `.deb`. All three builders now stage files with explicit 0755 directory/command modes and 0644 data modes, leaving checkout modes and symlink targets unchanged. The package audit rejects inaccessible, privileged, writable-by-everyone or incorrectly owned entries. Regression fixtures simulate a private checkout. The full ISO must still be rebuilt and boot-tested after this build-path change; unit tests and a native package do not certify the remixed image.

## CI and durable evidence

Ordinary PRs run the small source/package/browser job. The large package dependency image has a separate **manual-only** workflow. ISO jobs remain opt-in and retain their real framebuffer captures; do not run them again without a new hypothesis or a qualified graphics environment.

Source artifacts retain evidence for **14 days**; the expanded manual package/desktop job retains it for **seven days**; older ISO workflows retain evidence for only two days. Download evidence before expiration. Commit a small session ledger with exact source/log hashes and outcomes, plus representative genuine screenshots; do not commit multi-GB ISOs or large videos. Artifacts are not permanent memory. The handoff must say when downloadable evidence has expired or is available only in the user's downloaded bundle.

Official tool references: [Playwright screenshots](https://playwright.dev/docs/screenshots), [offline browser contexts](https://playwright.dev/docs/api/class-browsercontext#browser-context-set-offline), [GitHub artifact retention](https://docs.github.com/en/actions/using-workflows/storing-workflow-data-as-artifacts), [Docker network isolation](https://docs.docker.com/engine/network/drivers/none/).
