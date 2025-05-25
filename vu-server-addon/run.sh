#!/usr/bin/with-contenv bashio
# Home Assistant Add-on startup script for VU-Server

# Function to handle cleanup on exit
cleanup() {
    bashio::log.info "Shutting down VU-Server..."
}
trap cleanup SIGTERM SIGINT

# Validate environment
if ! bashio::supervisor.ping; then
    bashio::log.warning "Supervisor is not available, continuing anyway..."
fi

# Read the configured API port from add-on options
PORT=$(bashio::config 'api_port')
if ! bashio::var.has_value "${PORT}"; then
    bashio::log.warning "No API port configured, using default 5340"
    PORT=5340
fi

# Validate port range
if [ "${PORT}" -lt 1024 ] || [ "${PORT}" -gt 65535 ]; then
    bashio::log.fatal "Invalid port ${PORT}. Must be between 1024 and 65535"
    exit 1
fi

bashio::log.info "Starting VU-Server on port ${PORT}..."

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

# Update the config.yaml with the configured port
bashio::log.info "Configuring VU-Server to use port ${PORT}"
if ! sed -i "s/port: [0-9]*/port: ${PORT}/" config.yaml; then
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
    sed -i "s|port:.*|port: $HARDWARE_PORT|" config.yaml
else
    bashio::log.info "No hardware port found, leaving empty for auto-detection"
fi

# Verify Python environment
if [ ! -x "/opt/venv/bin/python" ]; then
    bashio::log.fatal "Python virtual environment not found"
    exit 1
fi

# Launch VU-Server (port is configured via config.yaml)
bashio::log.info "Launching VU-Server..."
exec /opt/venv/bin/python server.py --logging info
