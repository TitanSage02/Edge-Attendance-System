#!/usr/bin/env python3
"""
Test interactif de la caméra avec capture sur appui de la touche Entrée
"""

import asyncio
import sys
import numpy as np
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sensors.camera import CameraController
from utils.logger import setup_logger
import logging

async def test_camera_interactive():
    logger = setup_logger(
        name="camera_test",
        level=logging.INFO,
        console_level=logging.INFO
    )
    
    try:
        logger.info("🎥 Initialisation de la caméra...")
        camera = CameraController(force_usb=True)  # Forcer l'utilisation de la caméra USB
        
        logger.info("✅ Caméra initialisée")
        logger.info("👉 Appuyez sur Entrée pour capturer une photo et extraire l'embedding")
        logger.info("👉 Appuyez sur 'q' puis Entrée pour quitter")
        
        while True:
            # Attendre l'entrée utilisateur
            user_input = input()
            
            if user_input.lower() == 'q':
                logger.info("👋 Au revoir !")
                break
            
            logger.info("📸 Capture et analyse en cours...")
            
            # Capture et extraction de l'embedding
            embedding = await camera.capture_and_extract()
            
            if embedding is not None:
                logger.info("✅ Embedding extrait avec succès !")
                logger.info(f"📊 Dimension de l'embedding: {embedding.shape}")
                logger.info(f"📊 Norme de l'embedding: {np.linalg.norm(embedding):.3f}")
                logger.info(f"📊 Quelques valeurs: {embedding[:5]}...")  # Affiche les 5 premières valeurs
            else:
                logger.warning("❌ Aucun visage détecté ou erreur lors de l'extraction")
            
            logger.info("\n👉 Appuyez sur Entrée pour une nouvelle capture, 'q' pour quitter")
            
    except KeyboardInterrupt:
        logger.info("\n👋 Test interrompu par l'utilisateur")
    except Exception as e:
        logger.error(f"❌ Erreur: {e}")
        import traceback
        logger.error(f"Détails: {traceback.format_exc()}")
    finally:
        # Nettoyage si nécessaire
        if 'camera' in locals():
            logger.info("🧹 Nettoyage des ressources...")

if __name__ == "__main__":
    try:
        asyncio.run(test_camera_interactive())
    except KeyboardInterrupt:
        print("\n🛑 Test arrêté par l'utilisateur")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Erreur fatale: {e}")
        sys.exit(1)
