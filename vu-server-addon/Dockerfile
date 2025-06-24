ARG BUILD_FROM
FROM alpine:latest AS vu-server-source

# Install git for cloning
RUN apk add --no-cache git

# Clone VU-Server at specific commit/tag
RUN git clone https://github.com/SasaKaranovic/VU-Server.git /opt/vu-server && \
    cd /opt/vu-server && \
    git checkout v20240329

FROM $BUILD_FROM

# Install Python and other dependencies
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

# Copy VU-Server source code from build stage
COPY --from=vu-server-source /opt/vu-server /opt/vu-server

# Create virtual environment and install dependencies
RUN python3 -m venv /opt/venv && \
    /opt/venv/bin/pip install --upgrade pip && \
    /opt/venv/bin/pip install -r /opt/vu-server/requirements.txt && \
    /opt/venv/bin/pip install beautifulsoup4

# Run make_version.py to replace template variables
RUN cd /opt/vu-server && python3 make_version.py

# Create persistent data directory structure and backup original config
RUN mkdir -p /data/vu-server && \
    cp /opt/vu-server/config.yaml /opt/vu-server/config.yaml.default && \
    ln -sf /data/vu-server/config.yaml /opt/vu-server/config.yaml && \
    ln -sf /data/vu-server/vudials.db /opt/vu-server/vudials.db

# Create s6-overlay service directory and copy files
RUN mkdir -p /etc/services.d/vu-server
COPY run.sh /etc/services.d/vu-server/run
COPY ingress_proxy.py /opt/ingress_proxy.py
RUN chmod a+x /etc/services.d/vu-server/run

# Expose VU-Server API port
EXPOSE 5340
