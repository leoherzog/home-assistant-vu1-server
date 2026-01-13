#!/usr/bin/with-contenv bashio
# Home Assistant Add-on startup script for VU-Server

# Early signal handling to ensure graceful shutdown during startup
# This trap is replaced with the full cleanup() trap after processes start
early_cleanup() {
    bashio::log.warning "Received shutdown signal during startup, exiting..."
    [ -n "$VU_SERVER_PID" ] && kill -TERM $VU_SERVER_PID 2>/dev/null || true
    [ -n "$PROXY_PID" ] && kill -TERM $PROXY_PID 2>/dev/null || true
    exit 0
}
trap early_cleanup SIGTERM SIGINT

# Validate environment
if ! bashio::supervisor.ping; then
    bashio::log.warning "Supervisor is not available, continuing anyway..."
fi

# Use fixed port for VU-Server (ingress handles external access)
PORT=5340

# Read user configuration options
LOG_LEVEL=$(bashio::config 'log_level' 'info')
bashio::log.info "Configuration: log_level=${LOG_LEVEL}"

# Initialize persistent storage for VU-Server data
bashio::log.info "Initializing persistent storage..."

# Create persistent data directory if it doesn't exist
if [ ! -d "/data/vu-server" ]; then
    bashio::log.info "Creating persistent storage directory..."
    mkdir -p /data/vu-server
fi

# Copy default config.yaml to persistent storage if it doesn't exist
if [ ! -f "/data/vu-server/config.yaml" ]; then
    bashio::log.info "Initializing default config.yaml in persistent storage..."
    cp /opt/vu-server/config.yaml.default /data/vu-server/config.yaml
else
    bashio::log.info "Using existing persistent config.yaml"
fi

bashio::log.info "Starting VU-Server on port ${PORT}..."
bashio::log.info "Web UI available via Home Assistant ingress (Open Web UI button)."

# Change to VU-Server directory
cd /opt/vu-server || {
    bashio::log.fatal "Failed to change to VU-Server directory"
    exit 1
}

# Verify required files exist
if [ ! -f "server.py" ]; then
    bashio::log.fatal "VU-Server files not found"
    exit 1
fi

if [ ! -f "config.yaml" ]; then
    bashio::log.fatal "VU-Server config.yaml not found"
    exit 1
fi

# Update the config.yaml with the fixed port
bashio::log.info "Configuring VU-Server to use port ${PORT}"
if ! sed -i "/^server:/,/^[^[:space:]]/ s/port: [0-9]*/port: ${PORT}/" config.yaml; then
    bashio::log.error "Failed to update config.yaml"
    exit 1
fi

# Configure hardware port to avoid auto-detection issues
bashio::log.info "Configuring hardware port..."
# Try to find the VU1 device - look for common USB serial devices
HARDWARE_PORT=""
for device in /dev/ttyACM* /dev/ttyUSB*; do
    if [ -e "$device" ]; then
        bashio::log.info "Found potential device: $device"
        HARDWARE_PORT="$device"
        break
    fi
done

if [ -n "$HARDWARE_PORT" ]; then
    bashio::log.info "Setting hardware port to: $HARDWARE_PORT"
    sed -i "/^hardware:/,/^[^[:space:]]/ s|port:.*|port: $HARDWARE_PORT|" config.yaml
else
    bashio::log.info "No hardware port found, leaving empty for auto-detection"
fi

# Verify Python environment
if [ ! -x "/opt/vu-server/venv/bin/python" ]; then
    bashio::log.fatal "Python virtual environment not found"
    exit 1
fi

# Launch VU-Server in background
bashio::log.info "Launching VU-Server on port ${PORT}..."
/opt/vu-server/venv/bin/python server.py --logging "${LOG_LEVEL}" &
VU_SERVER_PID=$!

# Wait for VU-Server to be fully ready
bashio::log.info "Waiting for VU-Server to be ready..."
READY=false
for i in {1..30}; do
    if curl -sf http://localhost:${PORT}/ >/dev/null 2>&1; then
        bashio::log.info "VU-Server is ready after ${i} seconds"
        READY=true
        break
    fi
    sleep 1
done

if [ "$READY" = false ]; then
    bashio::log.error "VU-Server failed to start properly after 30 seconds"
    exit 1
fi

# Publish discovery info to Supervisor for custom integration auto-discovery
bashio::log.info "Publishing discovery info to Supervisor..."
API_KEY=$(grep -Po '(?<=master_key: ).*' /data/vu-server/config.yaml | tr -d '"' | tr -d "'" | tr -d ' ')
CONTAINER_IP=$(hostname -i | awk '{print $1}')

if [ -n "$API_KEY" ]; then
    config=$(bashio::var.json \
        host "${CONTAINER_IP}" \
        port "^${PORT}" \
        api_key "${API_KEY}" \
    )

    if bashio::discovery "vu_server" "${config}" > /dev/null 2>&1; then
        bashio::log.info "Discovery published successfully"
    else
        bashio::log.warning "Discovery publish failed (custom integration may not auto-discover)"
    fi
else
    bashio::log.warning "Could not publish discovery (missing API key)"
fi

# Launch Ingress proxy (always needed for Home Assistant integration)
bashio::log.info "Launching Ingress proxy on port 8099..."
/opt/vu-server/venv/bin/python /opt/ingress_proxy.py ${PORT} &
PROXY_PID=$!

# Enhanced cleanup function following Home Assistant add-on best practices
cleanup() {
    bashio::log.info "Shutting down VU-Server add-on..."

    # First try graceful shutdown with SIGTERM
    if [ -n "$PROXY_PID" ]; then
        bashio::log.info "Stopping ingress proxy (PID: $PROXY_PID)..."
        kill -TERM $PROXY_PID 2>/dev/null || true
    fi

    if [ -n "$VU_SERVER_PID" ]; then
        bashio::log.info "Stopping VU-Server (PID: $VU_SERVER_PID)..."
        kill -TERM $VU_SERVER_PID 2>/dev/null || true
    fi

    # Wait a moment for graceful shutdown
    sleep 2

    # Force kill if still running
    if [ -n "$PROXY_PID" ] && kill -0 $PROXY_PID 2>/dev/null; then
        bashio::log.warning "Force killing ingress proxy..."
        kill -KILL $PROXY_PID 2>/dev/null || true
    fi

    if [ -n "$VU_SERVER_PID" ] && kill -0 $VU_SERVER_PID 2>/dev/null; then
        bashio::log.warning "Force killing VU-Server..."
        kill -KILL $VU_SERVER_PID 2>/dev/null || true
    fi

    # Also kill any lingering processes by name (fallback)
    pkill -f "python3.*ingress_proxy.py" 2>/dev/null || true
    pkill -f "python.*server.py" 2>/dev/null || true

    bashio::log.info "VU-Server add-on shutdown complete"
    exit 0
}
trap cleanup SIGTERM SIGINT

# Wait for either process to exit
wait -n $VU_SERVER_PID $PROXY_PID

# If we get here, one process exited - trigger cleanup for the other
bashio::log.warning "A process exited unexpectedly, initiating cleanup..."
cleanup
