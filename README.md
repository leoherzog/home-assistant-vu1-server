# VU-Server Home Assistant Add-On

## What is this?

This Home Assistant add-on runs the [`VU-Server`](https://github.com/SasaKaranovic/vu-server) server software to control Streacom [VU1 Dynamic Analogue Dials](https://vudials.com/). VU1 Dials are physical, USB-connected VU meters with eInk screens that can be controlled via API calls. This add-on provides the VU-Server API within your Home Assistant environment, but does not include a custom component for Home Assistant entities.

### Features

- 🔌 Runs VU-Server within Home Assistant as an add-on
- 🌐 Provides HTTP API for controlling VU1 dials via Home Assistant ingress
- 🔒 Secure ingress-only access by default
- 🔄 Auto-starts with Home Assistant

## Installation

### Add Repository to Home Assistant

1. In Home Assistant, navigate to **Supervisor** > **Add-on Store**
2. Click the three dots menu in the top right and select **Repositories**
3. Add this repository URL: `https://github.com/leoherzog/home-assistant-vu1-server`
4. Click **Add**

### Install the Add-on

1. Find "VU-Server" in your add-on store
2. Click **Install**
3. Start the add-on

### Configuration

Optional setting:
- `log_level`: debug | info | warning | error (default: info)

The VU-Server runs on a fixed internal port and is accessed through Home Assistant's ingress system.

## Usage

1. Once the add-on is running, **click "Open Web UI"** in the add-on interface to access the VU-Server web interface
2. The VU-Server API is available through Home Assistant's ingress proxy
3. The master key will be automatically generated and can be found in the add-on logs

### API Access

All API endpoints are available through Home Assistant's ingress system. When accessing the API programmatically, use relative URLs from within Home Assistant or the full ingress URL path.
Ingress request bodies are buffered and limited to ~16 MB; for larger uploads, use direct port mapping below.

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

## License

The MIT License (MIT)

Copyright © 2025 Leo Herzog

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

## About Me

<a href="https://herzog.tech/" target="_blank">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://herzog.tech/signature/link-light.svg.png">
    <source media="(prefers-color-scheme: light)" srcset="https://herzog.tech/signature/link.svg.png">
    <img src="https://herzog.tech/signature/link.svg.png" width="32px">
  </picture>
</a>
<a href="https://mastodon.social/@herzog" target="_blank">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://herzog.tech/signature/mastodon-light.svg.png">
    <source media="(prefers-color-scheme: light)" srcset="https://herzog.tech/signature/mastodon.svg.png">
    <img src="https://herzog.tech/signature/mastodon.svg.png" width="32px">
  </picture>
</a>
<a href="https://github.com/leoherzog" target="_blank">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://herzog.tech/signature/github-light.svg.png">
    <source media="(prefers-color-scheme: light)" srcset="https://herzog.tech/signature/github.svg.png">
    <img src="https://herzog.tech/signature/github.svg.png" width="32px">
  </picture>
</a>
<a href="https://keybase.io/leoherzog" target="_blank">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://herzog.tech/signature/keybase-light.svg.png">
    <source media="(prefers-color-scheme: light)" srcset="https://herzog.tech/signature/keybase.svg.png">
    <img src="https://herzog.tech/signature/keybase.svg.png" width="32px">
  </picture>
</a>
<a href="https://www.linkedin.com/in/leoherzog" target="_blank">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://herzog.tech/signature/linkedin-light.svg.png">
    <source media="(prefers-color-scheme: light)" srcset="https://herzog.tech/signature/linkedin.svg.png">
    <img src="https://herzog.tech/signature/linkedin.svg.png" width="32px">
  </picture>
</a>
<a href="https://hope.edu/directory/people/herzog-leo/" target="_blank">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://herzog.tech/signature/anchor-light.svg.png">
    <source media="(prefers-color-scheme: light)" srcset="https://herzog.tech/signature/anchor.svg.png">
    <img src="https://herzog.tech/signature/anchor.svg.png" width="32px">
  </picture>
</a>
<br />
<a href="https://herzog.tech/$" target="_blank">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://herzog.tech/signature/mug-tea-saucer-solid-light.svg.png">
    <source media="(prefers-color-scheme: light)" srcset="https://herzog.tech/signature/mug-tea-saucer-solid.svg.png">
    <img src="https://herzog.tech/signature/mug-tea-saucer-solid.svg.png" alt="Buy Me A Tea" width="32px">
  </picture>
  Found this helpful? Buy me a tea!
</a>
