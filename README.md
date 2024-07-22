# VU1 Dynamic Analogue Dial

## What is this?

This Home Assistant add-on allows you to integrate [VU1 Dynamic Analogue Dials](https://vudials.com/) into your smart home setup. VU1 Dials are physical, USB-connected VU meters with eInk screens that can display various sensor data from your Home Assistant instance. This add-on handles the communication between Home Assistant and the VU1 Dials, making it easy to visualize your data.

### Features

- 🔌 Auto-discovers VU1 Dials connected via USB
- 📊 Creates devices and entities in Home Assistant for each connected dial
- 🔢 Allows setting min/max values for each dial
- 🔄 Automatically updates dial positions based on linked sensor values

## Installation

### HACS Installation

1. Ensure you have [HACS](https://hacs.xyz/) installed in your Home Assistant instance.
2. In the HACS panel, click on "Integrations".
3. Click the "+" button in the bottom right corner.
4. Search for "VU1 Dynamic Analogue Dial" and select it.
5. Click "Install" and wait for the process to complete.
6. Restart Home Assistant.

### Configuration

After installation:

1. Go to "Configuration" > "Integrations" in Home Assistant.
2. Click the "+" button to add a new integration.
3. Search for "VU1 Dynamic Analogue Dial" and select it.
4. Follow the prompts to complete the setup.

## Usage

Once installed and configured:

1. The add-on will automatically discover any connected VU1 Dials.
2. Each dial will appear as a device in Home Assistant.
3. For each dial, you can:
   - Set a minimum and maximum value
   - Link it to any numeric sensor in your Home Assistant instance
   - The dial will automatically update to reflect the current sensor value

## Troubleshooting

- Ensure your VU1 Dials are properly connected via USB.
- Check the add-on logs for any error messages.
- If dials are not auto-discovered, try unplugging and reconnecting them.

## License

The MIT License (MIT)

Copyright © 2024 Leo Herzog

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
