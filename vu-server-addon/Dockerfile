# syntax=docker/dockerfile:1
ARG BUILD_FROM=ghcr.io/home-assistant/base:3.24
FROM $BUILD_FROM

RUN apk add --no-cache python3 nginx

# Must equal the vu-server submodule commit (CI checks this).
ADD https://github.com/SasaKaranovic/VU-Server.git#62a405972c629858085cf17ec5e3d2b110a34581 /opt/vu-server

WORKDIR /opt/vu-server
RUN python3 -m venv venv && \
    venv/bin/pip install --no-cache-dir --only-binary=:all: -r requirements.txt && \
    python3 make_version.py && \
    mv config.yaml config.yaml.default && mv upload upload.default && \
    ln -s /data/vu-server/config.yaml config.yaml && \
    ln -s /data/vu-server/vudials.db vudials.db && \
    ln -s /data/vu-server/upload upload && rm -rf .git

COPY rootfs /

# On failure Docker marks the container unhealthy; Supervisor restarts the app only if the user enables Watchdog.
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s CMD curl -sf http://127.0.0.1:5340/ || exit 1
