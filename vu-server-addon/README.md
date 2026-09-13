# VU-Server Home Assistant App

Runs [VU-Server](https://github.com/SasaKaranovic/VU-Server) to control Streacom [VU1 Dynamic Analogue Dials](https://vudials.com/), USB-connected analogue meters with eInk screens. It provides the VU-Server API and Web UI; for Home Assistant entities, use the companion integration [home-assistant-vu1-devices](https://github.com/leoherzog/home-assistant-vu1-devices).

## What the app changes

The upstream source runs unmodified with its default config. nginx rewrites a handful of absolute URLs so the Web UI works under ingress.

## Configuration

- `log_level`: `debug` | `info` (default `info`)

## Usage

1. Connect the VU1 hub via USB and start the app.
2. Click **Open Web UI**, then **API Keys** in the top bar, and create a key.
3. Paste the key into the companion integration. It discovers the host and port by itself.

The Web UI works only through ingress. For programmatic access, use the companion integration, which reaches the API on the internal network at port `5340`.

### Master key

The app uses upstream's default master key, stored in `/data/vu-server/config.yaml`. The Web UI has this key built in and needs it to list dials and manage API keys, so do not change it. VU-Server logs failed requests with their keys, so treat the app log as secret.

## Security

- The master key is upstream's public default, so anything that can reach port `5340` has admin access. Other apps on the internal network can reach it.
- Several upstream endpoints need no key.
- Upstream builds SQL queries from request values, so treat any key you issue as admin-equivalent.
- Mapping `5340` to a host port (under **Network** on the app's configuration page) exposes all of the above to your LAN.

## Troubleshooting

- The VU1 hub must be connected. If it is missing, the server retries every few seconds and recovers once the hub is plugged in.
- Turn on the app's **Watchdog** toggle to restart it automatically when its health check fails.

## Support

For VU-Server itself, see the [upstream project](https://github.com/SasaKaranovic/VU-Server). Report problems with the app in [this repository](https://github.com/leoherzog/home-assistant-vu1-server/issues).
