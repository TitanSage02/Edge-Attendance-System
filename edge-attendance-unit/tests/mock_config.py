"""
Configuration fictive pour les tests
"""
import os

# Identifiants du module
MODULE_ID = 1
MODULE_NAME = "Test Module"

# Configuration MQTT
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_USERNAME = "test_user"
MQTT_PASSWORD = "test_password"
USE_TLS = False
mqtt_ca_cert = None
mqtt_client_cert = None
mqtt_client_key = None

# Configuration API
BASE_URL = "http://localhost:8000"
API_KEY = "test_api_key"

# Configuration de la caméra
CAMERA_INDEX = 0
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480
CAMERA_FPS = 30

# Seuils de reconnaissance
SIMILARITY_THRESHOLD = 0.70
DISTANCE_THRESHOLD_MM = 300

# Mode de fonctionnement
DEBUG = True
