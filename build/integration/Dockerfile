# Disposable package/UI test host. Never use as a deployed OS image.
FROM ubuntu@sha256:6a06111c3b0a8600feadb270aec771dc239bf407b25625f93f44ab00e11f4d3c
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update -qq && apt-get install -y --no-install-recommends \
    plasma-workspace plasma-desktop systemsettings kdeconnect xdg-utils kdialog konsole \
    dbus-x11 xvfb x11-utils xdotool scrot python3 sudo \
    && rm -rf /var/lib/apt/lists/*
RUN useradd --create-home --uid 1500 --shell /bin/bash orez-test
CMD ["bash", "/input/package-lifecycle.sh"]
