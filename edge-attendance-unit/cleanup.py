#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script de nettoyage d'urgence pour Edge Attendance System
Ce script est destiné à être exécuté en cas de crash pour nettoyer les ressources.
"""

import os
import sys
import logging
import traceback
import RPi.GPIO as GPIO

# Ajout du chemin parent pour l'import
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.logger import setup_logger

# Configuration du logger
logger = setup_logger("emergency_cleanup", logging.INFO)

def cleanup_gpio():
    """Nettoie toutes les ressources GPIO"""
    try:
        logger.info("Nettoyage des GPIO...")
        GPIO.setwarnings(False)
        GPIO.cleanup()
        logger.info("✅ GPIO nettoyé avec succès")
        return True
    except Exception as e:
        logger.error(f"❌ Erreur lors du nettoyage GPIO: {e}")
        return False

def cleanup_camera():
    """Essaie de fermer proprement la caméra"""
    try:
        logger.info("Tentative de fermeture de la caméra...")
        # Essayer d'importer et de fermer la caméra
        try:
            from picamera2 import Picamera2
            # Essayer de récupérer l'instance et de la fermer
            try:
                camera = Picamera2()
                camera.close()
                logger.info("✅ Caméra fermée proprement")
            except:
                logger.warning("⚠️ Impossible de récupérer l'instance de la caméra")
        except ImportError:
            logger.warning("⚠️ Module picamera2 non disponible")
        
        return True
    except Exception as e:
        logger.error(f"❌ Erreur lors du nettoyage de la caméra: {e}")
        return False

def kill_processes():
    """Tue les processus potentiellement bloqués"""
    try:
        logger.info("Recherche des processus Python bloqués...")
        
        # Liste des processus à arrêter
        processes_to_kill = ["python3", "python"]
        
        # Tuer les processus Python (sauf ce script)
        pid = os.getpid()
        logger.info(f"PID actuel: {pid} (sera ignoré)")
        
        for proc_name in processes_to_kill:
            os.system(f"pkill -9 -f {proc_name} | grep -v {pid}")
        
        logger.info("✅ Processus terminés")
        return True
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'arrêt des processus: {e}")
        return False

def main():
    """Point d'entrée principal"""
    logger.info("=== DÉMARRAGE DU NETTOYAGE D'URGENCE ===")
    
    # Nettoyer les GPIO
    gpio_cleaned = cleanup_gpio()
    
    # Nettoyer la caméra
    camera_cleaned = cleanup_camera()
    
    # Tuer les processus bloqués
    processes_killed = kill_processes()
    
    # Résumé
    logger.info("\n=== RÉSULTAT DU NETTOYAGE ===")
    logger.info(f"GPIO: {'✅ OK' if gpio_cleaned else '❌ Échec'}")
    logger.info(f"Caméra: {'✅ OK' if camera_cleaned else '❌ Échec'}")
    logger.info(f"Processus: {'✅ OK' if processes_killed else '❌ Échec'}")
    
    # Déterminer le résultat global
    all_ok = gpio_cleaned and camera_cleaned and processes_killed
    if all_ok:
        logger.info("\n✅ NETTOYAGE COMPLET RÉUSSI")
        return 0
    else:
        logger.warning("\n⚠️ NETTOYAGE PARTIEL")
        return 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except Exception as e:
        logger.critical(f"Erreur fatale: {e}")
        traceback.print_exc()
        sys.exit(1)
