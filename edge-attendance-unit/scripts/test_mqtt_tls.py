#!/usr/bin/env python3
"""
Script de test pour la connexion MQTT TLS
Teste la connexion sécurisée au broker MQTT
"""

import sys
import os
import ssl
import time
import json
from datetime import datetime

# Ajouter le répertoire parent au path pour importer config
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import paho.mqtt.client as mqtt
from config import config

def test_mqtt_tls():
    """Test de connexion MQTT avec TLS"""
    
    print("=== TEST DE CONNEXION MQTT TLS ===")
    print(f"Broker: {config.MQTT_BROKER}")
    print(f"Port: {config.MQTT_TLS_PORT if config.USE_TLS else config.MQTT_PORT}")
    print(f"TLS activé: {config.USE_TLS}")
    print(f"Utilisateur: {config.MQTT_USERNAME}")
    print()
    
    # Configuration du client MQTT
    client_id = f"test_tls_{int(time.time())}"
    client = mqtt.Client(client_id=client_id, protocol=mqtt.MQTTv5)
    
    # Variables de test
    connected = False
    connection_error = None
    
    # Callbacks
    def on_connect(client, userdata, flags, rc, properties=None):
        nonlocal connected
        if rc == mqtt.CONNACK_ACCEPTED:
            print("✅ Connexion MQTT réussie")
            connected = True
            
            # Test de publication
            test_topic = f"test/module_{config.MODULE_ID}"
            test_message = {
                "timestamp": datetime.now().isoformat(),
                "test": "TLS connection successful",
                "module_id": config.MODULE_ID
            }
            
            result = client.publish(test_topic, json.dumps(test_message), qos=1)
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                print(f"✅ Message de test publié sur {test_topic}")
            else:
                print(f"❌ Échec de publication: {result.rc}")
        else:
            print(f"❌ Échec de connexion MQTT, code: {rc}")
            connected = False
    
    def on_disconnect(client, userdata, rc, properties=None):
        print(f"🔌 Déconnecté du broker MQTT (code: {rc})")
    
    def on_publish(client, userdata, mid, properties=None):
        print(f"📤 Message publié (mid: {mid})")
    
    def on_log(client, userdata, level, buf):
        print(f"🔍 Log MQTT: {buf}")
    
    # Configuration des callbacks
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_publish = on_publish
    client.on_log = on_log
    
    # Configuration de l'authentification
    if config.MQTT_USERNAME and config.MQTT_PASSWORD:
        client.username_pw_set(config.MQTT_USERNAME, config.MQTT_PASSWORD)
        print(f"🔐 Authentification configurée pour {config.MQTT_USERNAME}")
    
    # Configuration TLS si activée
    if config.USE_TLS:
        try:
            context = ssl.create_default_context()
            
            # Certificat CA personnalisé
            if hasattr(config, 'MQTT_CA_CERT') and config.MQTT_CA_CERT and os.path.exists(config.MQTT_CA_CERT):
                context.load_verify_locations(cafile=config.MQTT_CA_CERT)
                print(f"🔐 Certificat CA chargé: {config.MQTT_CA_CERT}")
            
            # Mode insecure pour test
            if hasattr(config, 'MQTT_INSECURE_TLS') and config.MQTT_INSECURE_TLS:
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
                print("⚠️  Mode TLS insécurisé activé")
            
            # Certificats client (authentification mutuelle)
            if (hasattr(config, 'MQTT_CLIENT_CERT') and config.MQTT_CLIENT_CERT and 
                hasattr(config, 'MQTT_CLIENT_KEY') and config.MQTT_CLIENT_KEY and
                os.path.exists(config.MQTT_CLIENT_CERT) and os.path.exists(config.MQTT_CLIENT_KEY)):
                context.load_cert_chain(certfile=config.MQTT_CLIENT_CERT, keyfile=config.MQTT_CLIENT_KEY)
                print("🔐 Certificats client chargés")
            
            client.tls_set_context(context)
            print("🔐 Configuration TLS appliquée")
            
        except Exception as e:
            print(f"❌ Erreur de configuration TLS: {e}")
            return False
    
    # Tentative de connexion
    try:
        port = config.MQTT_TLS_PORT if config.USE_TLS else config.MQTT_PORT
        print(f"🔗 Tentative de connexion à {config.MQTT_BROKER}:{port}...")
        
        client.connect(config.MQTT_BROKER, port, keepalive=60)
        
        # Démarrer la boucle dans un thread séparé
        client.loop_start()
        
        # Attendre la connexion
        timeout = 10
        start_time = time.time()
        while not connected and (time.time() - start_time) < timeout:
            time.sleep(0.1)
        
        if connected:
            print("✅ Test de connexion réussi")
            
            # Laisser le temps pour les échanges
            time.sleep(2)
            
            client.disconnect()
            client.loop_stop()
            return True
        else:
            print("❌ Timeout de connexion")
            client.loop_stop()
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors de la connexion: {e}")
        client.loop_stop()
        return False

def main():
    """Fonction principale"""
    
    # Vérifier la configuration
    if not config.MQTT_BROKER:
        print("❌ MQTT_BROKER non configuré dans .env")
        return False
    
    if not config.MQTT_USERNAME or not config.MQTT_PASSWORD:
        print("❌ MQTT_USERNAME ou MQTT_PASSWORD non configuré dans .env")
        return False
    
    # Effectuer le test
    success = test_mqtt_tls()
    
    if success:
        print("\n🎉 Test TLS MQTT réussi!")
        return True
    else:
        print("\n💥 Test TLS MQTT échoué!")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
