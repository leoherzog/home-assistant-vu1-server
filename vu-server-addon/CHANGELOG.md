# Changelog

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
