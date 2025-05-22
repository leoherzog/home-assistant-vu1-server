# VU-Server Home Assistant Add-On

Runs the Streacom VU1 Server within Home Assistant to control VU1 analogue dials.

## About

This add-on packages the VU-Server software as a Home Assistant add-on, allowing you to control VU1 Dynamic Analogue Dials from within your Home Assistant environment.

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

## Support

For support with the VU-Server software itself, please refer to the [official VU-Server documentation](https://github.com/streacom/vu-server).

For add-on specific issues, please report them in the [GitHub repository](https://github.com/leoherzog/home-assistant-vu1-server).