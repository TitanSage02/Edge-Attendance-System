# Server — Backend (FastAPI)

REST + WebSocket API and MQTT service for the Edge Attendance System. Handles authentication, student/module management, presence ingestion, secure storage of face embeddings, and an optional RAG chatbot over system logs.

## Role

Receives presence events from edge units (via MQTT and REST), persists them to PostgreSQL, exposes a typed API to the dashboard, and streams real-time updates over WebSockets.

## Tech

Python 3.10 · FastAPI · SQLAlchemy/SQLModel · PostgreSQL · Pydantic · structlog · paho-mqtt / fastapi-mqtt · InsightFace · ChromaDB/FAISS · Google Generative AI (chatbot).

## Setup & run

### With Docker (recommended)

```bash
cd server/backend
cp .env.example .env            # fill in real values — see ../../docs/SECURITY.md
docker compose -f docker-compose.dev.yml up --build
```

### Without Docker

```bash
cd server/backend
cp .env.example .env
python -m venv venv && source venv/bin/activate    # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Tables are created automatically on startup. The initial admin account is seeded from the `FIRST_USER_*` variables in `.env`.

## API docs

Once running:

- Swagger UI — http://localhost:8000/docs
- ReDoc — http://localhost:8000/redoc

## Structure

```
server/backend/
├── app/
│   ├── api/v1/        # REST endpoints (auth, students, presence, modules, chat, ...)
│   ├── core/          # config, security, rate limiting, websocket manager
│   ├── db/            # session + init
│   ├── models/        # SQLAlchemy ORM models
│   ├── schemas/       # Pydantic schemas
│   ├── services/      # business logic (presence, mqtt, face recognition, chatbot, email)
│   └── utils/         # encryption (AES-256), hashing (bcrypt), sanitization
├── migrations/        # Alembic migrations
├── mosquitto/         # MQTT broker (TLS) image + config
├── nginx/ · Caddyfile # reverse proxy configs
└── docker-compose.*.yml
```

## Security highlights

- JWT auth with role-based access; bcrypt password hashing.
- **AES-256 encryption** of biometric embeddings at rest (`app/utils/encryption.py`).
- Rate limiting, CORS allow-list, strict Pydantic input validation.
- MQTT over TLS to edge units.

See [docs/SECURITY.md](../../docs/SECURITY.md) and [docs/DEPLOYMENT.md](../../docs/DEPLOYMENT.md).

## Notes on face recognition models

The InsightFace `buffalo_l` models are **not** committed (`app/services/face_recognition/models/` is gitignored). They are downloaded automatically on first use by `face_model.py` / InsightFace.
