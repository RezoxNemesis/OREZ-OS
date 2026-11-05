# Publishable QA dependency image, not an OREZ installation image.
# Build the three documented integration base images first.
FROM orez-everyday-test:20261105
USER root
RUN --mount=type=secret,id=qa_ca_bundle,mode=0444 \
    --mount=type=bind,source=environment/preflight.py,target=/tmp/orez-preflight.py \
    if [ -f /run/secrets/qa_ca_bundle ]; then \
      printf '%s\n' 'Acquire::https::CaInfo "/run/secrets/qa_ca_bundle";' > /etc/apt/apt.conf.d/99-qa-trust; \
    fi; \
    apt-get -o APT::Update::Error-Mode=any update -qq && apt-get install -y --no-install-recommends \
    qemu-system-x86 qemu-utils ovmf swtpm xorriso squashfs-tools zstd \
    openjdk-21-jre-headless vulkan-tools pciutils usbutils iproute2 procps \
    plasma-nm network-manager bluedevil bluez bluez-obexd kio-extras \
    && mkdir -p /opt/orez-qa \
    && dpkg-query -W > /opt/orez-qa/published-packages.txt \
    && install -m 0644 /tmp/orez-preflight.py /opt/orez-qa/preflight.py \
    && runuser -u orez-test -- python3 /opt/orez-qa/preflight.py > /opt/orez-qa/build-preflight.json \
    && cat /opt/orez-qa/build-preflight.json \
    && qemu-system-x86_64 --version && java -version \
    && rm -rf /var/lib/apt/lists/* && rm -f /etc/apt/apt.conf.d/99-qa-trust
USER orez-test
CMD ["bash"]
