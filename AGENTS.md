# AGENTS.md

Guidance for coding agents working in this repository.

## Overview

A Home Assistant app that runs upstream [VU-Server](https://github.com/SasaKaranovic/VU-Server) for Streacom VU1 dials.

- `vu-server/`: upstream git submodule, for reference only.
- `vu-server-addon/`: the app.

**Do not modify** `vu-server/`. The upstream source must run unmodified; all wrapper behaviour lives in `vu-server-addon/`.

## Upstream pin

The Dockerfile fetches upstream by commit SHA. That SHA must equal the `vu-server` submodule gitlink (`git ls-tree HEAD vu-server`), and CI (`.github/workflows/main.yml`) checks this. To bump upstream, update the submodule and the Dockerfile ref together.

## Layout (`vu-server-addon/`)

| Path | Role |
|---|---|
| `Dockerfile` | Built on `ghcr.io/home-assistant/base`. Adds pinned upstream, a Python venv from wheels only, and nginx. Symlinks `config.yaml`, `vudials.db` and `upload/` into `/data/vu-server/`. `HEALTHCHECK` on `:5340/`. |
| `rootfs/etc/cont-init.d/vu-server.sh` | Runs once before services. Creates `/data/vu-server/upload`, restores `img_blank`, and copies upstream's default `config.yaml` if none exists. The Web UI hardcodes upstream's default master key, so the app never changes it. |
| `rootfs/etc/services.d/vu-server/run` | Runs `server.py --logging <log_level>`. Kills the server after 3 `[Errno 5]` lines, because upstream never reopens a failed serial port. |
| `rootfs/etc/services.d/vu-server/finish` | Lets s6 restart the server, sleeping 3 s after a non-signal exit, because upstream exits 0 on every failure. |
| `rootfs/etc/services.d/nginx/run` | Execs nginx. |
| `rootfs/etc/nginx/nginx.conf` | Ingress on 8099, only from `172.30.32.2`. Proxies to `127.0.0.1:5340` and rewrites root-absolute URLs with `sub_filter`. Access log is off because query strings carry keys. |
| `config.yaml` | `init: false`, `ingress`, `uart`, optional `5340/tcp` mapping, `log_level: list(debug\|info)` (upstream supports only these two), `stage: experimental` (the store shows an Experimental warning badge). |
| `apparmor.txt` | Broad file and network access (intentional), Docker's default deny rules, signal receive from `runc`/`crun` so stop delivers SIGTERM, and the capabilities nginx needs. |
| `translations/en.yaml`, `README.md`, `CHANGELOG.md` | Option labels, store page and changelog. |

Health: when `HEALTHCHECK` fails, Docker marks the container unhealthy; Supervisor restarts the app on that only if the user turns on the app's Watchdog toggle.

## Integration

The companion [home-assistant-vu1-devices](https://github.com/leoherzog/home-assistant-vu1-devices) integration discovers the app through Supervisor and connects to `<hostname>:5340` directly, not through ingress. The user supplies only an API key, created in the Web UI under **API Keys**.

## Lint and release

CI runs `frenck/action-app-linter` on `vu-server-addon`. To run it locally:

```bash
cd /tmp && git clone --depth 1 https://github.com/frenck/action-app-linter.git
cd action-app-linter/src
uv venv .venv && source .venv/bin/activate && uv pip install jsonschema pyyaml
cp *.schema.json /tmp/
sed 's|/config.schema.json|/tmp/config.schema.json|g' lint.py > lint_local.py
INPUT_PATH="/path/to/vu-server-addon" INPUT_COMMUNITY="false" python lint_local.py
```

`release.yml` runs when a GitHub release is published. It checks that the tag (without a leading `v`) equals `version:` in `config.yaml`, then builds amd64 and aarch64 with the `home-assistant/builder` actions and publishes `ghcr.io/leoherzog/vu-server-addon`. Update `CHANGELOG.md` with each version bump.
