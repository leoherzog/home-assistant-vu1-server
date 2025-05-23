ARG BUILD_FROM
FROM alpine:latest AS vu-server-source

# Install git for cloning
RUN apk add --no-cache git

# Clone VU-Server at specific commit/tag
RUN git clone https://github.com/SasaKaranovic/VU-Server.git /opt/vu-server && \
    cd /opt/vu-server && \
    git checkout v20240329

FROM $BUILD_FROM

# Install Python, bashio, and any needed libs
RUN apk add --no-cache \
    python3 \
    py3-pip \
    bashio

# Copy VU-Server source code from build stage
COPY --from=vu-server-source /opt/vu-server /opt/vu-server

# Create virtual environment and install VU-Server Python dependencies
RUN python3 -m venv /opt/venv && \
    /opt/venv/bin/pip install -r /opt/vu-server/requirements.txt

# Create s6-overlay service directory and copy the run script
RUN mkdir -p /etc/services.d/vu-server
COPY run.sh /etc/services.d/vu-server/run
RUN chmod a+x /etc/services.d/vu-server/run

# Expose VU-Server API port
EXPOSE 5340
