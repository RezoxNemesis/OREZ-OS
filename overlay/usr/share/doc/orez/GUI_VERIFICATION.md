# OREZ GUI VM test (source-visible, opt-in)
This strictly read-only process probe only runs with both `boot=casper` and `orez.verify=1` kernel parameters. It executes as `nobody` with no network, home access or system write access. It observes whether Plasma Shell and the display manager are running, then writes a marker to the VM's local serial port. Normal OREZ desktop usage does not activate it.

Inspect with `systemctl status orez-gui-verify.service`. The user may disable it through normal systemd administration. A passed marker **does not** certify visual UI, UEFI, NVIDIA, Secure Boot, installation, keyboard operation or recovery; a separate screenshot must be manually reviewed.
