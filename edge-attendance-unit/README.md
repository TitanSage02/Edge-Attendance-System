# Edge Attendance Unit (Raspberry Pi)

The on-device attendance unit. Runs on a Raspberry Pi 4, performs **face recognition + RFID** identification locally, works offline, and syncs presence events to the server over MQTT/TLS.

## Role

Sensor capture → on-device inference (InsightFace + ChromaDB) → local presence queue → MQTT publish when online. The unit keeps working during network outages and flushes buffered events on reconnect.

## Hardware

- Raspberry Pi 4 (4 GB RAM recommended)
- Pi Camera v2 (or compatible USB camera)
- MFRC522 RFID reader (SPI)
- VL53L0X time-of-flight distance sensor (I²C) — wakes the camera on approach
- Status LEDs (red/green/blue) + buzzer for feedback

## Setup

```bash
cd edge-attendance-unit
cp .env.example .env            # set BASE_URL, API_KEY, MQTT credentials
pip install -r requirements.txt
```

> On first run, InsightFace downloads the `buffalo_l` model automatically (internet required for the initial download only). Models are **not** committed to the repo.

For a full Raspberry Pi provisioning (system packages, venv, I²C/SPI), use the helper script:

```bash
./start.sh
```

## Run

```bash
python startup.py
```

Optional helpers:

- `python diagnostic.py` — check sensors/camera/RFID wiring
- `config_web/` — local Flask portal to configure the unit from a browser
- `crec-presence.service` — systemd unit for auto-start (install via `install_service.sh`)

## Tests

```bash
./run_tests.sh            # installs test deps then runs pytest
# or directly:
pytest tests/
```

Hardware-dependent libraries (RPi.GPIO, spidev, picamera2) are mocked in `tests/mocks/`, so the suite runs on a development machine without a Pi.

## Structure

```
edge-attendance-unit/
├── startup.py          # main entry point
├── config.py           # centralized configuration (reads .env)
├── data_manager.py     # local ChromaDB vector store
├── sensors/            # camera, RFID, VL53L0X distance, LED/buzzer feedback
├── auth/               # face + RFID authentication logic
├── communication/      # MQTT manager (TLS, offline buffering, reconnection)
├── utils/              # logging, persistence
├── config_web/         # local Flask configuration portal
├── scripts/            # TLS cert setup, MQTT test utilities
└── tests/              # pytest suite (hardware mocked)
```

## MQTT topics

| Topic | Direction | Purpose |
|---|---|---|
| `crec/modules/config_updates` | in | broadcast configuration updates |
| `crec/modules/{module_uid}/status` | out | module health/status |
| `crec/modules/{module_uid}/presence` | out | presence events |
| `crec/modules/{module_uid}/logs` | out | structured logs |
| `crec/modules/{module_uid}/command` | in | remote commands (restart, etc.) |

> These runtime topic names and the `crec-presence.service` identifier are kept as-is to preserve compatibility with deployed units.
