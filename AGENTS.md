# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **Home Assistant Add-on** for the **VU-Server** that controls **Streacom VU1 Dynamic Analogue Dials** - physical USB-connected VU meters with eInk screens. The project has two main components:

1. **VU-Server Core** (`/vu-server/`) - Python Tornado server with REST API (Git submodule)
2. **Home Assistant Add-on** (`/vu-server-addon/`) - Docker container wrapper

**IMPORTANT**: The `/vu-server/` directory is a **Git submodule** pointing to the upstream VU-Server repository (`https://github.com/SasaKaranovic/VU-Server.git`). Do NOT modify files within this directory as they are managed by the upstream project. All Home Assistant add-on specific changes should be made in `/vu-server-addon/` only.

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

### Code Quality
```bash
# Run pylint (from vu-server directory)
pylint *.py dials/*.py

# Generate version info
python3 make_version.py
```

### Add-on Development
```bash
# Build Docker image (from vu-server-addon directory)
docker build -t vu-server-addon .
```

## Architecture

### Core Components
- **`server.py`** - Main Tornado web server (port 5340) with REST API endpoints
- **`dial_driver.py`** - Low-level serial communication with VU1 hardware
- **`server_dial_handler.py`** - High-level dial management and periodic updates
- **`server_config.py`** - Configuration management (YAML + SQLite integration)
- **`database.py`** - SQLite database for dials, API keys, and settings

### Configuration
- **`config.yaml`** - Server settings (port, master key, hardware port)
- **SQLite database** - Persistent storage for dial configurations and API keys

### REST API Structure
All endpoints under `/api/v0/`:
- **Dial Control**: `/dial/{uid}/set?value={0-100}`, `/dial/{uid}/setRaw?value={raw}`
- **Hardware**: `/dial/{uid}/backlight?red={}&green={}&blue={}`, `POST /dial/{uid}/image/set`
- **Administration**: `/dial/provision`, `/dial/{uid}/name?name={}`, `/dial/{uid}/calibrate?value={}`
- **API Keys**: `/admin/keys/list`, `POST /admin/keys/create`, `POST /admin/keys/update`

### Web Interface
- **Location**: `/vu-server/www/`
- **Framework**: Tabler dashboard template with jQuery
- **Entry Point**: `index.html`
- **JavaScript APIs**: `vu1_api.js`, `vu1_gui_*.js` files

### Add-on Integration
- **`run.sh`** - Startup script with USB device detection
- **`ingress_proxy.py`** - HTTP proxy for Home Assistant ingress
- **Auto-discovery**: Scans `/dev/ttyACM*` and `/dev/ttyUSB*` for VU1 hardware
- **Recent fixes**: JS redirections, button/icon handling, jQuery loading order, event listener cleanup

## Key Patterns

### Serial Communication
- Hardware communication through pyserial over USB
- Device auto-detection in add-on startup script
- Custom protocol for VU1 hub communication

### API Authentication
- Master key system with configurable API keys
- Granular permissions per dial UID
- Key management through admin endpoints

### Configuration Management
- YAML base configuration overlaid with SQLite database
- Runtime dial discovery and provisioning
- Persistent dial naming and calibration settings

### Docker Integration
- Multi-stage Alpine Linux build
- Home Assistant ingress proxy for secure web UI access
- Optional external port mapping (port 5340)

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