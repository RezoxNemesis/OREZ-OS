# OREZ OS — MASTER PROJECT BRIEF AND ARCHITECTURE DIRECTIVE

Connectivity follow-up: native Wi-Fi/internet/Bluetooth controls, Realme hotspot/
USB tethering, consented phone mirroring, LAN/Bluetooth/USB file transfer and
safe eject are required. See [CONNECTIVITY.md](CONNECTIVITY.md) for providers,
visible controls and the still-pending physical test matrix.

## Owner additions — 5 November 2026

- Built-in Android application support must eventually download actual YouTube
  and free casual games through a qualified Play Store provider. The current
  SDK-based developer tool is experimental, not delivered consumer support.
- Use the two owner-supplied 1280×720 wallpapers unchanged: Rest default,
  Horizon optional. Provenance and SHA-256: WALLPAPER_SOURCES.json.
- Owner remains sole human administrator/development authority; no vendor,
  Google or AI host-admin identity. Public repository now; private only after
  PC-readiness gates pass. See OWNER_CONTROL.md for actual audit limitations.
- Engineer responsive ordinary use at 6 GiB and excellent measured performance
  on the actual 16 GiB PC, with low idle overhead and appropriate power use.
  Preserve functionality/security. No unsafe hardware-unlock or zero-lag claim.
- Install needed QA tools and provide a publishable environment definition;
  provider-owned KVM/GPU/cgroups/sandbox access must be verified separately.
- Preserve screenshots of every executed test, including failures and blocks.

You are the lead operating-system architect, Linux distribution engineer, desktop UX designer, cybersecurity engineer, AI-systems engineer, and release/QA lead for **OREZ OS**. Prepare a rigorous, executable master plan for a real, installable, professional desktop operating system—not just a theme, prototype, wallpaper, mockup, or Android-style launcher. The plan must be safe, realistic, hardware-specific, maintainable, and resumable by other ChatGPT conversations or agents.

## 1. Vision and non-negotiable principles

- OREZ OS is **our own customizable desktop OS experience**, initially built on a mature, actively supported Linux foundation for the kernel, drivers, package management, and hardware support. Do not pretend it is an entirely new kernel. Evaluate the best actively supported Ubuntu LTS / other suitable base using verified current documentation and justify the choice.
- **Full desktop freedom:** No arbitrary app-store lock-in. Provide a genuine multitasking desktop, proper windows, multitasking, shortcuts, unrestricted user files, terminal, developer tools, third-party software, package management, containers, VMs, creative suites, game engines, and system administration subject to normal authentication and security boundaries.
- **Visual direction:** Elegant Japanese *sumi-e* ink-brush art on textured white paper. Black-brushed tree with a person in black resting under/against it, restrained monochrome styling, subtle black and gray accents, and tasteful translucent frosted-glass panels (glassmorphism). Minimal, professional, spacious, accessible, readable. **Not colorful neon, not bloated, not a mobile UI.** The approved desktop theme should extend consistently across the login screen, launcher, dock/taskbar, settings, file manager, notifications, installer, boot/splash screen, and OREZ AI panels.
- **Polished usability:** A Windows-easy GUI for ordinary tasks with power-user tools always available. All advanced features and settings must be findable by search and in understandable menus. Accessible keyboard/mouse controls; sensible first-run setup and help.
- **No artificial performance claims, no hidden backdoors, no undocumented switches, no silent security bypasses, and no false claims that a feature or build works without evidence.**

## 2. Actual target hardware and constraints

- MSI **B550M PRO-VDH WIFI** AM4 motherboard, 4 DDR4 slots, UEFI-capable.
- AMD **Ryzen 5 5600** CPU (no integrated graphics; monitor must connect to dedicated GPU).
- NVIDIA **GeForce RTX 3050 6 GB** graphics card.
- **16 GB DDR4 RAM**, **WD Blue SN5000 500 GB NVMe** SSD.
- Lenovo 27-inch monitor (exact model/resolution/refresh still to be verified).
- Android phone: **Realme P1 Speed**, USB-C with **USB 2.0** data capability; user mainly operates from Android and uses GitHub via phone. Do not assume USB-C DisplayPort Alt Mode or that a USB-C-to-HDMI adapter can output video from the phone.
- OS should be installable through a **USB flash drive** using a simple, documented, UEFI-compatible method. A separate Windows 11 installation/recovery USB already exists; **do not overwrite it**.
- Prefer free/open-source tooling and avoid mandatory paid services. GitHub Actions capacity and artifact storage are limited; design efficient, consolidated builds and release storage rather than assuming unlimited minutes/storage.
- Do not assume all Wi-Fi, Bluetooth, audio, Secure Boot, NVIDIA-driver, or monitor behavior is validated until exact firmware/chipset and real-machine tests confirm it.

## 3. Core desktop capabilities

Create an architecture and phased implementation plan for:

1. Real desktop shell, window management, workspaces, file manager, search, settings, power controls, notifications, recovery interface, accessible themes.
2. Open software ecosystem: supported Linux apps, software center as an **option**, standard package manager, Flatpak or equivalent sandboxed apps, developer-installed packages. Explain Windows app/game compatibility limits (Wine/Proton, anti-cheat, specific unsupported drivers).
3. Professional work: browser, office, media playback, audio, video editing, animation/VFX, Blender, Godot, other suitable engines, programming tools, Git, C++/Python/Rust/Java, IDEs, Docker/Podman, VMs when supported.
4. Gaming and graphics: proper NVIDIA driver, Vulkan/OpenGL, Steam/Proton, optional performance profiles, gamepad and monitor support, reliable driver upgrades.
5. AI workstation: first-class GPU compute and CUDA-compatible components when supported; PyTorch, inference runtimes, local LLMs, model/embedding/vector-store tools, model evaluation, fine-tuning strategies, coding agents, data pipelines, and background jobs. Clearly state that RTX 3050 **6 GB VRAM** and **16 GB RAM** limit practical model size and training; support quantization, CPU offload, external compute, and future hardware upgrades without promising huge-model training on this machine.
6. Deep but **permissioned** OREZ AI integration: natural-language search, app opening, workflow assistance, coding and creation, system diagnostics, optional voice; support multiple local or user-selected cloud models without making a paid service mandatory.
7. Straightforward settings, system monitoring, updates, backup, restore, snapshot/recovery, and diagnostics.

## 4. Seamless Android ↔ PC connection (high priority)

Design a polished built-in **OREZ Connect** app with a matching Android companion or integration with reputable existing tools. Prefer local-first operation and an open protocol where possible. Include:

- Discover and pair via QR code or short code on the same Wi-Fi/LAN, using explicit user confirmation, mutually authenticated encryption, trusted-device list, device renaming, key rotation, and one-click revoke/unpair.
- Easy file/photo/video transfer both directions; optional automatic folder sync with visible control over scope; phone clipboard sharing with consent; notifications with per-app preferences; battery status; optional media controls and remote PC control.
- USB fallback for large file transfers where technically supported (e.g. MTP, user-enabled USB debugging with scrcpy for optional screen mirroring), with clear instructions and safe defaults; don't assume phone can provide HDMI video output or that all features work without authorization.
- Optional Android screen mirroring, remote input, and phone-as-trackpad, each opt-in, visibly active, and revocable. Support connection only on trusted networks by default; remote access over internet must be off unless explicitly configured and secured.
- Connection status, permissions, errors, transfer progress, and **Disconnect** controls visible in ordinary Settings → Devices → OREZ Connect; no invisible persistent pairing or permanent ADB requirement.
- Show a realistic MVP using proven tools and what actually requires custom development.

## 5. Security architecture: defend against malware, hackers, and AI misuse

**Never claim a system can be 100% unhackable.** Use defense in depth and a documented threat model covering hostile network traffic, malicious apps, phishing, supply-chain attacks, compromised dependencies, unsafe USB devices, physical theft, and prompt-injection/malicious AI tool output. Design and verify:

- Trusted and reproducible build pipeline, verified upstream packages, pinned/reviewed dependencies, SBOM, signed releases, hash verification, restricted CI permissions, dependency scanning, and no secrets in source or logs.
- UEFI Secure Boot approach where compatible, protected boot chain, full-disk encryption option (e.g. LUKS2), secure key handling, routine security patches, kernel maintenance, firewall enabled by default, sandboxing, minimal exposed services, application permissions and least privilege, secure DNS/browser defaults, and backup/recovery.
- Clearly identified administrative operations using OS authentication (e.g. polkit); root is **never** implicitly granted to OREZ AI or third-party assistants. Do not hardcode root credentials, secret admin ports, universal developer keys, backdoor users, or bypass tokens.
- **AI security boundary:** Treat prompts, websites, files, tool outputs, and MCP/plugin responses as untrusted input. An AI instruction cannot supersede OS login, privilege checks, filesystem restrictions, firewall policy, or an explicit user approval. Sensitive actions (packages/drivers/kernel changes, firewall changes, reading sensitive files, network exposure, deleting data, privileged shell operations, code execution) require narrow, auditable authorization in a trustworthy GUI. Use allowlisted tools and scoped capabilities, separate system/data permissions, visible activity log, kill switch, and immediate session/token revocation. Never permit an agent to secretly downgrade security to complete a task.
- Security verification: automated scanning, tests for privilege escalation and prompt-injection paths, negative permission tests, dependency/vulnerability scans, firewall tests, recovery tests, and independent review before a public installer release.
- User has final control: every feature, AI permission, startup service, pairing, update mode, firewall rule, and optional integration must be **discoverable, documented, and manageable** in a GUI and/or clear CLI. Show effective current values, why a setting is applied, the file/service that implements it, what changes on toggling, and how to revert it. Critical protection changes require clear warnings and administrator authentication. No inaccessible configs, undisclosed permanent behavior, or hidden telemetry.

## 6. USB boot and installation must be safe

- Choose a supported, maintainable x86-64 Linux build method and a real installer. Provide a live **Try OREZ OS** environment before disk modification.
- Create a UEFI/GPT-compatible, bootable, verified ISO with correct bootloader and recovery path. Validate ISO checksums, image structure, boot menus, initramfs, desktop startup and installer. Test in QEMU/OVMF first; document that VM success does **not** prove compatibility with NVIDIA, Wi-Fi, Bluetooth, or real firmware.
- Test signed/proprietary NVIDIA driver handling and Secure Boot/MOK path where needed; plan fallback graphics modes. Verify AMD chipset, audio, networking, Bluetooth, NVMe, USB and suspend behavior on real target hardware.
- Never automatically wipe or repartition the SSD. Support explicitly selected **try-only**, full-install, and optional dual-boot scenarios; show affected partitions and require confirmation before destructive steps. Provide data-backup and Windows-recovery instructions.
- Supply an Android-friendly ISO download and USB-writing process with checksum verification and clear failure recovery. Do **not** overwrite the existing Windows installer flash drive.
- Specify acceptance criteria for successful cold boot, reboot, login, driver load, storage mount, Wi-Fi, Bluetooth, desktop use, install completion, and rollback; mark actual validations as PASS / FAIL / NOT TESTED.

## 7. Engineering execution, licensing and releases

- Repository: proposed **RezoxNemesis/OREZ-OS** (verify its existence before any GitHub actions; never invent a created repository, commit, workflow, artifact, or test).
- Prefer modular upstream components over rewriting stable kernels/drivers. Design source layout, build scripts, CI, package repo/updates, versioning, signing and release channels. Keep base OS, custom desktop, apps, AI service and phone companion independently maintainable.
- License review is mandatory: choosing 'no license' for original proprietary code **does not remove** third-party Linux/kernel/open-source license obligations. Identify which source code must remain available on redistribution and what may remain proprietary. Never claim that Linux as a whole can be made closed-source by simply choosing 'All Rights Reserved'.
- Explain GitHub Actions build constraints, cache efficiency, artifact/release limits, multipart downloads only if needed, checksums, traceable manifests, and safer distribution options; verify current provider limits from official documentation rather than repeating unverified numbers.
- Plan tests and security gates before adding expansive features; optimize for a mobile-only developer and few manual steps, while requiring explicit consent for destructive/security-sensitive actions.
- Never state 'done', 'build succeeded', 'secure', or 'boots on hardware' without logs, workflow URLs, checksums, and relevant test evidence.

## 8. Durable cross-chat continuity (essential)

The GitHub repository—not a single chat's memory—is the **canonical source of truth**. Define a mandatory, version-controlled documentation convention:

- `README.md` — vision, status, install overview.
- `docs/MASTER_BRIEF.md` — this directive, updated with approved decisions.
- `docs/ARCHITECTURE.md` — layers, dependencies, interfaces.
- `docs/HARDWARE.md` — target components, firmware info, driver tests.
- `docs/SECURITY.md` — threat model, privileges, hardening, audit controls.
- `docs/DESIGN_SYSTEM.md` — visuals, UX rules, accessibility.
- `docs/ROADMAP.md` — milestones, owner, priorities, measurable exit gates.
- `docs/DECISIONS.md` — dated architectural decisions and trade-offs.
- `docs/BUILD_AND_RELEASE.md` — reproducible build, CI, signing, artifacts.
- `docs/INSTALL_AND_RECOVERY.md` — USB, UEFI, dual-boot, rollback.
- `docs/KNOWN_ISSUES.md` — all failures and mitigations.
- **`docs/AI_HANDOFF.md`** — one-page latest state: timestamp, last confirmed commit/branch/PR, last green CI URL, currently working features, unverified features, blockers, security risks, tools/connectors used and their state (without credentials), exact next three tasks, and first verification command/tool action for the next chat.

At the **start** of every new chat: fetch `docs/MASTER_BRIEF.md`, `docs/AI_HANDOFF.md`, `docs/ROADMAP.md`, and relevant code/CI history via an authorized GitHub integration; verify reality before acting. At the **end** of every work session: update `AI_HANDOFF.md` and other affected files, commit when authorized, and state what was actually checked. If the GitHub integration is not connected, say so and request the latest files instead of fabricating context. Keep a compact user-pastable 'resume prompt' referencing these files.

## 9. Deliverable requested from you NOW

Produce a **full technical master plan, not merely inspirational ideas**. In order:

1. Executive summary and precise definition of MVP vs long-term OS.
2. Architecture diagram/layer map and base-distribution decision matrix with reasons.
3. Feature priority matrix: MVP, post-MVP, advanced/research; explicit feasibility limits.
4. Hardware, driver, UEFI, Secure Boot and installation compatibility matrix with known unknowns.
5. OREZ Connect architecture and phone/PC user journeys including permissions and failure handling.
6. Security threat model, hardened defaults, AI-agent permission model, user-visible controls and recovery strategy.
7. Visual/UX design system, screens, interactions, and accessibility standards.
8. GitHub repo structure, CI/release design, licensing obligations, testing strategy.
9. Sequential phases with concrete deliverables, dependencies, risk assessment, resource needs, and **pass/fail exit criteria**. Prioritize safe first boot, installation, networking, drivers, security and functional desktop before ambitious AI polish.
10. Initial 2–3 implementation milestones broken into actionable issues/PRs and one recommended first coding task.
11. Detailed `docs/AI_HANDOFF.md` template and a <=250-word **NEW CHAT RESUME PROMPT**.
12. An explicit list of assumptions and facts requiring verification; link official current sources for technical decisions.

Use professional engineering judgment; make reasonable assumptions when information is missing and mark them. **Do not ask repetitive questions or claim impossible guarantees.** If any plan element is unrealistic, replace it with a safe, technically feasible approach and explain the trade-off. Preserve the user's ownership, control, transparency, security, professional capability, and chosen design aesthetic.
