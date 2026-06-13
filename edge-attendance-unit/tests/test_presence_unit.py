#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script de test d'intégration pour le module Edge Attendance System
Ce script teste le système d'authentification complet avec tous les capteurs
"""

import os
import sys
import time
import asyncio
import logging
import argparse
from datetime import datetime
from typing import Dict, Optional, List, Any

# Ajouter le répertoire parent au path pour importer les modules du projet
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.logger import setup_logger
from config import config

# Importer les contrôleurs
from sensors.sensor import VL065XController
from sensors.camera import CameraController
from sensors.rfid import RFIDController
from sensors.feedback import FeedbackController
from auth.auth_manager import AuthenticationManager, AuthenticationResult
from data_manager import DataManager
from communication.mqtt_manager import MQTTManager

# Configuration du logger
logger = setup_logger("integration_test", logging.INFO)

class PresenceUnitTest:
    """
    Classe de test d'intégration pour le module Edge Attendance System
    Teste le flux complet d'authentification et d'enregistrement de présence
    """
    
    def __init__(self):
        """Initialisation des composants du système"""
        self.data_manager = None
        self.camera_controller = None
        self.rfid_controller = None
        self.sensor_controller = None
        self.feedback_controller = None
        self.auth_manager = None
        self.mqtt_manager = None
        
    async def initialize(self):
        """Initialisation de tous les composants du système"""
        logger.info("Initialisation du système de test...")
        
        try:
            # Initialiser le gestionnaire de données
            self.data_manager = DataManager()
            
            # Initialiser les contrôleurs de capteurs
            self.sensor_controller = VL065XController(
                threshold=config.DISTANCE_THRESHOLD_MM
            )
            
            self.camera_controller = CameraController()
            
            self.rfid_controller = RFIDController()
            
            # Initialiser le contrôleur de feedback
            self.feedback_controller = FeedbackController()
            
            # Initialiser le gestionnaire d'authentification
            self.auth_manager = AuthenticationManager(
                self.data_manager,
                self.camera_controller,
                self.rfid_controller
            )
            
            # Initialiser le gestionnaire MQTT
            self.mqtt_manager = MQTTManager()
            await self.mqtt_manager.connect()
            
            # Récupérer les données des étudiants
            await self.data_manager.fetch_students_data()
            
            logger.info("✅ Système initialisé avec succès")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de l'initialisation du système: {e}")
            return False
    
    async def test_presence_detection(self, duration=30):
        """
        Test de détection de présence avec le capteur de distance
        
        Args:
            duration: Durée du test en secondes
        """
        logger.info("=== TEST DE DÉTECTION DE PRÉSENCE ===")
        
        # Créer un événement pour signaler une présence détectée
        presence_detected = asyncio.Event()
        
        # Définir le callback pour le capteur de distance
        async def on_presence_detected():
            logger.info("👤 Présence détectée!")
            presence_detected.set()
        
        # Configurer le callback et démarrer la surveillance
        await self.sensor_controller.start_monitoring(callback=on_presence_detected)
        
        logger.info(f"Test de détection pendant {duration} secondes...")
        logger.info("Approchez-vous du capteur pour déclencher une détection.")
        
        try:
            # Attendre qu'une présence soit détectée ou que le timeout soit atteint
            await asyncio.wait_for(presence_detected.wait(), timeout=duration)
            logger.info("✅ Détection de présence réussie!")
            return True
        except asyncio.TimeoutError:
            logger.warning("❌ Aucune présence détectée pendant la période d'attente")
            return False
        finally:
            # Arrêter la surveillance
            await self.sensor_controller.stop_monitoring()
    
    async def test_authentication(self, duration=30):
        """
        Test d'authentification complète (faciale + RFID)
        
        Args:
            duration: Durée maximale du test en secondes
        """
        logger.info("=== TEST D'AUTHENTIFICATION ===")
        logger.info(f"Test d'authentification pendant {duration} secondes...")
        logger.info("Présentez votre visage à la caméra et/ou votre carte RFID au lecteur.")
        
        try:
            # Définir un timeout pour l'authentification
            start_time = time.time()
            authentication_successful = False
            
            # Boucle d'authentification jusqu'à succès ou timeout
            while time.time() - start_time < duration and not authentication_successful:
                # Tentative d'authentification
                auth_result = await self.auth_manager.authenticate_student()
                
                if auth_result.success:
                    logger.info(f"✅ Authentification réussie pour l'étudiant {auth_result.student_id}")
                    logger.info(f"Méthode: {auth_result.method}")
                    
                    # Feedback de succès
                    await self.feedback_controller.indicate_success()
                    
                    # Enregistrer la présence via MQTT
                    presence_data = {
                        "student_id": auth_result.student_id,
                        "module_id": config.MODULE_ID,
                        "timestamp": datetime.now().isoformat(),
                        "auth_method": auth_result.method
                    }
                    
                    await self.mqtt_manager.publish_presence(presence_data)
                    logger.info("✅ Présence publiée via MQTT")
                    
                    authentication_successful = True
                    break
                else:
                    logger.warning(f"❌ Échec d'authentification: {auth_result.error}")
                    await self.feedback_controller.indicate_failure()
                    
                # Petite pause avant la prochaine tentative
                await asyncio.sleep(2)
            
            if not authentication_successful:
                logger.warning("❌ Aucune authentification réussie pendant la période d'attente")
            
            return authentication_successful
            
        except Exception as e:
            logger.error(f"❌ Erreur lors du test d'authentification: {e}")
            await self.feedback_controller.indicate_failure()
            return False
    
    async def test_mqtt_connectivity(self):
        """Test de la connectivité MQTT avec le backend"""
        logger.info("=== TEST DE CONNECTIVITÉ MQTT ===")
        
        if not self.mqtt_manager or not self.mqtt_manager.connected.is_set():
            logger.info("Connexion au broker MQTT...")
            self.mqtt_manager = MQTTManager()
            await self.mqtt_manager.connect()
            
        if self.mqtt_manager.connected.is_set():
            logger.info(f"✅ Connexion MQTT établie avec le broker {self.mqtt_manager.broker}")
            
            # Publier un message de test
            test_data = {
                "timestamp": datetime.now().isoformat(),
                "type": "test_message",
                "module_id": config.MODULE_ID
            }
            
            # Publish sur le topic de logs
            topic = f"crec/modules/{config.MODULE_ID}/logs"
            success = await self.mqtt_manager.publish(topic, test_data)
            
            if success:
                logger.info(f"✅ Message de test publié sur {topic}")
                return True
            else:
                logger.error("❌ Échec de la publication du message de test")
                return False
        else:
            logger.error(f"❌ Impossible de se connecter au broker MQTT {self.mqtt_manager.broker}")
            return False
    
    async def run_all_tests(self):
        """Exécute tous les tests d'intégration dans l'ordre"""
        logger.info("=== DÉMARRAGE DES TESTS D'INTÉGRATION ===")
        
        # Initialiser le système
        if not await self.initialize():
            logger.error("❌ Échec de l'initialisation, tests annulés")
            return False
            
        # Test de connectivité MQTT
        mqtt_ok = await self.test_mqtt_connectivity()
        if not mqtt_ok:
            logger.warning("⚠️ Connectivité MQTT défaillante, certaines fonctionnalités seront limitées")
            
        # Test de détection de présence
        presence_ok = await self.test_presence_detection(duration=15)
        if not presence_ok:
            logger.warning("⚠️ Détection de présence non validée, passage au test d'authentification")
            
        # Test d'authentification
        auth_ok = await self.test_authentication(duration=30)
        
        # Résumé des tests
        logger.info("=== RÉSUMÉ DES TESTS ===")
        logger.info(f"▶️ Connectivité MQTT: {'✅ OK' if mqtt_ok else '❌ ÉCHEC'}")
        logger.info(f"▶️ Détection présence: {'✅ OK' if presence_ok else '❌ ÉCHEC'}")
        logger.info(f"▶️ Authentification: {'✅ OK' if auth_ok else '❌ ÉCHEC'}")
        
        # Jouer un pattern sonore selon le résultat global
        if mqtt_ok and (presence_ok or auth_ok):
            logger.info("✅ TESTS GLOBALEMENT RÉUSSIS")
            await self.feedback_controller.indicate_success()
            return True
        else:
            logger.warning("❌ TESTS PARTIELLEMENT ÉCHOUÉS")
            await self.feedback_controller.indicate_failure()
            return False
    
    async def cleanup(self):
        """Nettoyage des ressources"""
        logger.info("Nettoyage des ressources...")
        
        # Arrêter la surveillance du capteur de distance
        if self.sensor_controller and self.sensor_controller.is_monitoring:
            await self.sensor_controller.stop_monitoring()
            
        # Déconnecter MQTT
        if self.mqtt_manager:
            await self.mqtt_manager.disconnect()
            
async def main():
    """Point d'entrée principal"""
    parser = argparse.ArgumentParser(description='Tests d\'intégration du module Edge Attendance System')
    parser.add_argument('--all', action='store_true', help='Exécuter tous les tests')
    parser.add_argument('--presence', action='store_true', help='Tester la détection de présence')
    parser.add_argument('--auth', action='store_true', help='Tester l\'authentification')
    parser.add_argument('--mqtt', action='store_true', help='Tester la connectivité MQTT')
    
    args = parser.parse_args()
    
    # Créer l'instance de test
    presence_test = PresenceUnitTest()
    
    try:
        # Initialiser le système pour tous les tests
        if not await presence_test.initialize():
            logger.error("Impossible d'initialiser le système de test")
            return
        
        # Exécuter les tests demandés
        if args.all or (not args.presence and not args.auth and not args.mqtt):
            await presence_test.run_all_tests()
        else:
            if args.mqtt:
                await presence_test.test_mqtt_connectivity()
                
            if args.presence:
                await presence_test.test_presence_detection()
                
            if args.auth:
                await presence_test.test_authentication()
    
    except KeyboardInterrupt:
        logger.info("Tests interrompus par l'utilisateur")
    except Exception as e:
        logger.critical(f"Erreur lors de l'exécution des tests: {e}")
    finally:
        # Nettoyage
        await presence_test.cleanup()
        
    logger.info("Tests d'intégration terminés.")

if __name__ == "__main__":
    asyncio.run(main())
