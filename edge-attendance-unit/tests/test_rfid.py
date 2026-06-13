#!/usr/bin/env python3
"""
Test du lecteur RFID pour Edge Attendance Unit
Ce script teste uniquement la fonctionnalité du lecteur RFID
"""

import sys
import os
import time
import logging
from logging.handlers import RotatingFileHandler
import signal
import atexit

# Ajouter le répertoire parent au path pour pouvoir importer les modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sensors.rfid import RFIDController
from config import config

# Importer le logger personnalisé
from utils.logger import setup_logger

# Fonction de test du lecteur RFID
def test_rfid_reader():
    logger = setup_logger("rfid_test", logging.DEBUG)
    logger.info("=== Test du lecteur RFID Edge Attendance Unit ===")
    
    # Gestion de l'arrêt du script avec CTRL+C
    running = True
    
    def signal_handler(sig, frame):
        nonlocal running
        logger.info("Arrêt du test RFID...")
        running = False
    
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        # Affichage des informations de configuration
        logger.info(f"Utilisation du pin RFID: {config.RFID_PIN}")
        
        # Enregistrer le nettoyage GPIO à la sortie du programme
        import RPi.GPIO as GPIO
        atexit.register(GPIO.cleanup)
        
        # Initialisation du contrôleur RFID
        rfid_controller = RFIDController(rst_pin=config.RFID_PIN)
        logger.info("Contrôleur RFID initialisé avec succès")
        
        # Fonction de callback pour afficher les badges détectés
        def card_detected_callback(card_id):
            # Conversion de l'UID en format hexadécimal (sans les 2 derniers caractères)
            uid_hex = rfid_controller._format_uid_hex(card_id)
            logger.info(f"Badge RFID détecté - HEX: {uid_hex}")
            return True  # Continue la lecture
        
        # Démarrage de la lecture continue
        rfid_controller.start_continuous_reading(callback=card_detected_callback)
        
        # Boucle principale
        logger.info("Veuillez présenter un badge RFID...")
        logger.info("Appuyez sur CTRL+C pour arrêter le test")
        
        while running:
            time.sleep(0.1)
            
    except Exception as e:
        logger.error(f"Erreur pendant le test RFID: {e}", exc_info=True)
    finally:
        # Nettoyage
        if 'rfid_controller' in locals():
            rfid_controller.stop_reading()
            logger.info("Contrôleur RFID arrêté")
        
        # Le nettoyage GPIO sera effectué par atexit.register à la sortie du programme
        logger.info("=== Fin du test RFID ===")

if __name__ == "__main__":
    test_rfid_reader()
