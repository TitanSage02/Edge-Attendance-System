# Deployment

The server runs with Docker Compose. The edge unit runs as a systemd service on Raspberry Pi OS.

## Server (Docker Compose)

The backend ships three compose files in `server/backend/`:

| File | Use |
|---|---|
| `docker-compose.dev.yml` | local development |
| `docker-compose.prod.yml` | production (reverse proxy, TLS) |
| `docker-compose.pi-server.yml` | running the server on a Raspberry Pi |

```bash
cd server/backend
cp .env.example .env            # fill in real values (see SECURITY.md)
docker compose -f docker-compose.dev.yml up --build
```

Services typically include:

- **backend** — FastAPI app (Uvicorn), port 8000
- **postgres** — PostgreSQL database (init scripts in `db-init/`)
- **mosquitto** — MQTT broker with TLS (`mosquitto/mosquitto-tls.conf`)
- **reverse proxy** — Nginx (`nginx/nginx.conf`) or Caddy (`Caddyfile`)

### Frontend

```bash
cd server/frontend
cp .env.example .env            # set VITE_API_URL to the deployed backend
npm install
npm run build                   # outputs to dist/ (gitignored)
```

Serve `dist/` behind your reverse proxy, or deploy via the included `vercel.json`.

## MQTT over TLS

The broker is configured for TLS in `server/backend/mosquitto/mosquitto-tls.conf`. On the edge unit, set in `.env`:

```
USE_TLS=true
MQTT_TLS_PORT=8883
MQTT_CA_CERT=/etc/ssl/certs/ca-certificates.crt
```

Generate/fetch the broker certificate with `edge-attendance-unit/scripts/setup_tls_certs.sh`. **Do not commit certificates** — they are gitignored.

## Edge unit (Raspberry Pi)

```bash
cd edge-attendance-unit
cp .env.example .env
./start.sh                      # installs system deps + Python venv
./install_service.sh            # installs the crec-presence systemd service
```

Manage the running unit:

```bash
./manage_service.sh status      # start | stop | restart | status | logs
```

> The systemd unit name `crec-presence.service` and MQTT topic prefix `crec/modules/*` are preserved to remain compatible with deployed devices.

## Remote access (optional)

A Cloudflare Tunnel token can be supplied via `CLOUDFLARE_TUNNEL_TOKEN` to expose the backend without opening inbound ports. Treat the token as a secret.

## Models

The InsightFace `buffalo_l` model is **not** shipped. It downloads automatically on first run (backend and edge unit both rely on this). Ensure the host has internet access for the initial download, then it is cached locally.
