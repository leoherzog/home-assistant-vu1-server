#!/bin/sh
set -e
mkdir -p /data/vu-server/upload
cp -n /opt/vu-server/upload.default/img_blank /data/vu-server/upload/
cp -n /opt/vu-server/config.yaml.default /data/vu-server/config.yaml
