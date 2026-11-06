# Image construction tools only. No desktop or consumer applications in this
# helper image. Run with rootless Docker, no devices/ports/additional privileges.
FROM ubuntu@sha256:6a06111c3b0a8600feadb270aec771dc239bf407b25625f93f44ab00e11f4d3c
ENV DEBIAN_FRONTEND=noninteractive LANG=C.UTF-8
RUN --mount=type=secret,id=qa_ca_bundle,mode=0444 \
    set -eu; \
    if [ -f /run/secrets/qa_ca_bundle ]; then \
      printf '%s\n' 'Acquire::https::CaInfo "/run/secrets/qa_ca_bundle";' > /etc/apt/apt.conf.d/99-build-trust; \
    fi; \
    sed -i 's|http://archive.ubuntu.com|https://archive.ubuntu.com|; s|http://security.ubuntu.com|https://security.ubuntu.com|' /etc/apt/sources.list.d/ubuntu.sources; \
    apt-get -o APT::Update::Error-Mode=any update -qq; \
    apt-get install -y --no-install-recommends ca-certificates curl gnupg \
      python3 python3-apt xorriso squashfs-tools zstd apt-utils dpkg-dev; \
    rm -rf /var/lib/apt/lists/*; \
    rm -f /etc/apt/apt.conf.d/99-build-trust
CMD ["bash"]
