######################################################
## Gestion centralisée de toutes les configurations ##
######################################################

import os
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

class Config:
    # Debug Configuration
    DEBUG = os.getenv('DEBUG_MODE', 'False').lower() in ['true', '1', 'yes']
    # Alias pour maintenir la compatibilité avec le code qui utilise DEBUG_MODE
    DEBUG_MODE = DEBUG
    
    # Délai minimal (en secondes) entre deux détections du même étudiant
    PRESENCE_COOLDOWN = int(os.getenv('PRESENCE_COOLDOWN', '300'))  # 5 minutes par défaut
    
    # API Configuration
    API_KEY = os.getenv('API_KEY')
    BASE_URL = os.getenv('BASE_URL')
    MODULE_ID = os.getenv('MODULE_ID')
    
    # Hardware Configuration
    DISTANCE_THRESHOLD_MM = float(os.getenv('DISTANCE_THRESHOLD_MM', '100'))
    SIMILARITY_THRESHOLD = float(os.getenv('SIMILARITY_THRESHOLD', '0.6'))
    
    # MQTT Configuration
    MQTT_BROKER = os.getenv('MQTT_BROKER')
    MQTT_PORT = int(os.getenv('MQTT_PORT', '1883'))
    MQTT_TLS_PORT = int(os.getenv('MQTT_TLS_PORT', '8883'))
    MQTT_WSS_PORT = int(os.getenv('MQTT_WSS_PORT', '443'))  # Port WebSocket sécurisé (Cloudflare)
    MQTT_USERNAME = os.getenv('MQTT_USERNAME')
    MQTT_PASSWORD = os.getenv('MQTT_PASSWORD')
    USE_TLS = os.getenv('USE_TLS', 'False').lower() in ['true', '1', 'yes']
    MQTT_USE_WEBSOCKETS = os.getenv('MQTT_USE_WEBSOCKETS', 'False').lower() in ['true', '1', 'yes']
    
    # Mode de connexion automatique (local/prod)
    MQTT_CONNECTION_MODE = os.getenv('MQTT_CONNECTION_MODE', 'auto')  # auto, local, prod
    
    # TLS/SSL Configuration for MQTT
    MQTT_CA_CERT = os.getenv('MQTT_CA_CERT')  # Certificat CA (Let's Encrypt)
    MQTT_CLIENT_CERT = os.getenv('MQTT_CLIENT_CERT')  # Certificat client (optionnel)
    MQTT_CLIENT_KEY = os.getenv('MQTT_CLIENT_KEY')  # Clé client (optionnel)
    MQTT_INSECURE_TLS = os.getenv('MQTT_INSECURE_TLS', 'False').lower() in ['true', '1', 'yes']

    # System Configuration
    MAX_FAILURES = int(os.getenv('MAX_FAILURES', '5'))

    # Pin Configuration
    RED_LED_PIN = int(os.getenv('RED_LED_PIN', '18'))
    GREEN_LED_PIN = int(os.getenv('GREEN_LED_PIN', '16'))
    BLUE_LED_PIN = int(os.getenv('BLUE_LED_PIN', '15'))
    BUZZER_PIN = int(os.getenv('BUZZER_PIN', '12'))

    # RFID Configuration
    RFID_PIN = int(os.getenv('RFID_PIN', '22'))  # Pin de reset pour le lecteur RFID

config = Config()

# Propriétés d'accès direct pour le MQTT Manager (compatibilité)
config.mqtt_ca_cert = config.MQTT_CA_CERT
config.mqtt_client_cert = config.MQTT_CLIENT_CERT  
config.mqtt_client_key = config.MQTT_CLIENT_KEY