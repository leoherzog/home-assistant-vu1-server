#!/usr/bin/env bash
# Home Assistant Add-on startup script for VU-Server
set -e

# Read the configured API port from add-on options
PORT=$(jq --raw-output '.api_port' /data/options.json)
if [ -z "$PORT" ] || [ "$PORT" = "null" ]; then
  PORT=5340
fi

echo "Starting VU-Server on port ${PORT}..."
cd /opt/vu-server || exit 1

# Launch VU-Server (listens for API calls on the specified port)
exec python3 server.py --port "${PORT}"
