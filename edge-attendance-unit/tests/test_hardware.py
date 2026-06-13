#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script de test pour les capteurs et actionneurs de Edge Attendance Unit.
Ce script permet de tester individuellement chaque composant matériel:
- Capteur de distance VL53L0X
- Caméra et reconnaissance faciale
- Lecteur RFID
- LEDs (rouge et verte)
- Buzzer
"""

import os
import sys
import time
import asyncio
import logging
import argparse
from PIL import Image
import numpy as np

# Importer les contrôleurs de capteurs
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from sensors.sensor import VL065XController
from sensors.camera import CameraController
from sensors.rfid import RFIDController
from sensors.feedback import FeedbackController
from config import config
from utils.logger import setup_logger

# Setup logger spécifique pour les tests
logger = setup_logger("hardware_test", logging.INFO)

class HardwareTest:
    """
    Classe de test pour les composants matériels de Edge Attendance System
    """
    
    def __init__(self):
        """Initialisation des contrôleurs de capteurs"""
        logger.info("Initialisation des tests matériels...")
        
        # Initialiser les contrôleurs à None pour commencer
        self.distance_sensor = None
        self.camera = None
        self.rfid = None
        self.feedback = None
        
    async def initialize_all(self):
        """Initialise tous les contrôleurs pour les tests complets"""
        try:
            logger.info("Initialisation de tous les contrôleurs...")
            
            # Initialiser le contrôleur de feedback (LEDs et buzzer)
            self.feedback = FeedbackController(
                red_led_pin=config.RED_LED_PIN,
                green_led_pin=config.GREEN_LED_PIN,
                buzzer_pin=config.BUZZER_PIN
            )
            
            # Initialiser le capteur de distance
            self.distance_sensor = VL065XController(
                threshold=config.DISTANCE_THRESHOLD_MM
            )
            
            # Initialiser la caméra
            self.camera = CameraController()
            
            # Initialiser le lecteur RFID
            self.rfid = RFIDController()
            
            logger.info("✅ Tous les contrôleurs initialisés avec succès")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de l'initialisation: {e}")
            return False
    
    async def test_distance_sensor(self, duration=10):
        """
        Test du capteur de distance VL53L0X
        
        Args:
            duration: Durée du test en secondes
        """
        logger.info("=== TEST CAPTEUR DE DISTANCE ===")
        
        if not self.distance_sensor:
            self.distance_sensor = VL065XController(
                threshold=config.DISTANCE_THRESHOLD_MM
            )
            await self.distance_sensor.initialize()
        
        logger.info(f"Test capteur de distance pendant {duration} secondes...")
        logger.info(f"Seuil de détection: {self.distance_sensor.threshold}mm")
        logger.info("Approchez et éloignez votre main du capteur.")
        
        end_time = time.time() + duration
        while time.time() < end_time:
            distance = self.distance_sensor.read_distance()
            
            # Déterminer l'état de détection
            if distance is not None:
                if distance < self.distance_sensor.threshold:
                    status = "DÉTECTÉ"
                    # Allumer LED verte si le feedback est initialisé
                    if self.feedback:
                        await self.feedback.indicate_success()
                else:
                    status = "NON DÉTECTÉ"
                    # Éteindre LEDs si le feedback est initialisé
                    if self.feedback:
                        await self.feedback.indicate_failure()

                logger.info(f"Distance: {distance:.1f}mm - {status}")
            else:
                logger.error("Erreur de lecture du capteur")
                
                # Allumer LED rouge en cas d'erreur
                if self.feedback:
                    await self.feedback.indicate_failure()
            
            # Pause avant la prochaine mesure
            await asyncio.sleep(0.5)
        
        # Éteindre les LEDs à la fin
        if self.feedback:
            await self.feedback.turn_off_all()
        
        logger.info("Test du capteur de distance terminé")
    
    async def test_camera(self, save_image=True):
        """
        Test de la caméra et de la détection faciale
        
        Args:
            save_image: Si True, enregistre l'image capturée
        """
        logger.info("=== TEST CAMÉRA ===")
        
        if not self.camera:
            self.camera = CameraController()
        
        logger.info("Capture d'une image...")
        image = self.camera.capture_photo()
        
        if image is not None:
            logger.info(f"✅ Image capturée: {image.shape}")
            
            if save_image:
                # Créer un dossier pour les images de test s'il n'existe pas
                test_dir = "test_images"
                if not os.path.exists(test_dir):
                    os.makedirs(test_dir)
                
                # Convertir l'image numpy en PIL Image et enregistrer
                test_image_path = os.path.join(test_dir, f"test_{int(time.time())}.jpg")
                Image.fromarray(image).save(test_image_path)
                logger.info(f"Image enregistrée: {test_image_path}")
            
            # Test de détection faciale
            logger.info("Test de détection faciale...")
            
            faces = self.camera.face_app.get(image)
            if faces:
                logger.info(f"✅ {len(faces)} visage(s) détecté(s)")
                
                for i, face in enumerate(faces):
                    bbox = face.bbox.astype(int)
                    score = face.det_score
                    logger.info(f"  Visage #{i+1}: confiance={score:.2f}, position={bbox}")
                
                # Extraction d'embedding
                embedding = await self.camera.capture_and_extract()
                if embedding is not None:
                    logger.info(f"✅ Embedding facial extrait: {len(embedding)} dimensions")
                else:
                    logger.warning("❌ Échec de l'extraction d'embedding")
            else:
                logger.warning("❌ Aucun visage détecté")
            
            # Allumer LEDs selon résultat
            if self.feedback:
                if faces:
                    await self.feedback.indicate_success()
                else:
                    await self.feedback.indicate_failure()
        else:
            logger.error("❌ Échec de la capture d'image")
            if self.feedback:
                await self.feedback.indicate_failure()

        logger.info("Test caméra terminé")
    
    async def test_rfid(self, duration=15):
        """
        Test du lecteur RFID
        
        Args:
            duration: Durée maximale d'attente pour une carte en secondes
        """
        logger.info("=== TEST RFID ===")
        
        if not self.rfid:
            self.rfid = RFIDController()
            
        if not self.feedback:
            self.feedback = FeedbackController()
        
        logger.info(f"Attente d'une carte RFID pendant {duration} secondes...")
        logger.info("Veuillez présenter une carte RFID au lecteur.")
        
        try:
            uid = await self.rfid.read_async(timeout=duration)
            
            if uid:
                logger.info(f"✅ Carte RFID détectée: {uid}")
                await self.feedback.indicate_success()
            else:
                logger.warning("❌ Aucune carte RFID détectée pendant la période d'attente")
                await self.feedback.indicate_failure()
        
        except Exception as e:
            logger.error(f"❌ Erreur lors de la lecture RFID: {e}")
            if self.feedback:
                await self.feedback.indicate_failure()
        
        logger.info("Test RFID terminé")
    
    async def test_feedback(self):
        """Test des LEDs et du buzzer"""
        logger.info("=== TEST FEEDBACK ===")
        
        if not self.feedback:
            self.feedback = FeedbackController()
            
        logger.info("Test des LEDs et du buzzer...")
        await self.feedback.turn_on_all()
        # Test LED rouge
        logger.info("Test LED rouge")
        await self.feedback.indicate_failure()
        await asyncio.sleep(3)
        self.feedback.turn_off_all()
        
        # Test LED verte
        logger.info("Test LED verte")
        await self.feedback.indicate_success()
        await asyncio.sleep(3)
        self.feedback.turn_off_all()
        
    
    async def run_all_tests(self):
        """Exécute tous les tests de façon séquentielle"""
        logger.info("=== DÉMARRAGE DES TESTS MATÉRIELS ===")
        
        # Initialiser tous les contrôleurs
        if not await self.initialize_all():
            logger.error("❌ Impossible d'initialiser les contrôleurs")
            return False
            
        # Test du feedback (LEDs et buzzer)
        await self.test_feedback()
        await asyncio.sleep(3)
        
        # Test du capteur de distance
        await self.test_distance_sensor(duration=5)
        await asyncio.sleep(3)
        
        # Test de la caméra
        await self.test_camera()
        await asyncio.sleep(3)
        
        # Test du RFID
        await self.test_rfid(duration=10)
        
        logger.info("=== TOUS LES TESTS SONT TERMINÉS ===")
        return True

async def main():
    """Point d'entrée principal"""
    parser = argparse.ArgumentParser(description='Test des capteurs et actionneurs Edge Attendance System')
    parser.add_argument('--all', action='store_true', help='Exécuter tous les tests')
    parser.add_argument('--distance', action='store_true', help='Tester le capteur de distance')
    parser.add_argument('--camera', action='store_true', help='Tester la caméra')
    parser.add_argument('--rfid', action='store_true', help='Tester le lecteur RFID')
    parser.add_argument('--feedback', action='store_true', help='Tester les LEDs et le buzzer')
    
    args = parser.parse_args()
    
    # Créer l'instance de test
    hardware_test = HardwareTest()
    
    # Exécuter les tests demandés
    if args.all or (not args.distance and not args.camera and not args.rfid and not args.feedback):
        await hardware_test.run_all_tests()
    else:
        if args.feedback:
            await hardware_test.test_feedback()
            
        if args.distance:
            await hardware_test.test_distance_sensor()
            
        if args.camera:
            await hardware_test.test_camera()
            
        if args.rfid:
            await hardware_test.test_rfid()
    
    logger.info("Tests terminés.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Tests interrompus par l'utilisateur")
    except Exception as e:
        logger.critical(f"Erreur lors de l'exécution des tests: {e}")
        sys.exit(1)
