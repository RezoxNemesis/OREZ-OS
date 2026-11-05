# QA dependencies only. A single filesystem layer avoids VFS full-copy growth.
# Ordinary desktop user by default; runtime fixtures explicitly install in a
# rootless disposable container, then run UI tests as UID 1500.
FROM ubuntu@sha256:6a06111c3b0a8600feadb270aec771dc239bf407b25625f93f44ab00e11f4d3c
ENV DEBIAN_FRONTEND=noninteractive LANG=C.UTF-8
RUN --mount=type=secret,id=qa_ca_bundle,mode=0444 \
    --mount=type=bind,source=environment/preflight.py,target=/tmp/orez-preflight.py \
    set -eu; \
    if [ -f /run/secrets/qa_ca_bundle ]; then \
      export CURL_CA_BUNDLE=/run/secrets/qa_ca_bundle npm_config_cafile=/run/secrets/qa_ca_bundle; \
      printf '%s\n' 'Acquire::https::CaInfo "/run/secrets/qa_ca_bundle";' > /etc/apt/apt.conf.d/99-qa-trust; \
    fi; \
    apt-get -o APT::Update::Error-Mode=any update -qq; \
    apt-get install -y --no-install-recommends \
      plasma-workspace plasma-desktop plasma-session-wayland sddm plymouth systemsettings kdeconnect xdg-utils kdialog konsole \
      dbus-x11 xvfb x11-utils xdotool scrot python3 sudo \
      dolphin kate kcalc xwayland wmctrl mesa-utils mesa-utils-extra mesa-vulkan-drivers \
      breeze breeze-icon-theme fonts-noto-core blender ffmpeg g++ make git sqlite3 unzip zip \
      curl gnupg ca-certificates vlc vlc-plugin-qt pulseaudio pulseaudio-utils \
      supertux nodejs npm python3-pil python3-pyside6.qtwidgets python3-pyside6.qttest python3-pyatspi at-spi2-core \
      qemu-system-x86 qemu-system-gui qemu-system-modules-opengl qemu-utils ovmf swtpm xorriso squashfs-tools zstd initramfs-tools-core \
      openjdk-21-jre-headless vulkan-tools pciutils usbutils iproute2 procps \
      plasma-nm network-manager bluedevil bluez bluez-obexd kio-extras; \
    curl -fsSLo /usr/share/keyrings/brave-browser-archive-keyring.gpg \
      https://brave-browser-apt-release.s3.brave.com/brave-browser-archive-keyring.gpg; \
    printf '%s\n' 'Types: deb' 'URIs: https://brave-browser-apt-release.s3.brave.com/' \
      'Suites: stable' 'Components: main' 'Architectures: amd64' \
      'Signed-By: /usr/share/keyrings/brave-browser-archive-keyring.gpg' \
      > /etc/apt/sources.list.d/brave-browser-release.sources; \
    apt-get -o APT::Update::Error-Mode=any update -qq; \
    apt-get install -y --no-install-recommends brave-browser; \
    useradd --create-home --uid 1500 --shell /bin/bash orez-test; \
    mkdir -p /opt/orez-qa; \
    npm install --prefix /opt/orez-qa --ignore-scripts --save-exact playwright-core@1.64.1; \
    gpg --show-keys --with-fingerprint /usr/share/keyrings/brave-browser-archive-keyring.gpg > /opt/orez-qa/brave-key.txt; \
    dpkg-query -W > /opt/orez-qa/published-packages.txt; \
    install -m 0644 /tmp/orez-preflight.py /opt/orez-qa/preflight.py; \
    runuser -u orez-test -- python3 /opt/orez-qa/preflight.py; \
    qemu-system-x86_64 --version; java -version; \
    rm -rf /var/lib/apt/lists/* /root/.npm; \
    rm -f /etc/apt/apt.conf.d/99-qa-trust
USER orez-test
CMD ["bash"]
