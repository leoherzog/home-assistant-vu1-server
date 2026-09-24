# Changelog

## 0.6.0

- Updated VU-Server to upstream `v20260918`.
- Upstream now binds to `server.hostname` in `config.yaml`, which defaults to `localhost`. The app clears it on every start so the integration can still reach port `5340`.
- Security fixes from upstream: parameterized SQL, per-dial access checks on every dial endpoint, and a key required to read dial status, image and CRC. A key you issue now reads and controls only the dials granted to it.
- Upstream now requires a key for the dial image. Under ingress the app adds it to the dial page's request; on a mapped port the dial page cannot show the image.
- The Web UI adds **Reset all dials**, which reboots every dial on the bus, and **Reset dial** on each dial's page, which re-sends that dial's value, backlight and image.
- Failed value and backlight writes are retried with backoff until a dial fails five times in a row, and the API stays responsive while the bus is busy.
- Dial image paths in the API are now absolute, so the integration's image entities may refresh once after the update.
- Keys in logged request URLs are redacted.
- Stopping the app takes about 7 s. s6 now waits 6 s after signalling the server, which needs 3 s to exit after turning the dials off. Upstream's shutdown lines now reach the app log.
- The image no longer includes `pyinstaller`.

## 0.5.0

- Uses upstream's default master key, which the Web UI has built in.
- Fixed: dials without a custom image show the default image again instead of an error.
- Fixed: a `hardware.port` set in `config.yaml` is no longer cleared on every start.
- Fixed: the app stops cleanly on hosts that confine the container runtime with AppArmor.
- If the VU1 hub is missing, the server retries every few seconds and recovers once the hub is plugged in.
- Replaced the ingress proxy with nginx, which does not log key-bearing request URLs.
- `log_level` now accepts only `debug` or `info`, the two levels upstream supports. If yours is set to `warning` or `error`, change it to `info`.
- The AppArmor profile now includes Docker's default deny rules.
- Updated the base image to Alpine 3.24 (Python 3.14).
- "Add-on" is now "app" throughout, following Home Assistant's rename.

## 0.4.0

- New installs get a unique master key; installs created before 0.4.0 keep their existing key.
