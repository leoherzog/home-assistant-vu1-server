# VU-Server Home Assistant Add-On

This Home Assistant add-on runs the [`VU-Server`](https://github.com/SasaKaranovic/vu-server) server software to control Streacom [VU1 Dynamic Analogue Dials](https://vudials.com/). VU1 Dials are physical, USB-connected VU meters with eInk screens that can be controlled via API calls. This add-on provides the VU-Server API within your Home Assistant environment, but does not include a custom component for Home Assistant entities.

### Features

- 🔌 Runs VU-Server within Home Assistant as an add-on
- 🌐 Provides HTTP API for controlling VU1 dials
- ⚙️ Configurable API port
- 🔄 Auto-starts with Home Assistant

## Configuration

### Options

- `api_port` (integer): Port number for the VU-Server API (default: 5340)

### Example configuration:

```yaml
api_port: 5340
```

## Usage

1. Connect your VU1 dials via USB to your Home Assistant device
2. Install and start this add-on
3. The VU-Server API will be available at `http://hassio.local:5340`
4. Use the API or a compatible Home Assistant integration to control your dials

## Troubleshooting

- Ensure your VU1 Dials are properly connected via USB.
- Check the add-on logs for any error messages.
- If dials are not auto-discovered, try unplugging and reconnecting them.

## Support

For support with the VU-Server software itself, please refer to the [official VU-Server documentation](https://github.com/streacom/vu-server).

For add-on specific issues, please report them in the [GitHub repository](https://github.com/leoherzog/home-assistant-vu1-server).