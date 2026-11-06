#!/usr/bin/env bash
# Runs ONLY inside an explicitly labelled, disposable container, never on a host.
set -euo pipefail
trap 'printf "FAILED at line %s: %s\n" "$LINENO" "$BASH_COMMAND" >&2' ERR
[[ -f /.dockerenv && "${OREZ_DISPOSABLE_TEST:-}" == 1 ]] || { echo 'Disposable container required'; exit 2; }
mkdir -p /evidence
test -f /input/orez-shell.deb
printf 'PACKAGE LIFECYCLE — Ubuntu container, not ISO/boot/hardware validation\n'
cat /etc/os-release
sha256sum /input/orez-shell.deb
# Network is disabled by the orchestrator. Dependencies were resolved during image build.
# Official Ubuntu containers strip /usr/share/doc; normal Kubuntu desktops do not.
# Include only this package's docs to make this fixture represent that desktop.
apt_options=(-y -o 'Dpkg::Options::=--path-include=/usr/share/doc/orez' -o 'Dpkg::Options::=--path-include=/usr/share/doc/orez/*')
printf 'Fixture: preserve OREZ documentation despite minimal-container path exclusions.\n'
apt-get "${apt_options[@]}" install /input/orez-shell.deb > /evidence/install.log 2>&1
dpkg-query -W -f='${Package} ${Version} ${Status}\n' orez-shell plasma-workspace systemsettings kdeconnect
dpkg --audit
count=0
while IFS= read -r rel; do
    [[ -n "$rel" && "$rel" != \#* ]] || continue
    test -f "/$rel"
    owner="$(dpkg-query -S "/$rel")"
    printf 'Ownership: %s\n' "$owner"
    [[ "$owner" == "orez-shell: /$rel" ]]
    count=$((count + 1))
done < /input/installed-files.txt
printf 'PASS: %s installed payload files owned by dpkg\n' "$count"
test ! -e /usr/bin/calamares
test ! -e /usr/lib/systemd/system/orez-live-verify.service
sudo -u orez-test -H /usr/bin/orezctl status
sudo -u orez-test -H /usr/bin/orezctl appearance disable
sudo -u orez-test -H /usr/bin/orezctl appearance enable
printf 'PASS: ordinary-user status and reversible appearance controls\n'
# Real reinstall of same version, without --force-depends or network.
apt-get "${apt_options[@]}" install --reinstall /input/orez-shell.deb > /evidence/reinstall.log 2>&1
printf 'PASS: APT reinstall\n'
if [[ "${OREZ_CAPTURE_NATIVE:-0}" == 1 ]]; then
    bash /input/capture-native.sh
fi
printf 'unrelated user data\n' > /home/orez-test/preserve-me.txt
sha256sum /home/orez-test/preserve-me.txt > /evidence/sentinel.sha256
apt-get purge -y orez-shell > /evidence/purge.log 2>&1
while IFS= read -r rel; do
    [[ -n "$rel" && "$rel" != \#* ]] || continue
    test ! -e "/$rel"
done < /input/installed-files.txt
sha256sum --check /evidence/sentinel.sha256
command -v systemsettings
command -v kdeconnect-app
test -z "$(dpkg --audit)"
printf 'PASS: purge removed package files; unrelated data and dependency applications retained\n'
printf 'Not tested: version upgrade, ISO installation, reboot, encryption, recovery, NVIDIA, Secure Boot.\n'
