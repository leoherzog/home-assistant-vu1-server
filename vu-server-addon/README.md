# VU-Server Home Assistant Add-On

This Home Assistant add-on runs the [`VU-Server`](https://github.com/SasaKaranovic/vu-server) server software to control Streacom [VU1 Dynamic Analogue Dials](https://vudials.com/). VU1 Dials are physical, USB-connected VU meters with eInk screens that can be controlled via API calls. This add-on provides the VU-Server API within your Home Assistant environment, but does not include a custom component for Home Assistant entities.

### Features

- 🔌 Runs VU-Server within Home Assistant as an add-on
- 🌐 Serves the VU-Server Web UI through Home Assistant ingress
- 🔒 Per-install API keys — a unique master key is generated on first start
- 🔄 Auto-starts with Home Assistant

## Configuration

Optional setting:
- `log_level`: debug | info | warning | error (default: info)

The VU-Server Web UI is served through Home Assistant's ingress system. The
VU-Server **API** listens on port `5340` and is reachable on Home Assistant's
internal network; ingress only fronts the Web UI, not the API. The companion
[home-assistant-vu1-devices](https://github.com/leoherzog/home-assistant-vu1-devices)
integration talks to that API directly. To expose the API outside Home
Assistant, map port `5340` to a host port (see **Advanced** below).

### API keys

On the first start of a fresh install the add-on generates a **unique master
key** for your installation, prints it **once** in the add-on log, and stores it
in `/data/vu-server/config.yaml`. Use it to unlock the Web UI and to create API
keys (**Settings → API Keys**) for the Home Assistant integration. Existing
installs keep their previously generated key.

## Usage

1. Connect your VU1 dials via USB to your Home Assistant device
2. Install and start this add-on
3. Access the VU-Server Web UI by clicking "Open Web UI" in the add-on interface
4. Use the web interface or API endpoints through Home Assistant's ingress proxy

### API Access

All API endpoints are available through Home Assistant's ingress system. When accessing the API programmatically, use relative URLs from within Home Assistant or the full ingress URL path.
Ingress request bodies are buffered and limited to ~16 MB; for larger uploads, use direct port mapping below.

## Advanced: Enabling External Access

If you need direct external access to the VU-Server API:

1. Go to **Settings** → **Add-ons** → **VU-Server**
2. In the **Network** section (bottom of the page), map **Host Port** `5340` to **Container Port** `5340/tcp`
3. Click **Save** and restart the add-on
4. The VU-Server API will then be accessible at `http://your-ha-ip:5340`

⚠️ **Security Warning**: The API is protected by VU-Server's own API-key system (and each install now gets a unique master key rather than a public default), but mapping port `5340` to a host port exposes that API directly on your network — outside Home Assistant's authentication and the ingress allowlist. Only enable external access if you understand the implications, and keep your keys secret.

## Troubleshooting

- Ensure your VU1 Dials are properly connected via USB.
- Check the add-on logs for any error messages.
- If dials are not auto-discovered, try unplugging and reconnecting them.

## Support

For support with the VU-Server software itself, please refer to the [official VU-Server documentation](https://github.com/SasaKaranovic/VU-Server).

For add-on specific issues, please report them in the [GitHub repository](https://github.com/leoherzog/home-assistant-vu1-server).
