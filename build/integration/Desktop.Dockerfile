# Test-only extension of the locally provisioned Ubuntu/KDE dependency image.
# Build the base with build/integration/Dockerfile first. Record image IDs per run.
FROM orez-package-test:20261105
ENV DEBIAN_FRONTEND=noninteractive LANG=C.UTF-8
RUN apt-get update -qq && apt-get install -y --no-install-recommends \
    dolphin konsole kate kcalc kdialog xwayland wmctrl \
    mesa-utils mesa-utils-extra mesa-vulkan-drivers \
    breeze breeze-icon-theme fonts-noto-core \
    blender ffmpeg g++ make git sqlite3 unzip zip \
    && rm -rf /var/lib/apt/lists/*
CMD ["bash", "/input/desktop-scenarios.sh"]
