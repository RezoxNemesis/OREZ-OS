# OREZ OS — Ease of use and user confidence requirements

**Owner requirement, 6 November 2026.** OREZ must provide Linux's strengths without transferring Linux's historical learning burden to ordinary users. The default experience is a calm, familiar, graphical desktop. It is not a developer-only distribution and must never require terminal knowledge for routine computer use.

## Product promise

> **Simple on the surface. Powerful underneath. Never leave the user lost.**

Users should be able to enjoy creative work, browsing, gaming, files, settings, updates and development without learning package managers, shell commands, filesystem internals, display managers, system services or Linux jargon first. Advanced capabilities remain available by choice; they are not removed or hidden from people who need them.

## Non-negotiable UX principles

1. **Familiar first-run desktop.** Clear application launcher, taskbar/dock, search, file manager, notifications, network/audio/battery controls, clock and predictable power menu. No surprise panels, duplicated launchers or unexplained desktop objects.
2. **One understandable Settings home.** A single searchable entry point with plain-language groups: Personalisation, Display, Sound, Network & Internet, Bluetooth & Devices, Apps, Accounts & Privacy, Accessibility, Storage, Updates & Recovery, and System Information. Avoid exposing KDE subsystem names as the primary navigation.
3. **No terminal requirement for ordinary tasks.** Install/uninstall supported apps, connect Wi-Fi/Bluetooth, configure displays, change wallpaper, update software, manage printers, backups and restore through visible controls. A terminal is an optional advanced tool, not a troubleshooting prerequisite.
4. **Explain before changing.** Every high-impact setting states what it changes, who it affects, and how to reverse it. Prefer previews and reversible toggles. Label advanced options clearly.
5. **Always show the way back.** Every OREZ settings page and guided flow has a clear Back/Close route. Keep navigation breadcrumbs, visible search, Home, and a persistent Help/Recovery entry. Never strand the user in a full-screen setup or terminal.
6. **Recovery is a product feature.** Provide plain-language recovery guidance, safe mode, known-good boot entry where supported, restore points and tested backup/restore workflows. Explain what will be preserved or erased before any destructive action. Never promise recovery until tested.
7. **Friendly errors, not cryptic logs.** Explain the issue in ordinary language, offer safe next steps, and provide a copyable diagnostic report as an optional advanced action. Do not display raw systemd/journal/stack traces as the only guidance.
8. **Safe defaults and consent.** No silent disk formatting, driver removal, remote access, privilege escalation or AI control. Confirm destructive operations with the target disk/device named, a clear consequence and a cancel path. Do not make password/security protections disappear for convenience.
9. **Progressive disclosure.** Keep the common path short. Put developer, package, kernel, service and boot options under clearly marked Advanced sections. Never make advanced users less capable; never make beginners depend on those controls.
10. **Accessibility and consistency.** Keyboard navigation, visible focus, screen-reader labels, scalable text, contrast, reduced motion and clear icon labels. Do not use frosted glass at the expense of legibility.
11. **Local-first and transparent.** Everyday shell, settings, help and app discovery should work offline where practical. Clearly identify when an action needs internet, an account or a download.
12. **One coherent OREZ vocabulary.** Prefer plain terms such as Apps, Files, Settings, Updates, Devices, Backup and Recovery. Avoid mixing Windows/macOS/KDE labels or inventing multiple names for the same function.

## Required first-release flows

- **Find anything:** user can search for an app, file, setting or help topic from the launcher and see clearly distinguished results.
- **Install an app:** user opens Software, searches, sees source/size/permissions, selects Install, authenticates only if required, and sees progress/result. No terminal command.
- **Connect Wi-Fi/Bluetooth:** user opens Quick Settings or Network & Internet, selects a device/network, sees connection state and a useful explanation if it fails.
- **Change appearance:** user previews and applies wallpaper/theme; can restore the previous choice without resetting the system.
- **Recover from confusion:** user can reach Help & Recovery from the desktop, go Home, search guidance, close the current screen, or restart safely without guessing commands.
- **Update safely:** user sees update purpose, size, restart requirement and progress; interrupted updates must not leave the machine unbootable.
- **Developer mode:** user can optionally enable a clearly labelled developer toolset; it must not alter default permissions or make the desktop dependent on a terminal.

## Acceptance tests — block release if failed

- A first-time desktop user can open an app, find a file, connect to Wi-Fi, change wallpaper, change volume, update and shut down using graphical controls only.
- A first-time user can return to the desktop from every OREZ-owned screen using a visible Back/Home/Close action.
- Settings search returns the correct setting and opens its exact page.
- Every destructive operation names the target and consequence before confirmation; Cancel leaves the target unchanged.
- Routine failures offer a plain-language explanation and a safe recovery route; raw logs are optional.
- App installation and updates have visible progress, clear success/failure state and no shell prerequisite.
- Keyboard-only and screen-reader smoke tests cover launcher, Settings, network, app store and recovery.
- All flows work at the supported display scaling and do not rely on color alone.
- These tests are demonstrated in the actual installed OS, not only in a browser mock-up or static design.

## Explicit non-goals

- Do not imitate every Windows or macOS detail at the cost of coherent behavior.
- Do not remove the Linux terminal, package ecosystem, filesystem access, development tools or user control. Keep them available as optional power features.
- Do not auto-install every utility, add clutter, force cloud accounts or enable AI by default.
- Do not call a UI feature complete because a mock-up exists. Record planned, implemented, built, VM-tested, hardware-tested and released separately.

## Current status

These are binding product requirements, not a claim that the full UX is already implemented. Current foundation uses Kubuntu/KDE; full OREZ shell, unified Settings, graphical software management, end-to-end recovery and usability certification remain implementation and verification work. Link this document from the master blueprint and keep the acceptance tests visible in the release roadmap.
