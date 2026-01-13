# VU-Server Home Assistant Add-On

This Home Assistant add-on runs the [`VU-Server`](https://github.com/SasaKaranovic/vu-server) server software to control Streacom [VU1 Dynamic Analogue Dials](https://vudials.com/). VU1 Dials are physical, USB-connected VU meters with eInk screens that can be controlled via API calls. This add-on provides the VU-Server API within your Home Assistant environment, but does not include a custom component for Home Assistant entities.

### Features

- 🔌 Runs VU-Server within Home Assistant as an add-on
- 🌐 Provides HTTP API for controlling VU1 dials via Home Assistant ingress
- 🔒 Secure ingress-only access by default
- 🔄 Auto-starts with Home Assistant

## Configuration

This add-on requires no configuration options. The VU-Server runs on a fixed internal port and is accessed through Home Assistant's ingress system.

## Usage

1. Connect your VU1 dials via USB to your Home Assistant device
2. Install and start this add-on
3. Access the VU-Server Web UI by clicking "Open Web UI" in the add-on interface
4. Use the web interface or API endpoints through Home Assistant's ingress proxy

### API Access

All API endpoints are available through Home Assistant's ingress system. When accessing the API programmatically, use relative URLs from within Home Assistant or the full ingress URL path.

## Advanced: Enabling External Access

If you need direct external access to the VU-Server API:

1. Go to **Settings** → **Add-ons** → **VU-Server**
2. In the **Network** section (bottom of the page), map **Host Port** `5340` to **Container Port** `5340/tcp`
3. Click **Save** and restart the add-on
4. The VU-Server API will then be accessible at `http://your-ha-ip:5340`

⚠️ **Security Warning**: Enabling external access bypasses Home Assistant's authentication. Only enable this if you understand the security implications.

## Troubleshooting

- Ensure your VU1 Dials are properly connected via USB.
- Check the add-on logs for any error messages.
- If dials are not auto-discovered, try unplugging and reconnecting them.

## Support

For support with the VU-Server software itself, please refer to the [official VU-Server documentation](https://github.com/SasaKaranovic/VU-Server).

For add-on specific issues, please report them in the [GitHub repository](https://github.com/leoherzog/home-assistant-vu1-server).