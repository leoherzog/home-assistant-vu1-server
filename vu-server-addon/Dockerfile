# Unified multi-arch Home Assistant base image (build.json/per-arch tags are
# deprecated). A default is provided so a plain `docker build` also works, since
# Supervisor no longer auto-injects BUILD_FROM.
ARG BUILD_FROM=ghcr.io/home-assistant/base:3.23

# ---------------------------------------------------------------------------
# Stage 1: fetch the pinned upstream VU-Server source (read-only upstream).
# ---------------------------------------------------------------------------
FROM alpine:3.22 AS vu-server-source
# Pinned to the immutable commit behind upstream tag v20240329; the tag itself
# is mutable and could be repointed. Verify with:
#   git ls-remote https://github.com/SasaKaranovic/VU-Server.git refs/tags/v20240329
ARG VU_SERVER_REF=a2a7d2489bdc3059117c6c401e5e68d75577434d
RUN apk add --no-cache git
RUN git init -q /opt/vu-server && \
    git -C /opt/vu-server remote add origin https://github.com/SasaKaranovic/VU-Server.git && \
    git -C /opt/vu-server fetch --depth 1 origin "${VU_SERVER_REF}" && \
    git -C /opt/vu-server checkout -q FETCH_HEAD

# ---------------------------------------------------------------------------
# Stage 2: build the Python virtualenv with the full toolchain (gcc/rust/cargo
# and -dev headers). None of this lands in the runtime image.
# ---------------------------------------------------------------------------
FROM $BUILD_FROM AS builder
RUN apk add --no-cache \
    python3 \
    py3-pip \
    gcc \
    musl-dev \
    python3-dev \
    libffi-dev \
    openssl-dev \
    zlib-dev \
    cargo \
    rust

COPY --from=vu-server-source /opt/vu-server /opt/vu-server

# Build the venv at the same absolute path it will live at in the runtime image
# so its shebangs/paths stay valid after the COPY.
RUN python3 -m venv /opt/vu-server/venv && \
    /opt/vu-server/venv/bin/pip install --no-cache-dir --upgrade pip && \
    /opt/vu-server/venv/bin/pip install --no-cache-dir -r /opt/vu-server/requirements.txt && \
    /opt/vu-server/venv/bin/pip install --no-cache-dir beautifulsoup4

# ---------------------------------------------------------------------------
# Stage 3: runtime image — only the Python runtime + curl, no build toolchain.
# ---------------------------------------------------------------------------
FROM $BUILD_FROM

RUN apk add --no-cache python3 curl

# Application source and the prebuilt virtualenv.
COPY --from=vu-server-source /opt/vu-server /opt/vu-server
COPY --from=builder /opt/vu-server/venv /opt/vu-server/venv

# Run make_version.py to replace template variables.
RUN cd /opt/vu-server && python3 make_version.py

# Persist mutable state under /data (the Supervisor-mounted volume):
#   - config.yaml  : server config + per-install master key
#   - vudials.db   : dial registry / API keys
#   - upload/      : uploaded dial-face images (referenced by the DB)
# run.sh creates /data/vu-server (+ upload) on first boot.
RUN cp /opt/vu-server/config.yaml /opt/vu-server/config.yaml.default && \
    ln -sf /data/vu-server/config.yaml /opt/vu-server/config.yaml && \
    ln -sf /data/vu-server/vudials.db /opt/vu-server/vudials.db && \
    rm -rf /opt/vu-server/upload && \
    ln -sf /data/vu-server/upload /opt/vu-server/upload

# s6-overlay v3 service: run + finish (finish halts the container on fatal exit).
RUN mkdir -p /etc/services.d/vu-server
COPY run.sh /etc/services.d/vu-server/run
COPY finish.sh /etc/services.d/vu-server/finish
COPY ingress_proxy.py /opt/ingress_proxy.py
RUN chmod a+x /etc/services.d/vu-server/run /etc/services.d/vu-server/finish

# Expose VU-Server API port. Supervisor uses the config.yaml `watchdog` URL for
# health monitoring; Docker HEALTHCHECK is ignored by Supervisor.
EXPOSE 5340
