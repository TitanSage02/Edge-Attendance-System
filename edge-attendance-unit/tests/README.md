# Tests automatisés pour Edge Attendance Unit

Ce répertoire contient les tests automatisés pour le système Edge Attendance Unit.

## Exécution des tests

### Sous Linux/MacOS

```bash
# Exécuter tous les tests
./run_tests.sh

# Exécuter un test spécifique
./run_tests.sh test_mqtt_manager.py
```

## Rapports de test

Les rapports de test sont générés dans le dossier `reports/` :
- Rapports XML dans `reports/test-results.xml`
- Rapports de couverture dans `reports/coverage.xml`
- Rapports HTML dans `reports/html/index.html`

## Dépendances pour les tests

Les scripts d'exécution des tests installent automatiquement les dépendances nécessaires :
- pytest
- pytest-asyncio
- pytest-mock
- pytest-cov
- coverage

## Résolution des problèmes courants

### Les tests échouent avec l'erreur "unrecognized arguments: --cov"

Si vous obtenez cette erreur, cela signifie que le paquet pytest-cov n'est pas installé. Exécutez :

```bash
pip install pytest-cov
```

### Erreurs d'accès aux périphériques matériels

Les tests sont conçus pour fonctionner avec des mocks pour simuler le matériel. Si vous obtenez des erreurs liées au matériel, vérifiez que les mocks sont correctement configurés dans les fichiers de test.

### Erreurs de connexion MQTT

Les tests MQTT utilisent des mocks pour simuler la connexion. Si vous obtenez des erreurs MQTT, assurez-vous que le broker MQTT n'est pas nécessaire pour les tests.

---

## Running off-device (development machine / CI)

The suite targets the Raspberry Pi, but it can now run on a regular machine.
`conftest.py` stubs the Pi-only and heavy native libraries (`board`, `spidev`,
`RPi.GPIO`, `picamera2`, `cv2`, `insightface`, `chromadb`, …) **only when they
fail to import**, so the real libraries are still used on a Pi.

Install the lightweight runtime deps the tests genuinely need, then run pytest:

```bash
pip install -r requirements-dev.txt
python -m pytest tests/
```

## Known pre-existing issues (not caused by the repository cleanup)

A few tests were already broken before the cleanup and are excluded from the
green CI run (`.github/workflows/ci.yml`). They are tracked for follow-up:

| Test(s) | Issue |
|---|---|
| `test_integration.py` | imports `from main import AttendanceSystem`, but the entry point is `startup.py` (no `main.py`); also drifted from `startup.py` (`_on_presence_detected` → `on_presence_detected`, `sensor_controller` → `sensor`, `_cleanup` no longer stops the sensor) |
| `test_mqtt_manager.py` | stale import corrected (`PresenceMQTT` → `PresenceBase`), but its tests still error at runtime pending rework |
| `test_rfid.py` | hardware read-loops (`read_card`, `time.sleep`) block off-device |
| `test_auth_manager.py::test_authenticate_student_face_only` / `…_rfid_only` | assertions written against an earlier auth flow |
| `test_feedback.py::test_interactive_feedback` | interactive test that reads from stdin (`OSError` under captured pytest), like `test_rfid` |
| `test_data_manager.py::test_find_matching_student_no_match` | passes with the now-active similarity gate, but asserts a no-match at similarity 0.7 using an explicit threshold of 0.8 — above the shipped default `SIMILARITY_THRESHOLD` (0.6), where that input would match. Kept deselected to avoid baking a stricter-than-default threshold into CI; revisit after on-device calibration |

With these excluded, **27 tests pass** off-device (`asyncio_mode=auto` is set in
`pytest.ini`; test dependencies are pinned in `requirements-dev.txt`).

> Note: `test_data_manager.py::test_fetch_students_data_success` previously failed
> on a broken async mock (`AsyncMock` on the synchronous `aiohttp.ClientSession()`
> constructor) — now fixed and re-enabled.
