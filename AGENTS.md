# AGENTS.md

This file provides guidance to Claude Code, Codex, Gemini, etc when working with code in this repository.

## Project Overview

This is a **Home Assistant Add-on** for the **VU-Server** that controls **Streacom VU1 Dynamic Analogue Dials** - physical USB-connected VU meters with eInk screens. The project has two main components:

1. **VU-Server Core** (`/vu-server/`) - Python Tornado server with REST API (Git submodule)
2. **Home Assistant Add-on** (`/vu-server-addon/`) - Docker container wrapper

**IMPORTANT**: The `/vu-server/` directory is a **Git submodule** pointing to the upstream VU-Server repository (`https://github.com/SasaKaranovic/VU-Server.git`). Do NOT modify files within this directory as they are managed by the upstream project. All Home Assistant add-on specific changes should be made in `/vu-server-addon/` only.

**Note**: The Dockerfile clones a pinned version (`v20240329`) directly from GitHub rather than using the local submodule. The submodule exists for development reference only.

## Development Commands

### Running VU-Server from Source
```bash
# Install dependencies (run once)
cd vu-server
pip3 install -r requirements.txt

# Start server
python3 server.py --logging info

# Start with debug logging
python3 server.py --logging debug
```

### Add-on Development
```bash
# Build Docker image (from vu-server-addon directory)
docker build -t vu-server-addon .

# Run add-on linter locally
cd /tmp && git clone --depth 1 https://github.com/frenck/action-addon-linter.git
cd action-addon-linter/src
uv venv .venv && source .venv/bin/activate && uv pip install jsonschema pyyaml
cp *.schema.json /tmp/
sed 's|/config.schema.json|/tmp/config.schema.json|g; s|/build.schema.json|/tmp/build.schema.json|g' lint.py > lint_local.py
INPUT_PATH="/path/to/vu-server-addon" INPUT_COMMUNITY="false" python3 lint_local.py
```

### Code Quality
```bash
# Run pylint (from vu-server directory)
pylint *.py dials/*.py

# Generate version info
python3 make_version.py
```

## Home Assistant Add-on (`/vu-server-addon/`)

### Configuration (`config.yaml`)

| Option | Value | Description |
|--------|-------|-------------|
| `homeassistant` | `"2024.4.0"` | Minimum HA version required |
| `udev` | `true` | Mounts host udev database for better USB detection |
| `ingress_stream` | `true` | Enables streaming for better API performance |
| `backup_exclude` | `["*.log", "upload/tmp_*"]` | Excludes logs and temp files from backups |
| `options`/`schema` | `log_level` | User-configurable: debug, info, warning, error |

### Key Files

- **`run.sh`** - Startup script
  - Reads user options via `bashio::config` (log_level)
  - Detects USB devices (`/dev/ttyACM*`, `/dev/ttyUSB*`)
  - Manages graceful shutdown with signal traps
- **`ingress_proxy.py`** - HTTP proxy for Home Assistant ingress
  - Multi-threaded `ThreadedTCPServer` for concurrent requests
  - 30-second timeout on upstream requests
  - URL rewriting for ingress compatibility
- **`Dockerfile`** - Multi-stage Alpine Linux build
  - Clones VU-Server at pinned version
  - Docker HEALTHCHECK on `/` endpoint (30s interval, 60s start period)

### Custom Integration Setup

This add-on does **not** use Supervisor auto-discovery. Users must manually configure the [home-assistant-vu1-devices](https://github.com/leoherzog/home-assistant-vu1-devices) integration with:

| Field | Value | Notes |
|-------|-------|-------|
| Host | Add-on container IP or `localhost` | Use container IP if integration runs on different host |
| Port | `5340` | Fixed, not configurable |
| API Key | From VU-Server Web UI | Open Web UI → Settings → API Keys |

**Finding your API key:**
1. Open the VU-Server Web UI (click "Open Web UI" in add-on panel)
2. Navigate to Settings → API Keys
3. Copy the master key or create a dedicated key for Home Assistant

## VU-Server Core (`/vu-server/` - Do Not Modify)

### Components

| File | Purpose |
|------|---------|
| `server.py` | Main Tornado web server (port 5340) with REST API |
| `dial_driver.py` | Low-level serial communication with VU1 hardware |
| `server_dial_handler.py` | High-level dial management and periodic updates |
| `server_config.py` | Configuration management (YAML + SQLite) |
| `database.py` | SQLite database for dials, API keys, settings |

### REST API (`/api/v0/`)

- **Dial Control**: `/dial/{uid}/set?value={0-100}`, `/dial/{uid}/setRaw?value={raw}`
- **Hardware**: `/dial/{uid}/backlight?red={}&green={}&blue={}`, `POST /dial/{uid}/image/set`
- **Administration**: `/dial/provision`, `/dial/{uid}/name?name={}`, `/dial/{uid}/calibrate?value={}`
- **API Keys**: `/admin/keys/list`, `POST /admin/keys/create`, `POST /admin/keys/update`

### Web Interface

- **Location**: `/vu-server/www/`
- **Framework**: Tabler dashboard template with jQuery
- **Entry Point**: `index.html`

### Authentication

- Master key system with configurable API keys
- Granular permissions per dial UID
- Health check endpoint `/` requires no authentication

## Hardware Requirements

- **Streacom VU1 Dynamic Analogue Dials** connected via USB
- **USB-to-serial drivers** for device communication
- **Linux permissions** for `/dev/ttyUSB*` or `/dev/ttyACM*` access

## Dependencies

- **tornado** - Web server framework
- **pyserial** - Serial communication
- **pillow** - Image processing for dial backgrounds
- **pyyaml/ruamel.yaml** - Configuration parsing
- **numpy** - Numerical operations
- **requests** - HTTP client library
