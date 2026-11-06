# Test-only desktop applications. Never use this image as an OS release.
FROM orez-desktop-test:20261105
ENV DEBIAN_FRONTEND=noninteractive LANG=C.UTF-8
RUN apt-get update -qq && apt-get install -y --no-install-recommends \
    curl gnupg ca-certificates vlc vlc-plugin-qt pulseaudio pulseaudio-utils \
    supertux nodejs npm python3-pil \
    && rm -rf /var/lib/apt/lists/*
# Brave's documented Debian repository; scoped signing key, no pipe-to-shell.
RUN --mount=type=secret,id=qa_ca_bundle,mode=0444 \
    if [ -f /run/secrets/qa_ca_bundle ]; then \
      export CURL_CA_BUNDLE=/run/secrets/qa_ca_bundle; \
      printf '%s\n' 'Acquire::https::CaInfo "/run/secrets/qa_ca_bundle";' > /etc/apt/apt.conf.d/99-qa-trust; \
    fi; \
    curl -fsSLo /usr/share/keyrings/brave-browser-archive-keyring.gpg \
      https://brave-browser-apt-release.s3.brave.com/brave-browser-archive-keyring.gpg \
    && printf '%s\n' 'Types: deb' \
      'URIs: https://brave-browser-apt-release.s3.brave.com/' \
      'Suites: stable' 'Components: main' 'Architectures: amd64' \
      'Signed-By: /usr/share/keyrings/brave-browser-archive-keyring.gpg' \
      > /etc/apt/sources.list.d/brave-browser-release.sources \
    && apt-get update && apt-get install -y --no-install-recommends brave-browser \
    && mkdir -p /opt/orez-qa \
    && gpg --show-keys --with-fingerprint /usr/share/keyrings/brave-browser-archive-keyring.gpg > /opt/orez-qa/brave-key.txt \
    && dpkg-query -W > /opt/orez-qa/packages.txt \
    && rm -rf /var/lib/apt/lists/* \
    && rm -f /etc/apt/apt.conf.d/99-qa-trust
RUN --mount=type=secret,id=qa_ca_bundle,mode=0444 \
    if [ -f /run/secrets/qa_ca_bundle ]; then export npm_config_cafile=/run/secrets/qa_ca_bundle; fi; \
    npm install --prefix /opt/orez-qa --ignore-scripts --save-exact playwright-core@1.64.1
