# syntax=docker/dockerfile:1
ARG BUILD_FROM=ghcr.io/home-assistant/base:3.24
FROM $BUILD_FROM

RUN apk add --no-cache python3 nginx

# Must equal the vu-server submodule commit (CI checks this).
ADD https://github.com/SasaKaranovic/VU-Server.git#c2e5b475e6c9f11fbfcd612e6f53c691c1449fbe /opt/vu-server

WORKDIR /opt/vu-server
# pyinstaller only builds upstream's desktop bundles.
RUN python3 -m venv venv && \
    grep -iv '^pyinstaller' requirements.txt > /tmp/requirements.txt && \
    venv/bin/pip install --no-cache-dir --only-binary=:all: -r /tmp/requirements.txt && \
    rm /tmp/requirements.txt && \
    python3 make_version.py && \
    mv config.yaml config.yaml.default && mv upload upload.default && \
    ln -s /data/vu-server/config.yaml config.yaml && \
    ln -s /data/vu-server/vudials.db vudials.db && \
    ln -s /data/vu-server/upload upload && rm -rf .git

# server.py gets SIGTERM only in s6's final kill-all and exits 3 s later, so the kill grace must exceed 3 s.
# The services grace bounds a stop that lands in the finish throttle; together they stay under Supervisor's 10 s stop timeout.
ENV S6_KILL_GRACETIME=6000 \
    S6_SERVICES_GRACETIME=1000

COPY rootfs /

# On failure Docker marks the container unhealthy; Supervisor restarts the app only if the user enables Watchdog.
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s CMD curl -sf http://127.0.0.1:5340/ || exit 1
