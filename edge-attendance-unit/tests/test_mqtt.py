#!/usr/bin/env python3
"""
Test de connectivité MQTT pour Edge Attendance Unit
Ce script permet de tester la connexion au broker MQTT, la publication et la souscription à des topics

Usage:
    python test_mqtt.py [--publish] [--subscribe] [--topic TOPIC] [--message MESSAGE] [--verbose]

Options:
    --publish       Tester la publication de messages
    --subscribe     Tester la souscription à des topics
    --topic TOPIC   Spécifier un topic custom (défaut: crec/test)
    --message MSG   Spécifier un message custom (défaut: message de test avec timestamp)
    --verbose       Afficher des informations détaillées
"""

import sys
import os
import time
import json
import logging
import argparse
import signal
from datetime import datetime
import ssl
from typing import Dict, Any, Optional

# Ajouter le répertoire parent au path pour importer les modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import paho.mqtt.client as mqtt
from config import config

# Importer notre logger standard
from utils.logger import setup_logger

# Configuration du logging adaptée
def setup_logging(verbose=False):
    level = logging.DEBUG if verbose else logging.INFO
    logger = setup_logger("mqtt_test", level)
    return logger


class MQTTTester:
    """Classe pour tester la connectivité MQTT"""
    
    def __init__(self, broker=None, port=None, username=None, password=None, use_tls=False, module_id=None):
        """Initialisation avec les paramètres de connexion"""
        self.logger = logging.getLogger("mqtt_tester")
        
        # Utiliser les paramètres fournis ou ceux de la config
        self.broker = broker or config.MQTT_BROKER
        self.port = port or config.MQTT_PORT
        self.username = username or config.MQTT_USERNAME
        self.password = password or config.MQTT_PASSWORD
        self.use_tls = use_tls or (hasattr(config, 'USE_TLS') and config.USE_TLS)
        self.module_id = module_id or config.MODULE_ID
        
        # Créer le client MQTT avec un ID unique basé sur le module_id
        self.client_id = f"crec-module-{self.module_id}-test-{int(time.time())}"
        # Utiliser MQTTv3.1.1 qui est plus largement supporté que MQTTv5
        self.client = mqtt.Client(client_id=self.client_id)
        
        # Variables d'état
        self.connected = False
        self.messages_received = []
        self.connection_rc = None
        
        # Configuration des callbacks
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message
        self.client.on_publish = self._on_publish
        self.client.on_subscribe = self._on_subscribe
        
    def _on_connect(self, client, userdata, flags, rc):
        """Callback appelé lors de la connexion au broker"""
        self.connection_rc = rc
        
        if rc == 0:
            self.connected = True
            self.logger.info(f"✅ Connexion réussie au broker MQTT {self.broker}:{self.port}")
        else:
            self.connected = False
            self.logger.error(f"❌ Échec de connexion au broker MQTT, code retour: {rc}")
            
            # Afficher les erreurs courantes pour aider au diagnostic
            error_messages = {
                1: "Version de protocole incorrecte",
                2: "Identifiant client rejeté",
                3: "Serveur indisponible",
                4: "Nom d'utilisateur ou mot de passe incorrect",
                5: "Non autorisé à se connecter"
            }
            
            if rc in error_messages:
                self.logger.error(f"  Cause probable: {error_messages[rc]}")
    
    def _on_disconnect(self, client, userdata, rc):
        """Callback appelé lors de la déconnexion du broker"""
        self.connected = False
        
        if rc == 0:
            self.logger.info("Déconnexion propre du broker MQTT")
        else:
            self.logger.warning(f"Déconnexion inattendue du broker MQTT, code: {rc}")
    
    def _on_message(self, client, userdata, msg):
        """Callback appelé lors de la réception d'un message"""
        try:
            # Tenter de décoder en JSON
            try:
                payload = json.loads(msg.payload.decode('utf-8'))
                payload_str = json.dumps(payload, indent=2)
            except:
                payload_str = msg.payload.decode('utf-8')
                
            self.logger.info(f"Message reçu sur le topic {msg.topic}:")
            self.logger.info(f"  {payload_str}")
            
            # Stocker le message reçu
            self.messages_received.append({
                'topic': msg.topic,
                'payload': msg.payload.decode('utf-8'),
                'time': datetime.now().isoformat()
            })
            
        except Exception as e:
            self.logger.error(f"Erreur lors du traitement du message: {e}")
    
    def _on_publish(self, client, userdata, mid):
        """Callback appelé après la publication d'un message"""
        self.logger.debug(f"Message publié avec succès (ID: {mid})")
    
    def _on_subscribe(self, client, userdata, mid, granted_qos):
        """Callback appelé après la souscription à un topic"""
        self.logger.info(f"Souscription réussie (QoS: {granted_qos})")
    
    def connect(self):
        """Connecter au broker MQTT"""
        try:
            self.logger.info(f"Tentative de connexion au broker MQTT {self.broker}:{self.port}...")
            
            # Configuration de l'authentification si nécessaire
            if self.username and self.password:
                self.logger.debug(f"Utilisation de l'authentification avec l'utilisateur '{self.username}'")
                self.client.username_pw_set(self.username, self.password)
            
            # Configuration TLS si activée
            if self.use_tls:
                self.logger.debug("Activation de TLS pour la connexion")
                self.client.tls_set(cert_reqs=ssl.CERT_REQUIRED)
                self.client.tls_insecure_set(False)
            
            # Connexion au broker
            self.client.connect(self.broker, self.port, keepalive=60)
            
            # Démarrer la boucle de traitement des messages
            self.client.loop_start()
            
            # Attendre que la connexion soit établie
            timeout = 10  # Timeout en secondes
            start_time = time.time()
            
            while not self.connected and (time.time() - start_time) < timeout:
                time.sleep(0.1)
            
            if not self.connected:
                self.logger.error("Timeout atteint lors de la connexion au broker MQTT")
                return False
                
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la connexion au broker MQTT: {e}")
            return False
    
    def disconnect(self):
        """Se déconnecter proprement du broker"""
        if self.client:
            self.logger.info("Déconnexion du broker MQTT...")
            self.client.loop_stop()
            self.client.disconnect()
    
    def publish_message(self, topic, message, qos=1, retain=False):
        """Publier un message sur un topic"""
        if not self.connected:
            self.logger.error("Impossible de publier: non connecté au broker")
            return False
        
        try:
            # Convertir en JSON si c'est un dictionnaire
            if isinstance(message, dict):
                payload = json.dumps(message)
            else:
                payload = str(message)
                
            self.logger.info(f"Publication sur le topic '{topic}':")
            self.logger.info(f"  {payload}")
            
            result = self.client.publish(topic, payload, qos=qos, retain=retain)
            
            # Vérifier si la publication a réussi
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                self.logger.info("✅ Message publié avec succès")
                return True
            else:
                self.logger.error(f"❌ Échec de la publication, code: {result.rc}")
                return False
                
        except Exception as e:
            self.logger.error(f"Erreur lors de la publication: {e}")
            return False
    
    def subscribe(self, topic, qos=1):
        """S'abonner à un topic"""
        if not self.connected:
            self.logger.error("Impossible de s'abonner: non connecté au broker")
            return False
            
        try:
            self.logger.info(f"Abonnement au topic '{topic}'...")
            result = self.client.subscribe(topic, qos)
            
            if result[0] == mqtt.MQTT_ERR_SUCCESS:
                self.logger.info(f"✅ Abonnement réussi au topic '{topic}'")
                return True
            else:
                self.logger.error(f"❌ Échec de l'abonnement, code: {result[0]}")
                return False
                
        except Exception as e:
            self.logger.error(f"Erreur lors de l'abonnement: {e}")
            return False
    
    def run_connectivity_test(self, publish=True, subscribe=True, topic=None, message=None):
        """Exécuter un test complet de connectivité"""
        test_topic = topic or ""
        test_message = message or {
            "type": "connectivity_test",
            "module_id": self.module_id,
            "timestamp": datetime.now().isoformat(),
            "test_id": int(time.time())
        }
        
        success = self.connect()
        if not success:
            return False
            
        overall_success = True
        
        # Test de publication
        if publish:
            pub_success = self.publish_message(test_topic, test_message)
            if not pub_success:
                overall_success = False
        
        # Test d'abonnement et réception
        if subscribe:
            sub_success = self.subscribe(test_topic + "/#")
            if not sub_success:
                overall_success = False
                
            # Publier un message sur le topic souscrit
            if sub_success and publish:
                time.sleep(1)  # Attendre que la souscription soit active
                test_message["echo"] = True
                self.publish_message(test_topic + "/echo", test_message)
                self.logger.info(f"Message publié sur {test_topic + '/echo'}: {test_message}")
                # Attendre un peu pour recevoir le message
                time.sleep(2)
                
                if not self.messages_received:
                    self.logger.warning("⚠️ Aucun message reçu après abonnement")
        
        return overall_success
        
    def __del__(self):
        """Destructeur pour assurer une déconnexion propre"""
        try:
            self.disconnect()
        except:
            pass
            
    def diagnose_connection_issues(self, broker, port):
        """Fonction pour diagnostiquer les problèmes courants de connexion MQTT"""
        logger = logging.getLogger("mqtt_diagnosis")
        
        import socket
        import subprocess
        import platform
        
        logger.info("\n=== Diagnostic de connexion MQTT ===")
        
        # 1. Vérifier si l'adresse du broker est résoluble
        logger.info(f"1. Résolution de l'adresse du broker: {broker}")
        try:
            ip_address = socket.gethostbyname(broker)
            logger.info(f"   ✅ Résolution réussie: {broker} -> {ip_address}")
        except socket.gaierror:
            logger.error(f"   ❌ Impossible de résoudre l'adresse: {broker}")
            logger.error("   → Vérifiez que le nom d'hôte est correct ou utilisez une adresse IP directe")
            
        # 2. Vérifier la connectivité réseau avec ping
        logger.info(f"\n2. Test de connectivité réseau vers {broker}")
        
        ping_param = "-n" if platform.system().lower() == "windows" else "-c"
        try:
            ping_result = subprocess.run(
                ["ping", ping_param, "2", broker], 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                text=True,
                timeout=5
            )
            
            if ping_result.returncode == 0:
                logger.info(f"   ✅ Le broker répond au ping")
            else:
                logger.warning(f"   ⚠️ Le broker ne répond pas au ping (code: {ping_result.returncode})")
                logger.warning("   → Le broker pourrait bloquer les requêtes ICMP ou être injoignable")
        except Exception as e:
            logger.error(f"   ❌ Erreur lors du test ping: {e}")
        
        # 3. Tester si le port est accessible
        logger.info(f"\n3. Test d'accessibilité du port {port} sur {broker}")
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5)
        try:
            result = s.connect_ex((broker, port))
            if result == 0:
                logger.info(f"   ✅ Le port {port} est accessible")
            else:
                logger.error(f"   ❌ Le port {port} n'est pas accessible (code: {result})")
                logger.error("   → Vérifiez que le port est correct et n'est pas bloqué par un pare-feu")
        except Exception as e:
            logger.error(f"   ❌ Erreur lors du test de port: {e}")
        finally:
            s.close()
        
        # 4. Vérifier la configuration TLS
        logger.info("\n4. Vérification de la configuration TLS")
        if hasattr(config, 'USE_TLS') and config.USE_TLS:
            logger.info("   ⚠️ TLS est activé - Assurez-vous que les certificats sont correctement configurés")
            logger.info("   → Pour tester sans TLS, définissez USE_TLS=False dans le fichier .env")
        else:
            logger.info("   ✅ TLS est désactivé")
        
        logger.info("\n=== Fin du diagnostic ===\n")


def main():
    """Point d'entrée du script de test"""
    # Analyse des arguments de la ligne de commande
    parser = argparse.ArgumentParser(description="Test de connectivité MQTT pour Edge Attendance System")
    parser.add_argument("--publish", action="store_true", help="Tester la publication de messages")
    parser.add_argument("--subscribe", action="store_true", help="Tester la souscription à des topics")
    parser.add_argument("--topic", help="Topic MQTT à utiliser pour le test")
    parser.add_argument("--message", help="Message à publier")
    parser.add_argument("--verbose", action="store_true", help="Mode verbeux")
    
    args = parser.parse_args()
    
    # Configuration du logger
    logger = setup_logging(args.verbose)
    
    # Par défaut, faire les deux tests si aucun n'est spécifié
    if not args.publish and not args.subscribe:
        args.publish = True
        args.subscribe = True
    
    # Affichage des informations de configuration
    logger.info("=== Test de connectivité MQTT pour Edge Attendance System ===")
    logger.info(f"Broker: {config.MQTT_BROKER}:{config.MQTT_PORT}")
    logger.info(f"Module ID: {config.MODULE_ID}")
    logger.info(f"Authentification: {'Activée' if config.MQTT_USERNAME else 'Désactivée'}")
    
    
    # Gestion du signal d'interruption
    running = True
    def signal_handler(sig, frame):
        nonlocal running
        logger.info("Arrêt du test en cours...")
        running = False
    
    signal.signal(signal.SIGINT, signal_handler)
    
    # Créer le testeur MQTT
    tester = MQTTTester()

    # Exécuter les diagnostics réseau avant de tenter la connexion
    tester.diagnose_connection_issues(config.MQTT_BROKER, config.MQTT_PORT)
    
    try:
        # Exécuter le test
        success = tester.run_connectivity_test(
            publish=args.publish, 
            subscribe=args.subscribe,
            topic=args.topic,
            message=args.message
        )
        
        # Si souscription active, attendre l'interruption utilisateur
        if args.subscribe and success:
            logger.info("Écoute des messages en cours. Appuyez sur CTRL+C pour terminer...")
            while running:
                time.sleep(0.1)
    
    except Exception as e:
        logger.error(f"Erreur lors du test MQTT: {e}", exc_info=True)
        return 1
    finally:
        # Nettoyage
        tester.disconnect()
    
    # Afficher le résultat global
    if success:
        logger.info("\n✅ Test de connectivité MQTT réussi!")
    else:
        logger.error("\n❌ Test de connectivité MQTT échoué")
        return 1
        
    return 0

if __name__ == "__main__":
    sys.exit(main())
