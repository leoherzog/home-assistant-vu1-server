# AGENTS.md

This file provides guidance to Claude Code, Codex, Gemini, etc when working with code in this repository.

## Project Overview

This is a **Home Assistant Add-on** for the **VU-Server** that controls **Streacom VU1 Dynamic Analogue Dials** - physical USB-connected VU meters with eInk screens. The project has two main components:

1. **VU-Server Core** (`/vu-server/`) - Python Tornado server with REST API (Git submodule)
2. **Home Assistant Add-on** (`/vu-server-addon/`) - Docker container wrapper

**IMPORTANT**: The `/vu-server/` directory is a **Git submodule** pointing to the upstream VU-Server repository (`https://github.com/SasaKaranovic/VU-Server.git`). Do NOT modify files within this directory as they are managed by the upstream project. All Home Assistant add-on specific changes should be made in `/vu-server-addon/` only.

**Note**: The Dockerfile clones the upstream source by **immutable commit SHA** (`a2a7d2489bdc3059117c6c401e5e68d75577434d`, the commit behind upstream tag `v20240329`) directly from GitHub rather than using the local submodule. The submodule exists for development reference only.

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
sed 's|/config.schema.json|/tmp/config.schema.json|g' lint.py > lint_local.py
INPUT_PATH="/path/to/vu-server-addon" INPUT_COMMUNITY="false" python3 lint_local.py
```

> The add-on has no `build.json` (per-arch base tags are deprecated). The base
> image is selected via the `Dockerfile` `ARG BUILD_FROM` default, and CI builds
> use the composable `home-assistant/builder` actions (see `.github/workflows/release.yml`).

### Release / CI

`release.yml` runs on a published GitHub release. A `verify` job first asserts
the git tag (minus a leading `v`) equals the `version:` in `vu-server-addon/config.yaml`
and fails the release otherwise. The build then uses the composable
`home-assistant/builder` actions (`prepare-multi-arch-matrix`, `build-image`,
`publish-multi-arch-manifest`, all pinned to `@2026.03.2`) to build and push the
`amd64`/`aarch64` images and multi-arch manifest to GHCR.

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
| `version` | `"0.4.0"` | Add-on version (must match the git tag on release — enforced by CI) |
| `stage` | `experimental` | Deliberately experimental; the add-on is hidden in the store unless non-stable stages are enabled |
| `homeassistant` | `"2024.4.0"` | Minimum HA version required |
| `ingress` | `true` | Exposes the Web UI through the HA ingress proxy (port 8099 internally) |
| `ports` / `ports_description` | `"5340/tcp": null` | Optional host-port mapping for the VU-Server API (unmapped by default) |
| `uart` | `true` | Grants access to host UART/serial devices for the VU1 hub |
| `udev` | `true` | Mounts the host udev database for reliable USB-serial detection |
| `backup_exclude` | `["vu-server/upload/tmp_*"]` | Excludes temp upload files from backups (uploaded dial images **are** backed up) |
| `options` / `schema` | `log_level` | User-configurable: debug, info, warning, error |

There is no `usb`, `ingress_stream`, `ingress_entry`, or `watchdog` key — the
first three were removed, and `watchdog` is obsolete in the current add-on schema.
Health monitoring is done via the Docker `HEALTHCHECK` in the Dockerfile (curl
against the unauthenticated `/` endpoint).

### Key Files

- **`run.sh`** - Startup script
  - Reads user options via `bashio::config` (log_level)
  - **On first init only** (when `/data/vu-server/config.yaml` does not yet exist):
    copies the default config, then generates a **random master key**
    (`head -c 16 /dev/urandom | base64 | tr -d '=+/'`), writes it into
    `/data/vu-server/config.yaml` with `sed`, and logs it **once** via
    `bashio::log.info`. Existing installs are never re-keyed. If the `sed` write
    fails it logs an error and the server falls back to the upstream default key.
  - Does **not** pick a serial port by first-match — it leaves `hardware.port`
    empty so upstream's FTDI VID/PID (`0403:6015`) auto-detection (`find_gauge_hub()`)
    runs. It only lists visible `/dev/ttyACM*`/`/dev/ttyUSB*` devices for info, and
    clears a stale persisted `hardware.port` that points at a now-missing device.
  - Supervises VU-Server with a restart budget, an I/O-error monitor, and the
    ingress proxy; manages graceful shutdown with signal traps.
- **`finish.sh`** - s6-overlay v3 `finish` script
  - Runs when the `vu-server` service exits. By default s6 restarts a dying
    `run` forever; this records the real exit code and **halts the container**
    instead, handing control back to Supervisor's restart policy so a
    fatal exit doesn't crash-loop invisibly.
- **`ingress_proxy.py`** - HTTP proxy for Home Assistant ingress (Web UI only)
  - Multi-threaded `ThreadedTCPServer`, `HTTP/1.1` (keep-alive), 30-second
    upstream timeout
  - Accepts requests **only** from the Supervisor ingress gateway (`172.30.32.2`)
    and loopback; everything else gets `403`
  - Forwards backend non-2xx responses (JSON error bodies, 304s) and 3xx
    redirects verbatim, rewriting `Location` to stay inside the ingress mount
  - Rewrites HTML/JS URLs for ingress compatibility; responses are fully buffered
    (no streaming — this is why the `ingress_stream` option was removed)
- **`Dockerfile`** - Multi-stage Alpine build with `ARG BUILD_FROM=ghcr.io/home-assistant/base:3.23`
  (default lets a plain `docker build` work since Supervisor no longer injects
  `BUILD_FROM`)
  - Stage 1 clones upstream VU-Server by **immutable commit SHA** (`VU_SERVER_REF`)
  - Stage 2 builds the Python venv with the full toolchain (none lands in runtime)
  - Stage 3 is the slim runtime (python3 + curl); symlinks `config.yaml`,
    `vudials.db`, and `upload/` to `/data/vu-server/` so they persist across
    updates and are included in backups
  - Installs the s6 `run` + `finish` services, `EXPOSE 5340`, and a Docker
    `HEALTHCHECK` against the unauthenticated `/` endpoint (the add-on schema's
    `watchdog` key is obsolete; Supervisor consumes the native HEALTHCHECK).
- **`apparmor.txt`** - AppArmor profile for the add-on (serial/`/dev/tty*` access,
  network, s6 + `/data` + `/opt` paths).
- **`translations/en.yaml`** - Supervisor UI labels/descriptions for the
  `log_level` option.

### Custom Integration Setup

The companion [home-assistant-vu1-devices](https://github.com/leoherzog/home-assistant-vu1-devices)
integration **auto-discovers this add-on** via the Supervisor `/addons` API (it
matches the `vu-server-addon` slug, then reads the add-on's stable DNS
**hostname** and connects directly to `hostname:5340`). The integration's ingress
proxy is **not** used for the API — API clients bypass it. Only the **API key**
is entered manually.

| Field | Value | Notes |
|-------|-------|-------|
| Host/Port | Auto-discovered | DNS hostname + `5340`, filled in by the config flow; manual entry is the fallback when not running under Supervisor |
| API Key | Manual | The only field the user supplies |

**Where the API key comes from:**
1. Open the VU-Server Web UI (click "Open Web UI" on the add-on page).
2. Unlock with the **master key** (printed once in the add-on log on first start,
   and stored in `/data/vu-server/config.yaml`).
3. Go to Settings → API Keys and create/copy a key for Home Assistant. (The
   master key itself also works and is required for the `provision` admin endpoint.)

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
