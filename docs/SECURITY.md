# Security

This system processes **biometric data** and is designed privacy-first. This document describes the threat model, key management, and encryption.

## Threat model

| Asset | Threat | Mitigation |
|---|---|---|
| Face embeddings | Theft / re-identification | AES-256 encryption at rest; never sent to cloud; raw images deleted after enrollment |
| Presence data | Tampering / eavesdropping | MQTT over TLS; JWT-authenticated API |
| Admin accounts | Credential theft | bcrypt password hashing; JWT access/refresh with expiry; role-based access |
| Edge unit ↔ server link | MITM, replay | TLS transport; per-module API keys |
| API surface | DoS, injection, XSS | rate limiting, CORS allow-list, strict Pydantic validation, input sanitization |
| Secrets (`.env`) | Accidental commit | `.gitignore` excludes all `.env`; only `.env.example` is tracked |

### Out of scope / known gaps

- **No liveness detection** — the pipeline can be fooled by a printed photo or video; RFID two-factor reduces but does not remove this risk. Liveness detection is planned future work.
- Physical access to an edge unit (SD card extraction) is not fully mitigated; consider full-disk encryption for high-risk deployments.

## Key management

All secrets live in per-component `.env` files (never committed). Copy from `.env.example` and generate fresh values:

```bash
# JWT secrets (one per secret)
openssl rand -hex 32

# AES-256 encryption key (ENCRYPTION_KEY), base64-encoded 32 bytes
python -c "import secrets,base64;print(base64.b64encode(secrets.token_bytes(32)).decode())"
```

Required secrets per component:

- **server/backend/.env** — `POSTGRES_PASSWORD`, `JWT_ACCESS_SECRET`, `JWT_REFRESH_SECRET`, `ENCRYPTION_KEY`, `MQTT_PASSWORD`, `MQTT_DEVICES_PASSWORD`, `SMTP_PASSWORD`, `CHATBOT_API_KEY`, `CLOUDFLARE_TUNNEL_TOKEN`.
- **edge-attendance-unit/.env** — `API_KEY` (per-module), `MQTT_PASSWORD`.
- **server/frontend/.env** — no secrets (only public `VITE_*` config).

## Encryption

- **At rest:** biometric embeddings are encrypted with AES-256 (`server/backend/app/utils/encryption.py`). The key comes from `ENCRYPTION_KEY`.
- **In transit:** TLS for the API (via reverse proxy) and for MQTT (port 8883).
- **Passwords:** hashed with bcrypt (`passlib`), never stored in plaintext.

## Preventing secret leaks

Two layers guard against committing credentials:

- **Pre-commit hook** — [gitleaks](https://github.com/gitleaks/gitleaks) plus `detect-private-key` and a large-file guard, configured in `.pre-commit-config.yaml`. Enable locally:

  ```bash
  pip install pre-commit && pre-commit install
  pre-commit run --all-files
  ```

- **CI** — the `secret-scan` job runs gitleaks on every push/PR (`.github/workflows/ci.yml`).

## Reporting

This is an academic/portfolio project. If you find a security issue, please open an issue describing it (without including exploit details for live systems).

---

## Secret management & hygiene

As standard hygiene when open-sourcing this project, all development credentials were rotated. No secrets were ever committed to git history — the repository was initialized fresh, and `.gitignore` excludes every `.env` file (only `.env.example` is tracked). A gitleaks pre-commit hook and a CI secret-scan job guard against accidental credential commits going forward.
