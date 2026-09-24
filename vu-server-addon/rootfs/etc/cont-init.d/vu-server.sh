#!/bin/sh
set -e
mkdir -p /data/vu-server/upload
cp -n /opt/vu-server/upload.default/img_blank /data/vu-server/upload/
cp -n /opt/vu-server/config.yaml.default /data/vu-server/config.yaml
# Upstream binds to server.hostname and treats an empty value as all interfaces, which the integration needs to reach :5340.
# Keep the key: without it upstream falls back to built-in defaults, including port 3000.
# Write only when needed, so an unwritable config.yaml does not halt startup.
if grep -q '^[[:space:]]*hostname:[[:space:]]*[^[:space:]]' /data/vu-server/config.yaml; then
  sed -i 's/^\([[:space:]]*hostname:\).*/\1/' /data/vu-server/config.yaml
fi
