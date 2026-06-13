"""
Configuration pour pytest
"""

import os
import sys
import pytest
from unittest.mock import MagicMock

# Ajouter le chemin du projet aux chemins de recherche
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ---------------------------------------------------------------------------
# Stub Raspberry-Pi-only and heavy native libraries so the suite collects and
# runs on a development machine / CI (no Pi hardware, no GPU). On a real Pi the
# genuine modules are imported instead — stubs only kick in when an import
# fails. Tests mock the relevant behavior, so the real libraries are not needed.
# ---------------------------------------------------------------------------
_OPTIONAL_HARDWARE_MODULES = [
    "board", "busio", "digitalio", "adafruit_vl53l0x",
    "spidev", "mfrc522", "RPi", "RPi.GPIO", "picamera2",
    "cv2", "insightface", "insightface.app",
    "chromadb", "PIL", "PIL.Image",
]
for _name in _OPTIONAL_HARDWARE_MODULES:
    try:
        __import__(_name)
    except Exception:
        _parts = _name.split(".")
        for _i in range(len(_parts)):
            _mod = ".".join(_parts[: _i + 1])
            sys.modules.setdefault(_mod, MagicMock())

# Configuration pour les tests
os.environ['PYTEST_CURRENT_TEST'] = "True"

@pytest.fixture(scope="session", autouse=True)
def setup_environment():
    """Configuration globale de l'environnement de test"""
    # Importer la configuration de test (selon le mode d'import pytest)
    try:
        from tests.mock_config import MODULE_ID
    except ModuleNotFoundError:
        from mock_config import MODULE_ID
    
    # Mock pour le module de configuration
    mock_config = MagicMock()
    mock_config.MODULE_ID = MODULE_ID
    mock_config.MQTT_BROKER = "localhost"
    mock_config.MQTT_PORT = 1883
    mock_config.MQTT_USERNAME = "test_user"
    mock_config.MQTT_PASSWORD = "test_password"
    mock_config.USE_TLS = False
    mock_config.mqtt_ca_cert = None
    mock_config.mqtt_client_cert = None
    mock_config.mqtt_client_key = None
    mock_config.BASE_URL = "http://localhost:8000"
    mock_config.API_KEY = "test_api_key"
    mock_config.SIMILARITY_THRESHOLD = 0.70
    
    # Injecter la configuration dans le système
    import types
    config_module = types.ModuleType('config')
    # Config object with necessary attributes
    class _Config:
        pass
    config_obj = _Config()
    config_obj.MODULE_ID = MODULE_ID
    config_obj.MQTT_BROKER = "localhost"
    config_obj.MQTT_PORT = 1883
    config_obj.MQTT_USERNAME = "test_user"
    config_obj.MQTT_PASSWORD = "test_password"
    config_obj.USE_TLS = False
    config_obj.mqtt_ca_cert = None
    config_obj.mqtt_client_cert = None
    config_obj.mqtt_client_key = None
    config_obj.BASE_URL = "http://localhost:8000"
    config_obj.API_KEY = "test_api_key"
    config_obj.SIMILARITY_THRESHOLD = 0.70
    # Assign config attribute so `from config import config` works
    config_module.config = config_obj
    sys.modules['config'] = config_module

    yield
    
    # Nettoyage après les tests
    if 'config' in sys.modules:
        del sys.modules['config']
