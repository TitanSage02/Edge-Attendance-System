#!/usr/bin/env python3
"""
Test physique et interactif du module de feedback (LEDs et buzzer)
Ce script permet de tester physiquement les LEDs et le buzzer sur un Raspberry Pi.
"""

import sys
import os
import time
import asyncio

# Ajouter le chemin du projet aux chemins de recherche
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sensors.feedback import FeedbackController
from utils.logger import setup_logger
import logging
import RPi.GPIO as GPIO

# Configuration GPIO
GPIO.setwarnings(False)  # Désactiver les avertissements
GPIO.setmode(GPIO.BCM)   # Utiliser le mode BCM

# Récupération des pins depuis config.py si disponible
try:
    from config import config
    RED_LED_PIN = config.RED_LED_PIN
    GREEN_LED_PIN = config.GREEN_LED_PIN
    BUZZER_PIN = config.BUZZER_PIN
except (ImportError, AttributeError):
    # Pins par défaut si la configuration n'est pas disponible
    RED_LED_PIN = 18
    GREEN_LED_PIN = 16
    BUZZER_PIN = 12

# Logger pour les tests
logger = setup_logger(
    name="feedback_test",
    level=logging.INFO,
    console_level=logging.INFO
)

async def test_physical_feedback():
    """Test physique et interactif du contrôleur de feedback"""
    
    try:
        logger.info("🔔 Initialisation du contrôleur de feedback...")
        logger.info(f"Pins utilisés: LED Rouge={RED_LED_PIN}, LED Verte={GREEN_LED_PIN}, Buzzer={BUZZER_PIN}")
        
        # Initialisation du contrôleur
        feedback = FeedbackController(
            red_led_pin=RED_LED_PIN,
            green_led_pin=GREEN_LED_PIN,
            buzzer_pin=BUZZER_PIN
        )
        
        logger.info("✅ Contrôleur initialisé avec succès")
        logger.info("📊 Tests physiques des composants de feedback")
        
        return feedback
    
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'initialisation: {e}")
        GPIO.cleanup()
        raise


async def test_leds():
    """Test des LEDs rouge et verte"""
    feedback = await test_physical_feedback()
    
    try:
        # Test LED rouge
        logger.info("🔴 Test de la LED rouge...")
        logger.info("  Allumage...")
        feedback._set_led(feedback.red_led_pin, feedback.red_pwm, True)
        time.sleep(2)
        logger.info("  Extinction...")
        feedback._set_led(feedback.red_led_pin, feedback.red_pwm, False)
        
        time.sleep(0.5)
        
        # Test LED verte
        logger.info("🟢 Test de la LED verte...")
        logger.info("  Allumage...")
        feedback._set_led(feedback.green_led_pin, feedback.green_pwm, True)
        time.sleep(2)
        logger.info("  Extinction...")
        feedback._set_led(feedback.green_led_pin, feedback.green_pwm, False)
        
        # Test réglage d'intensité (si PWM activé)
        logger.info("💡 Test d'intensité variable...")
        for brightness in [20, 40, 60, 80, 100]:
            logger.info(f"  Intensité: {brightness}%")
            feedback.set_brightness(brightness)
            feedback._set_led(feedback.red_led_pin, feedback.red_pwm, True)
            time.sleep(0.5)
        
        feedback._set_led(feedback.red_led_pin, feedback.red_pwm, False)
        
        logger.info("✅ Test des LEDs terminé")
    finally:
        # Nettoyage dans tous les cas
        feedback.turn_off_all()

async def test_buzzer():
    """Test du buzzer avec différentes fréquences"""
    feedback = await test_physical_feedback()
    
    try:
        logger.info("🔊 Test du buzzer...")
        
        # Test de différentes fréquences
        frequencies = [300, 500, 800, 1000, 1200]
        for freq in frequencies:
            logger.info(f"  Fréquence: {freq}Hz")
            feedback._play_tone(freq, 0.3)
            time.sleep(0.2)
        
        logger.info("✅ Test du buzzer terminé")
    finally:
        feedback.turn_off_all()

async def test_patterns():
    """Test des patterns d'animation prédéfinis"""
    feedback = await test_physical_feedback()
    
    try:
        logger.info("🎬 Test des patterns d'animation...")
        
        # Pattern de démarrage
        logger.info("🚀 Pattern de démarrage...")
        await feedback.indicate_startup()
        time.sleep(4)
        
        # Pattern de succès
        logger.info("✅ Pattern de succès...")
        await feedback.indicate_success()
        time.sleep(3)
        
        # Pattern d'échec
        logger.info("❌ Pattern d'échec...")
        await feedback.indicate_failure()
        time.sleep(3)
        
        # Pattern d'alerte
        logger.info("⚠️ Pattern d'alerte...")
        feedback.indicate_alert()
        time.sleep(3)
        
        # Pattern d'arrêt
        logger.info("🛑 Pattern d'arrêt...")
        await feedback.play_pattern('shutdown')
        time.sleep(2)
        
        logger.info("✅ Test des patterns terminé")
    finally:
        feedback.turn_off_all()

async def test_interactive_feedback():
    """Test interactif du module de feedback"""
    feedback = await test_physical_feedback()
    
    try:
        logger.info("👉 Menu de test interactif:")
        logger.info("1. Test LED rouge")
        logger.info("2. Test LED verte")
        logger.info("3. Test buzzer")
        logger.info("4. Animation de succès")
        logger.info("5. Animation d'échec")
        logger.info("6. Animation d'alerte")
        logger.info("7. Animation de démarrage")
        logger.info("8. Test complet")
        logger.info("9. Régler la luminosité des LEDs")
        logger.info("q. Quitter")
        
        while True:
            # Attendre l'entrée utilisateur
            user_input = input("Choisissez une option (1-9, q): ")
            
            if user_input.lower() == 'q':
                logger.info("👋 Au revoir !")
                break
            
            elif user_input == '1':
                logger.info("🔴 Test LED rouge...")
                feedback._set_led(feedback.red_led_pin, feedback.red_pwm, True)
                time.sleep(2)
                feedback._set_led(feedback.red_led_pin, feedback.red_pwm, False)
            
            elif user_input == '2':
                logger.info("🟢 Test LED verte...")
                feedback._set_led(feedback.green_led_pin, feedback.green_pwm, True)
                time.sleep(2)
                feedback._set_led(feedback.green_led_pin, feedback.green_pwm, False)
            
            elif user_input == '3':
                logger.info("🔊 Test buzzer...")
                freq = input("Entrez une fréquence (Hz) [800]: ") or "800"
                duration = input("Entrez une durée (s) [0.5]: ") or "0.5"
                try:
                    feedback._play_tone(int(freq), float(duration))
                except ValueError:
                    logger.warning("Valeurs incorrectes, utilisation des valeurs par défaut")
                    feedback._play_tone(800, 0.5)
            
            elif user_input == '4':
                logger.info("✅ Animation de succès...")
                await feedback.indicate_success()
                time.sleep(3)  # Laisser l'animation se terminer
            
            elif user_input == '5':
                logger.info("❌ Animation d'échec...")
                await feedback.indicate_failure()
                time.sleep(3)  # Laisser l'animation se terminer
            
            elif user_input == '6':
                logger.info("⚠️ Animation d'alerte...")
                feedback.indicate_alert()
                time.sleep(3)  # Laisser l'animation se terminer
            
            elif user_input == '7':
                logger.info("🚀 Animation de démarrage...")
                await feedback.indicate_startup()
                time.sleep(5)  # Laisser l'animation se terminer
            
            elif user_input == '8':
                logger.info("🧪 Test complet...")
                await feedback.test_feedback()
            
            elif user_input == '9':
                logger.info("💡 Réglage de la luminosité...")
                try:
                    brightness = int(input("Entrez la luminosité (0-100%): "))
                    if 0 <= brightness <= 100:
                        feedback.set_brightness(brightness)
                        logger.info(f"Luminosité réglée à {brightness}%")
                        
                        # Montrer l'effet
                        logger.info("Démonstration...")
                        feedback._set_led(feedback.red_led_pin, feedback.red_pwm, True)
                        feedback._set_led(feedback.green_led_pin, feedback.green_pwm, True)
                        time.sleep(2)
                        feedback._set_led(feedback.red_led_pin, feedback.red_pwm, False)
                        feedback._set_led(feedback.green_led_pin, feedback.green_pwm, False)
                    else:
                        logger.warning("La luminosité doit être entre 0 et 100%")
                except ValueError:
                    logger.warning("Valeur incorrecte")
            
            else:
                logger.warning("⚠️ Option non reconnue")
    
    finally:
        # Nettoyage dans tous les cas
        feedback.cleanup()
        logger.info("Ressources libérées")

async def test_synchronization():
    """Test de synchronisation des LEDs et du buzzer"""
    feedback = await test_physical_feedback()
    
    try:
        logger.info("🔄 Test de synchronisation des composants...")
        
        # Clignotement synchronisé avec bip
        for _ in range(5):
            # Allumer les LEDs et jouer un son
            feedback._set_led(feedback.red_led_pin, feedback.red_pwm, True)
            feedback._set_led(feedback.green_led_pin, feedback.green_pwm, True)
            feedback._play_tone(800, 0.1)
            
            # Pause courte
            time.sleep(0.2)
            
            # Éteindre les LEDs
            feedback._set_led(feedback.red_led_pin, feedback.red_pwm, False)
            feedback._set_led(feedback.green_led_pin, feedback.green_pwm, False)
            
            # Pause avant le prochain cycle
            time.sleep(0.2)
        
        logger.info("✅ Test de synchronisation terminé")
    finally:
        feedback.turn_off_all()


if __name__ == "__main__":
    try:
        if len(sys.argv) > 1:
            if sys.argv[1] == '--interactive':
                # Mode interactif
                asyncio.run(test_interactive_feedback())
            elif sys.argv[1] == '--leds':
                # Test des LEDs uniquement
                asyncio.run(test_leds())
            elif sys.argv[1] == '--buzzer':
                # Test du buzzer uniquement
                asyncio.run(test_buzzer())
            elif sys.argv[1] == '--patterns':
                # Test des patterns d'animation
                asyncio.run(test_patterns())
            elif sys.argv[1] == '--sync':
                # Test de synchronisation
                asyncio.run(test_synchronization())
            else:
                print(f"Option inconnue: {sys.argv[1]}")
                print("Options disponibles: --interactive, --leds, --buzzer, --patterns, --sync")
        else:
            # Mode interactif par défaut
            asyncio.run(test_interactive_feedback())
    except KeyboardInterrupt:
        print("\nTest interrompu par l'utilisateur")
        # Nettoyage GPIO si nécessaire
        GPIO.cleanup()
    except Exception as e:
        print(f"Erreur lors de l'exécution du test: {e}")
        # Nettoyage GPIO si nécessaire
        GPIO.cleanup()
