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

# Update the config.yaml with the configured port
sed -i "s/port: 5340/port: ${PORT}/" config.yaml

# Launch VU-Server (port is configured via config.yaml)
exec python3 server.py --logging info
