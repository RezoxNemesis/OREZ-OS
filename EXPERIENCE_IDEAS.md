# Forty-five OREZ proposals

Original OREZ combinations and game concepts; not a claim that no other product has related ideas.

45 proposals. Stabilize boot, installation, updates and recovery first. Games are optional native downloads, not mandatory preload.

Every idea below is a proposal, not a shipped or tested feature. The acceptance condition describes future testing. Shortcut bindings require a conflict audit and remain configurable.

## Original games

- **Ink Courier** — Deliver letters through brush-painted villages by drawing a limited supply of ink platforms. Small native Godot 2D game; keyboard/controller; offline. Acceptance: Finish ten levels with remappable controls and a 60-FPS target on qualified hardware.
- **Folded Worlds** — Fold a paper map to connect paths, redirect light and reach hidden rooms. Native puzzle game with deterministic undo; no ads or purchases. Acceptance: Every puzzle has a reachable solution and undo restores the exact board.
- **Quiet Station** — Repair a train station by arranging signals, power and passenger routes. Short pause-anytime logic sessions; optional local co-op later. Acceptance: Pause/save/reload preserves the complete simulation without losing progress.
- **Shadow Garden** — Grow a moonlit garden by placing trees whose shadows form changing paths. Low-spec turn-based puzzle with an accessible high-contrast mode. Acceptance: All puzzles remain playable without colour discrimination or timed input.
- **Rewind Harbour** — Route small boats through a harbour while rewinding selected objects instead of the entire world. A compact native puzzle prototype; bounded simulation history. Acceptance: Rewind cannot duplicate rewards or corrupt saved games.

## OS features

- **Project Rooms** — Open a chosen set of files, apps and window positions as one named work context. Local workspace manifests; never store credentials or automatically execute imported scripts. Acceptance: Export/import a room; missing apps are explained and no command runs without permission.
- **Change Receipts** — Show what every OREZ-managed update or settings action changed, why, and how to undo it. Start with OREZ operations; never claim to capture every arbitrary root command. Acceptance: Apply and undo a supported change; compare effective state and preserve the audit entry.
- **Resource Agreements** — Give a foreground game, render or call a visible resource budget and postpone optional background jobs. Use supported Linux cgroups/PSI; owner can override; no magical CPU/GPU unlock. Acceptance: Measure frame times and responsiveness under enforced competing loads.
- **Offline Readiness** — A clear checklist shows which apps, drivers, documentation and recovery tools really work without internet. Package/content inventory plus explicit offline tests. Acceptance: Disconnect networking and launch every item marked ready; stale claims must disappear.
- **Context Dock** — Each Project Room can keep a small set of relevant files and safe actions in its own dock. Explicit local configuration; no covert usage tracking. Acceptance: Switch rooms repeatedly without launching hidden apps or leaking another room’s recent files.

## Security features

- **Access Receipts** — Display the app, exact folder/device, purpose, duration and revocation control for permission grants. Narrow capability broker; OS authentication is separate from AI text. Acceptance: Wrong app, expired token and revoked token must all be rejected.
- **Canary Documents** — Optional decoy documents detect suspicious mass rewriting near protected work. Evidence-based alert first; ignore known backup/indexing workflows; no automatic destructive response. Acceptance: Run benign indexers and controlled synthetic ransomware fixtures; measure both misses and false alarms.
- **Remote-Control Beacon** — Show a persistent, owner-controlled indicator whenever an authorized remote-input session exists. Track known remote sessions and device arrivals, not private keystrokes; cannot prove human identity. Acceptance: Start/revoke a permitted session; injected USB input must not be mislabeled as proven owner activity.
- **Payment Workspace** — Offer a separate, minimal browser profile for financial work with reduced extensions and sharing. Opt-in isolation, clear domain display and ordinary bank authentication; no guarantee against phishing. Acceptance: Verify profile/cookie separation, clipboard policy and permission revocation with dummy accounts.
- **Revocation-Safe Restore** — Restore the system without silently resurrecting revoked devices, tokens or obsolete trust decisions. Separate revocation records from ordinary rollback; require owner-held recovery credentials. Acceptance: Revoke access, roll back, and prove the revoked principal still cannot connect.

## Shortcut features

- **Hold-to-Learn** — Hold a configurable key to see the shortcuts available in the current app. Accessible overlay; query known app bindings; do not intercept passwords. Acceptance: Overlay is readable at 200% scale and never consumes a typing shortcut unintentionally.
- **Action Palette** — Search settings, apps and safe operations with clear previews and required permissions. Local command registry; no arbitrary shell execution from guessed natural language. Acceptance: Ambiguous and privileged actions require explicit selection and normal authentication.
- **Return to Task** — One configurable action returns to the previous Project Room and focused document. Window/app context only; recovery of unsaved documents depends on application support. Acceptance: Switch across three rooms; restore the correct window without exposing hidden work.
- **Peek and Place** — Hold a shortcut, choose a workspace visually, and release to move the current window. Use compositor APIs and cancel safely with Escape. Acceptance: Move/cancel repeatedly across multiple displays without losing the window.
- **Private Paste Shelf** — An opt-in temporary shelf holds selected clipboard items and clears them visibly. Never assume sensitive-content detection is perfect; exclude password managers where supported. Acceptance: Disable/clear removes stored items; clipboard synchronization remains separately consented.

## Multitasking features

- **Task Lanes** — Group windows by activity and give each group its own notification policy. Reuse Plasma workspaces/activities with a coherent OREZ interface. Acceptance: Switch groups under load and prove notification exceptions still work.
- **Window Placeholders** — After restart, show where previous windows belonged and let the owner reopen them. Do not claim to recover arbitrary app memory or unsaved content. Acceptance: Unavailable files/apps produce useful placeholders and never trigger silent downloads.
- **Drop-to-Action Tray** — Drop selected files onto explicit local actions such as convert, compress or compare. Preview output and destination; preserve originals; external sending is always separate. Acceptance: Cancellation leaves originals intact; path traversal and command injection are refused.
- **Phone Handoff Parcel** — Send a selected document or task note to the paired phone with a visible transfer receipt. Build on KDE Connect; selected data only, encrypted transport where supported. Acceptance: Pair, send, interrupt, retry and revoke against an actual Android device.
- **Attention Queue** — Collect routine notifications while recording or gaming, then present a concise review. User-defined exceptions for calls and critical warnings; no invisible permanent suppression. Acceptance: A critical alert remains visible and queued notifications survive an app restart.

## Crash resistance and recovery

- **Graphics Safe Profile** — Keep a tested conservative display/effects profile for recovery after graphics problems. Supported driver/compositor options only; no firmware or voltage bypass. Acceptance: Recover from a deliberately bad test profile on a VM and the actual GPU.
- **Checkpoint Before Change** — Create an appropriate system checkpoint before supported driver or OS changes. Snapshots complement independent backups; account for app consistency and revocations. Acceptance: Interrupt an update, restore, and verify both boot and untouched user documents.
- **Restart Only What Failed** — Offer to restart a hung app or desktop shell while keeping other applications running. Record diagnostics with consent; never promise recovery of all unsaved app state. Acceptance: Crash the selected component and prove unrelated processes/data remain intact.
- **Trial Boot Updates** — Boot a staged update once and retain a known-good recovery choice until health checks pass. Design against rollback to vulnerable versions and protect trust/revocation state. Acceptance: Failed boot returns to the approved recovery path without deleting user files.
- **Memory Pressure Assistant** — Explain memory pressure and offer to pause selected background work before a severe stall. Use actual pressure metrics and bounded zram/swap policies; no cache-clearing gimmicks. Acceptance: Test enforced 6/16-GiB workloads, missed warnings and false interventions.

## Computer wellbeing

- **Thermal Context** — Explain sustained temperature, fan and throttling patterns in plain language. Read hwmon/NVML when available; offer maintenance advice rather than unsafe tuning. Acceptance: Compare displayed values with trusted tools and handle missing sensors honestly.
- **Storage Care** — Track NVMe health, free-space pressure and supported maintenance schedules. No automatic formatting, destructive tests or unsupported repair operations. Acceptance: Recognize simulated warning logs; verify read-only polling and safe cancellation.
- **Power With Evidence** — Compare quiet, balanced and performance profiles using measured workload results. Owner chooses the trade-off; avoid universal better-performance/lower-power promises. Acceptance: Repeat the same benchmark and record power, temperature and completion time.
- **Backup Rehearsal** — Periodically restore a chosen sample into an isolated folder to check backup usability. Explicit opt-in, encrypted backups where configured, and no original-file overwrite. Acceptance: Detect a damaged backup and recover the sample with an owner-held key.
- **Restful Desktop** — Schedule quiet periods and sleep around the owner’s actual work rather than a fixed idle timer alone. Respect renders, recordings and active sessions; explain every inhibited sleep request. Acceptance: Verify sleep/wake and display reconnection while preserving active work.

## UI design

- **Readable Paper Glass** — Use restrained translucent panels with an opaque fallback when contrast or GPU resources require it. Accessible colours, cached effects and a visible effects switch. Acceptance: Check contrast on both supplied wallpapers and under software rendering.
- **Meaningful Motion** — Animate where a window or task went, using short transitions that can be disabled. Respect reduced-motion preferences everywhere. Acceptance: No task requires animation to understand its state; measure input latency.
- **Truthful Status** — Show effective configuration and distinguish ready, unavailable, pending and failed features. No fake connected devices, working AI badges or implied successful installs. Acceptance: Disconnect services/devices and compare the UI with actual backend state.
- **One Search, Clear Scope** — Search apps and settings together, with optional file indexing under explicit exclusions. Local-first indexing; expose included locations and deletion controls. Acceptance: Excluded/private locations never appear and changed settings are discoverable.
- **Keyboard and Pointer Equality** — Make every important action usable with visible focus, mouse, keyboard and assistive tools. Avoid tiny controls, hidden hover-only actions and icon-only consent. Acceptance: Complete the main journeys without a mouse and at enlarged text scale.

## Additional theme directions

- **Silver Mist** — Cool grayscale paper, light glass and subtle silver focus outlines. Keep the approved tree imagery and minimal palette. Acceptance: Contrast and focus indicators pass on light and detailed wallpaper regions.
- **Moonlit Ink** — Charcoal surfaces with pale brush details and quiet, warm-white text. A proposed refinement beyond the current basic OREZ Ink palette. Acceptance: Unchecked controls, disabled states and text remain distinguishable.
- **Snow Field** — Nearly white surfaces, generous spacing and a small ink-red accent. Red is optional and never the sole meaning of a status. Acceptance: All status meanings remain clear in grayscale and colour-vision simulations.
- **Archive Paper** — Warm handmade-paper tones with compact typography for long reading and coding. Font choice and density remain user-controlled. Acceptance: Review long documents, code and file lists at common display scales.
- **Focus Contrast** — Opaque black/white surfaces, strong borders and reduced animation. Accessibility/performance profile with the same features as decorative themes. Acceptance: Every permission, error and focus state remains visible with effects disabled.
