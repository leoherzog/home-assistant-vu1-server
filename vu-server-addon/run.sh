#!/usr/bin/with-contenv bashio
# Home Assistant Add-on startup script for VU-Server

# Early signal handling to ensure graceful shutdown during startup
# This trap is replaced with the full cleanup() trap after processes start
early_cleanup() {
    bashio::log.warning "Received shutdown signal during startup, exiting..."
    [ -n "$VU_SERVER_PID" ] && kill -TERM $VU_SERVER_PID 2>/dev/null || true
    [ -n "$PROXY_PID" ] && kill -TERM $PROXY_PID 2>/dev/null || true
    [ -n "$TAIL_PID" ] && kill -TERM $TAIL_PID 2>/dev/null || true
    exit 0
}
trap early_cleanup SIGTERM SIGINT

# Validate environment
if ! bashio::supervisor.ping; then
    bashio::log.warning "Supervisor is not available, continuing anyway..."
fi

# Use fixed port for VU-Server (ingress handles external access)
PORT=5340

# Error monitoring and restart configuration
LOG_FILE="/tmp/vu-server.log"
MAX_RESTARTS=5
RESTART_WINDOW=600  # seconds — reset restart counter after this
ERROR_CHECK_INTERVAL=10
ERROR_THRESHOLD=3

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

# --- Helper Functions ---

# Abort startup and clean up the spawned server process.
abort_startup() {
    bashio::log.error "$1"
    if [ -n "$VU_SERVER_PID" ]; then
        bashio::log.info "Stopping VU-Server (PID: $VU_SERVER_PID)..."
        kill -TERM $VU_SERVER_PID 2>/dev/null || true
        sleep 2
        if kill -0 $VU_SERVER_PID 2>/dev/null; then
            bashio::log.warning "Force killing VU-Server..."
            kill -KILL $VU_SERVER_PID 2>/dev/null || true
        fi
    fi
    exit 1
}

# Start VU-Server, wait for readiness, and capture PID.
# Usage: start_server <ready_timeout_seconds>
start_server() {
    local ready_timeout=${1:-30}

    > "$LOG_FILE"

    /opt/vu-server/venv/bin/python server.py --logging "${LOG_LEVEL}" >> "$LOG_FILE" 2>&1 &
    VU_SERVER_PID=$!

    bashio::log.info "Waiting for VU-Server (PID: $VU_SERVER_PID) to be ready (timeout: ${ready_timeout}s)..."
    local i
    for (( i=1; i<=ready_timeout; i++ )); do
        if ! kill -0 $VU_SERVER_PID 2>/dev/null; then
            bashio::log.error "VU-Server process died during startup"
            return 1
        fi
        if curl -sf http://localhost:${PORT}/ >/dev/null 2>&1; then
            bashio::log.info "VU-Server is ready after ${i} seconds"
            return 0
        fi
        sleep 1
    done

    bashio::log.error "VU-Server failed to become ready after ${ready_timeout} seconds"
    kill -TERM $VU_SERVER_PID 2>/dev/null || true
    return 1
}

# Background monitor: detect persistent I/O errors and kill the server.
error_monitor() {
    while sleep "$ERROR_CHECK_INTERVAL"; do
        # Stop if server is already dead
        kill -0 $VU_SERVER_PID 2>/dev/null || return 0

        local count
        count=$(grep -c "OSError.*I/O error" "$LOG_FILE" 2>/dev/null || echo 0)
        if [ "$count" -ge "$ERROR_THRESHOLD" ]; then
            bashio::log.error "Detected $count I/O errors in server log, triggering restart..."
            kill -TERM $VU_SERVER_PID 2>/dev/null
            return 0
        fi
    done
}

# --- Main Flow ---

# Stream server log to container output (persists across server restarts)
> "$LOG_FILE"
tail -F "$LOG_FILE" &
TAIL_PID=$!

# First server start (30s readiness timeout)
bashio::log.info "Launching VU-Server on port ${PORT}..."
if ! start_server 30; then
    abort_startup "VU-Server failed to start properly"
fi

# Launch Ingress proxy (always needed for Home Assistant integration)
bashio::log.info "Launching Ingress proxy on port 8099..."
/opt/vu-server/venv/bin/python /opt/ingress_proxy.py ${PORT} &
PROXY_PID=$!

# Watch for proxy death and signal main script
(wait $PROXY_PID 2>/dev/null; bashio::log.warning "Ingress proxy exited unexpectedly"; kill -TERM $$ 2>/dev/null) &
PROXY_WATCHER_PID=$!

# Enhanced cleanup function following Home Assistant add-on best practices
cleanup() {
    bashio::log.info "Shutting down VU-Server add-on..."

    # First try graceful shutdown with SIGTERM
    [ -n "$PROXY_PID" ] && kill -TERM $PROXY_PID 2>/dev/null || true
    [ -n "$VU_SERVER_PID" ] && kill -TERM $VU_SERVER_PID 2>/dev/null || true
    [ -n "$MONITOR_PID" ] && kill -TERM $MONITOR_PID 2>/dev/null || true
    [ -n "$PROXY_WATCHER_PID" ] && kill -TERM $PROXY_WATCHER_PID 2>/dev/null || true
    [ -n "$TAIL_PID" ] && kill -TERM $TAIL_PID 2>/dev/null || true

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

    rm -f "$LOG_FILE"
    bashio::log.info "VU-Server add-on shutdown complete"
    exit 0
}
trap cleanup SIGTERM SIGINT

# --- Restart Loop ---

restart_count=0
window_start=$(date +%s)

while true; do
    # Start error monitor for this server lifetime
    error_monitor &
    MONITOR_PID=$!

    # Block until server exits (crash or killed by monitor)
    wait $VU_SERVER_PID 2>/dev/null
    exit_code=$?

    # Stop the monitor
    kill $MONITOR_PID 2>/dev/null || true
    wait $MONITOR_PID 2>/dev/null || true

    # Check restart budget
    now=$(date +%s)
    if [ $((now - window_start)) -gt $RESTART_WINDOW ]; then
        restart_count=0
        window_start=$now
    fi

    restart_count=$((restart_count + 1))

    if [ $restart_count -ge $MAX_RESTARTS ]; then
        bashio::log.fatal "VU-Server has restarted $MAX_RESTARTS times in ${RESTART_WINDOW}s, giving up"
        exit 1
    fi

    bashio::log.warning "VU-Server exited (code: $exit_code), restarting in 5 seconds... (attempt $restart_count/$MAX_RESTARTS)"
    sleep 5

    if ! start_server 15; then
        bashio::log.error "VU-Server failed to restart, will retry..."
        continue
    fi
done
