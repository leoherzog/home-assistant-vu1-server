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
| `Dockerfile` | Built on `ghcr.io/home-assistant/base`. Adds pinned upstream, a Python venv from wheels only (upstream's pinned requirements minus `pyinstaller`), and nginx. Symlinks `config.yaml`, `vudials.db` and `upload/` into `/data/vu-server/`. `S6_KILL_GRACETIME=6000` because server.py gets SIGTERM only in s6's final kill-all and exits 3 s later; `S6_SERVICES_GRACETIME=1000` bounds a stop that lands in the finish throttle. `HEALTHCHECK` on `:5340/`. |
| `rootfs/etc/cont-init.d/vu-server.sh` | Runs before services on every start. Creates `/data/vu-server/upload`, restores `img_blank`, copies upstream's default `config.yaml` if none exists, and blanks `server.hostname` if it has a value. Upstream binds to that address, defaults it to `localhost`, and treats empty as all interfaces. The key must stay, or upstream falls back to its built-in defaults, including port 3000. The Web UI hardcodes upstream's default master key, so the app never changes it. |
| `rootfs/etc/services.d/vu-server/run` | Runs `server.py --logging <log_level>`. Redacts key values, because Tornado logs failed requests with their query strings. Kills the server after 3 `[Errno 5]` lines, because upstream never reopens a failed serial port. awk ignores SIGTERM so upstream's shutdown lines reach the log. |
| `rootfs/etc/services.d/vu-server/finish` | Lets s6 restart the server, sleeping 3 s after a non-signal exit, because upstream exits 0 on every failure. |
| `rootfs/etc/services.d/nginx/run` | Execs nginx. |
| `rootfs/etc/nginx/nginx.conf` | Ingress on 8099, only from `172.30.32.2`. Proxies to `127.0.0.1:5340` and rewrites root-absolute URLs with `sub_filter`. Also appends the master key to the dial page's `image/get` request, which upstream's Web UI sends without one. Access log is off because query strings carry keys. |
| `config.yaml` | `init: false`, `ingress`, `uart`, optional `5340/tcp` mapping, `log_level: list(debug\|info)` (upstream supports only these two), `stage: experimental` (the store shows an Experimental warning badge). |
| `apparmor.txt` | Broad file and network access (intentional), Docker's default deny rules, signal receive from `runc`/`crun` so stop delivers SIGTERM, and the capabilities nginx needs. |
| `translations/en.yaml`, `README.md`, `CHANGELOG.md` | Option labels, store page and changelog. |

Health: when `HEALTHCHECK` fails, Docker marks the container unhealthy; Supervisor restarts the app on that only if the user turns on the app's Watchdog toggle.

## Integration

The companion [home-assistant-vu1-devices](https://github.com/leoherzog/home-assistant-vu1-devices) integration discovers the app through Supervisor and connects to `<hostname>:5340` directly, not through ingress. That works only because cont-init blanks `server.hostname`; ingress and `HEALTHCHECK` use loopback and would not notice a loopback-only bind. The user supplies only an API key, created in the Web UI under **API Keys**.

## Lint and release

CI checks the upstream pin and runs `frenck/action-app-linter` on `vu-server-addon`. A smoke job builds the amd64 image and starts it with `.github/fake-hub.py`, a pty hub with no dials, as entrypoint. It checks that another container reaches `:5340`, that logged keys are redacted, and that every nginx `sub_filter` pattern still occurs in upstream's Web UI. To run the linter locally:

```bash
cd /tmp && git clone --depth 1 https://github.com/frenck/action-app-linter.git
cd action-app-linter/src
uv venv .venv && source .venv/bin/activate && uv pip install jsonschema pyyaml
cp *.schema.json /tmp/
sed 's|/config.schema.json|/tmp/config.schema.json|g' lint.py > lint_local.py
INPUT_PATH="/path/to/vu-server-addon" INPUT_COMMUNITY="false" python lint_local.py
```

`release.yml` runs when a GitHub release is published. It checks that the tag (without a leading `v`) equals `version:` in `config.yaml`, then builds amd64 and aarch64 with the `home-assistant/builder` actions and publishes `ghcr.io/leoherzog/vu-server-addon`. Update `CHANGELOG.md` with each version bump.
