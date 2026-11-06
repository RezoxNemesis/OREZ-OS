# OREZ Help & Recovery

Status: implemented as a source component; package/ISO integration and runtime UI verification pending.

## User experience
- A dedicated launcher opens Help & Recovery.
- Get Help explains safe next steps and the known development-build login issue.
- Recovery Status distinguishes implemented features from unavailable ones.
- System Check runs bounded, read-only local checks and lets the owner choose where to save a JSON report.
- The report avoids usernames, serial numbers, IP addresses, Wi-Fi names, saved passwords, file names and personal logs.

## Safety boundary
This component does not run as root, invoke an administrator prompt, modify settings, mount or repair filesystems, create restore points, perform backups, install packages, roll back drivers or format disks. The recovery page explicitly reports those capabilities as unavailable. A saved diagnostic is informational and is not a certification.

## Acceptance tests
- Python source parses.
- The diagnostic command is bounded and uses a fixed command argument list.
- No shell execution, elevation, disk-write or destructive command is present.
- Recovery copy does not claim an unimplemented capability.
- Launcher, desktop entry and installed-file allowlist agree.
- Settings opens this dedicated application.

A passing source test does not prove Qt runtime, package build, live ISO, login, installer or recovery behavior. Those remain separate gates.
