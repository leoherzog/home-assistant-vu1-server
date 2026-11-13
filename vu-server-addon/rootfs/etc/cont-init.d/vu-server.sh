#!/bin/sh
set -e
config=/data/vu-server/config.yaml
mkdir -p /data/vu-server/upload
cp -n /opt/vu-server/upload.default/img_blank /data/vu-server/upload/
# Upstream binds to server.hostname and treats an empty value as all interfaces, which the integration needs to reach :5340.
# Keep the key: without it, or with an empty file, upstream falls back to built-in defaults, which bind to localhost.
if ! awk '/^server:/ { s = 1; next } /^[^[:space:]#]/ { s = 0 } s && /^[[:space:]]+hostname:/ { f = 1 } END { exit !f }' "$config" 2>/dev/null; then
  [ ! -s "$config" ] || echo "cont-init: $config has no server.hostname key, replacing it with the default"
  cp /opt/vu-server/config.yaml.default "$config"
fi
# Write only when needed, so an unwritable config.yaml does not halt startup.
if grep -q '^[[:space:]]*hostname:[[:space:]]*[^[:space:]]' "$config"; then
  sed -i 's/^\([[:space:]]*hostname:\).*/\1/' "$config"
fi
