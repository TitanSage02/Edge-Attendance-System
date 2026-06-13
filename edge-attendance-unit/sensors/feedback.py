import time
import logging
from utils.logger import setup_logger
import threading
from typing import Optional, Dict, Any
import RPi.GPIO as GPIO
from threading import Thread, Event

from config import config

class FeedbackController:
    """
    Contrôleur pour les retours visuels et sonores
    Gestion des LEDs (rouge/verte) et du buzzer
    """

    def __init__(self,
                 red_led_pin=config.RED_LED_PIN,
                 green_led_pin=config.GREEN_LED_PIN,
                 blue_led_pin=config.BLUE_LED_PIN,
                 buzzer_pin=config.BUZZER_PIN,
                 use_pwm: bool = True):
        """
        Initialise le contrôleur de feedback
        
        Args:
            red_led_pin: Pin GPIO pour LED rouge
            green_led_pin: Pin GPIO pour LED verte
            blue_led_pin: Pin GPIO pour LED bleue
            buzzer_pin: Pin GPIO pour le buzzer
            use_pwm: Utiliser PWM pour contrôler l'intensité des LEDs
        """
        
        self.logger = setup_logger(
            name="feedback",
            level=logging.INFO,
            console_level=logging.INFO
        )
        
        # Configuration des pins
        self.red_led_pin = red_led_pin
        self.green_led_pin = green_led_pin
        self.blue_led_pin = blue_led_pin
        self.buzzer_pin = buzzer_pin
        self.use_pwm = use_pwm
        
        # Objets PWM pour contrôle d'intensité
        self.red_pwm = None
        self.green_pwm = None
        self.blue_pwm = None
        self.buzzer_pwm = None
        
        # Configuration PWM
        self.pwm_frequency = 1000  # 1kHz pour LEDs
        self.buzzer_frequency = 2000  # 2kHz spécifique pour buzzer (plus efficace)
        self.led_brightness = 70   # 0-100%
        self.buzzer_volume = 80    # 0-100% - Volume du buzzer
        
        # Configuration des patterns sonores
        # Format: liste de tuples (fréquence en Hz, durée en secondes)
        self.sound_patterns = {
            'success': [
                (600, 0.15),   # 600Hz pendant 150ms - Plus grave, plus audible
                (800, 0.15),   # 800Hz pendant 150ms  
                (1000, 0.2)    # 1000Hz pendant 200ms - Finition plus claire
            ],
            'failure': [
                (300, 0.4),    # 300Hz pendant 400ms - Son grave d'erreur
                (0, 0.2),      # Pause de 200ms
                (300, 0.4),    # 300Hz pendant 400ms - Deuxième son
                (0, 0.2),      # Pause de 200ms
                (300, 0.4)     # 300Hz pendant 400ms - Troisième son
            ],
            'alert': [
                (800, 0.15),   # 800Hz au lieu de 1319Hz - Plus audible
                (0, 0.05),     # Pause
                (800, 0.15),   # 800Hz
                (0, 0.05),     # Pause
                (800, 0.15),   # 800Hz
                (0, 0.05),     # Pause
                (800, 0.4)     # 800Hz - Plus long et plus grave
            ],
            'startup': [
                (500, 0.2),    # 500Hz pendant 200ms - Plus grave
                (700, 0.2),    # 700Hz pendant 200ms
                (900, 0.3)     # 900Hz pendant 300ms - Plus long
            ]
        }
        
        # Threading pour animations non-bloquantes
        self.animation_thread = None
        self.stop_animation = Event()
        self.is_initialized = False
        
        # Initialiser les GPIOs
        self._initialize_gpio()
        
    def _initialize_gpio(self):
        """Initialise les pins GPIO et PWM"""
        try:
            # Configuration des pins en sortie
            GPIO.setup(self.red_led_pin, GPIO.OUT)
            GPIO.setup(self.green_led_pin, GPIO.OUT)
            GPIO.setup(self.blue_led_pin, GPIO.OUT)
            GPIO.setup(self.buzzer_pin, GPIO.OUT)
            
            # Éteindre toutes les LEDs au démarrage sauf la bleue
            GPIO.output(self.red_led_pin, GPIO.LOW)
            GPIO.output(self.green_led_pin, GPIO.LOW)
            GPIO.output(self.buzzer_pin, GPIO.LOW)
            
            if self.use_pwm:
                # Initialiser PWM pour les LEDs et buzzer
                self.red_pwm = GPIO.PWM(self.red_led_pin, self.pwm_frequency)
                self.green_pwm = GPIO.PWM(self.green_led_pin, self.pwm_frequency)
                self.blue_pwm = GPIO.PWM(self.blue_led_pin, self.pwm_frequency)
                self.buzzer_pwm = GPIO.PWM(self.buzzer_pin, self.buzzer_frequency)  # Fréquence spécifique
                
                # Démarrer PWM avec duty cycle 0 pour toutes sauf bleue
                self.red_pwm.start(0)
                self.green_pwm.start(0)
                self.blue_pwm.start(self.led_brightness)  # LED bleue allumée par défaut
                self.buzzer_pwm.start(0)
            else:
                # Allumer la LED bleue par défaut en mode non-PWM
                GPIO.output(self.blue_led_pin, GPIO.HIGH)
            
            self.is_initialized = True
            self.logger.info("FeedbackController initialisé avec succès")
            
            # Jouer le son de démarrage
            self._play_sound_pattern('startup')
            
        except Exception as e:
            self.logger.error(f"Erreur lors de l'initialisation GPIO: {e}")
            raise
    
    def _set_led(self, 
                 led_pin: int, 
                 pwm_obj: Optional[GPIO.PWM], 
                 state: bool, 
                 brightness: int = None):
        """
        Contrôle une LED avec ou sans PWM
        
        Args:
            led_pin: Pin GPIO de la LED
            pwm_obj: Objet PWM correspondant
            state: True pour allumer, False pour éteindre
            brightness: Intensité 0-100% (uniquement avec PWM)
        """
        if not self.is_initialized:
            return
            
        try:
            if self.use_pwm and pwm_obj:
                if state:
                    intensity = brightness if brightness is not None else self.led_brightness
                    pwm_obj.ChangeDutyCycle(intensity)
                else:
                    pwm_obj.ChangeDutyCycle(0)
            else:
                GPIO.output(led_pin, GPIO.HIGH if state else GPIO.LOW)
                
        except Exception as e:
            self.logger.error(f"Erreur contrôle LED pin {led_pin}: {e}")
    
    def _return_to_default_state(self):
        """Retourne à l'état par défaut avec LED bleue allumée"""
        if not self.is_initialized:
            return
            
        try:
            # Éteindre rouge et verte
            self._set_led(self.red_led_pin, self.red_pwm, False)
            self._set_led(self.green_led_pin, self.green_pwm, False)
            
            # Allumer bleue
            self._set_led(self.blue_led_pin, self.blue_pwm, True)
            
        except Exception as e:
            self.logger.error(f"Erreur retour état par défaut: {e}")
    
    def _play_tone(self, frequency: int, duration: float):
        """
        Joue un ton avec le buzzer
        
        Args:
            frequency: Fréquence en Hz
            duration: Durée en secondes
        """
        if not self.is_initialized:
            return
            
        try:
            if self.use_pwm and self.buzzer_pwm:
                # Changer la fréquence du PWM
                self.buzzer_pwm.ChangeFrequency(frequency)
                self.buzzer_pwm.ChangeDutyCycle(self.buzzer_volume)  # Utiliser le volume configuré
                time.sleep(duration)
                self.buzzer_pwm.ChangeDutyCycle(0)
            else:
                # Génération manuelle du signal
                period = 1.0 / frequency
                half_period = period / 2
                end_time = time.time() + duration
                
                while time.time() < end_time:
                    if self.stop_animation.is_set():
                        break
                    GPIO.output(self.buzzer_pin, GPIO.HIGH)
                    time.sleep(half_period)

                    GPIO.output(self.buzzer_pin, GPIO.LOW)
                    time.sleep(half_period)
                    
        except Exception as e:
            self.logger.error(f"Erreur lors de la génération du ton: {e}")
    
    def _play_sound_pattern(self, pattern_name: str):
        """
        Joue un pattern sonore défini
        
        Args:
            pattern_name: Nom du pattern ('success', 'failure', 'alert', 'startup')
        """
        if pattern_name not in self.sound_patterns:
            self.logger.warning(f"Pattern sonore '{pattern_name}' non trouvé")
            return
            
        pattern = self.sound_patterns[pattern_name]
        
        # Joue chaque note de la séquence
        for i, note in enumerate(pattern):
            if self.stop_animation.is_set():
                break
                
            frequency, duration = note
            
            if frequency > 0:
                # Joue une note
                self._play_tone(frequency, duration)
            else:
                # Pause silencieuse (fréquence = 0)
                time.sleep(duration)
            
            # Ajouter une pause de 50ms entre les notes pour les patterns success/startup
            # (équivalent au delay(50) dans le code Arduino)
            if pattern_name in ['success', 'startup'] and i < len(pattern) - 1:
                time.sleep(0.05)  # 50ms de pause
    
    def _led_fade_animation(self, led_pin: int, pwm_obj: Optional[GPIO.PWM], 
                          duration: float = 2.0, fade_in: bool = True):
        """
        Animation de fade pour une LED
        
        Args:
            led_pin: Pin de la LED
            pwm_obj: Objet PWM
            duration: Durée de l'animation
            fade_in: True pour fade in, False pour fade out
        """
        if not self.use_pwm or not pwm_obj:
            return
            
        steps = 50
        step_duration = duration / steps
        
        for i in range(steps + 1):
            if self.stop_animation.is_set():
                break
                
            if fade_in:
                brightness = (i / steps) * self.led_brightness
            else:
                brightness = ((steps - i) / steps) * self.led_brightness
                
            pwm_obj.ChangeDutyCycle(brightness)
            time.sleep(step_duration)
    
    def _blink_animation(self, led_pin: int, pwm_obj: Optional[GPIO.PWM], 
                        count: int = 3, on_time: float = 0.2, off_time: float = 0.2):
        """
        Animation de clignotement
        
        Args:
            led_pin: Pin de la LED
            pwm_obj: Objet PWM
            count: Nombre de clignotements
            on_time: Durée allumée
            off_time: Durée éteinte
        """
        for i in range(count):
            if self.stop_animation.is_set():
                break
                
            self._set_led(led_pin, pwm_obj, True)
            time.sleep(on_time)
            self._set_led(led_pin, pwm_obj, False)
            
            if i < count - 1:  # Pas de pause après le dernier clignotement
                time.sleep(off_time)
    
    async def indicate_success(self):
        """LED verte + son de succès, puis retour à la LED bleue"""
        self.stop_current_animation()
        
        def success_animation():
            try:
                # Éteindre la LED bleue
                self._set_led(self.blue_led_pin, self.blue_pwm, False)
                
                # LED verte avec fade in
                self._led_fade_animation(self.green_led_pin, self.green_pwm, 
                                       duration=0.5, fade_in=True)
                
                # Son de succès
                self._play_sound_pattern('success')
                
                # Maintenir LED allumée 1 seconde
                time.sleep(1.0)
                
                # Fade out
                self._led_fade_animation(self.green_led_pin, self.green_pwm, 
                                       duration=0.5, fade_in=False)
                
                # Retour à l'état par défaut (LED bleue)
                self._return_to_default_state()
                
            except Exception as e:
                self.logger.error(f"Erreur animation succès: {e}")
                self._return_to_default_state()
        
        self.animation_thread = Thread(target=success_animation, daemon=True)
        self.animation_thread.start()
        
        self.logger.info("Indication de succès activée")
    
    async def indicate_failure(self):
        """LED rouge + son d'échec, puis retour à la LED bleue"""
        self.stop_current_animation()
        
        def failure_animation():
            try:
                # Éteindre la LED bleue
                self._set_led(self.blue_led_pin, self.blue_pwm, False)
                
                # LED rouge clignotante
                self._blink_animation(self.red_led_pin, self.red_pwm, 
                                    count=3, on_time=0.3, off_time=0.2)
                
                # Son d'échec
                self._play_sound_pattern('failure')
                
                # LED rouge fixe pendant 2 secondes
                self._set_led(self.red_led_pin, self.red_pwm, True)
                time.sleep(2.0)
                
                # Éteindre rouge et retour au bleu
                self._set_led(self.red_led_pin, self.red_pwm, False)
                self._return_to_default_state()
                
            except Exception as e:
                self.logger.error(f"Erreur animation échec: {e}")
                self._return_to_default_state()
        
        self.animation_thread = Thread(target=failure_animation, daemon=True)
        self.animation_thread.start()
        
        self.logger.info("Indication d'échec activée")
    
    def indicate_alert(self):
        """Signal d'alerte, puis retour à la LED bleue"""
        self.stop_current_animation()
        
        def alert_animation():
            try:
                # Éteindre la LED bleue
                self._set_led(self.blue_led_pin, self.blue_pwm, False)
                
                # Alternance rapide rouge/vert avec sons
                for cycle in range(3):
                    if self.stop_animation.is_set():
                        break
                    
                    # Rouge
                    self._set_led(self.red_led_pin, self.red_pwm, True)
                    self._set_led(self.green_led_pin, self.green_pwm, False)
                    self._play_tone(1200, 0.15)
                    
                    time.sleep(0.1)
                    
                    # Vert
                    self._set_led(self.red_led_pin, self.red_pwm, False)
                    self._set_led(self.green_led_pin, self.green_pwm, True)
                    self._play_tone(800, 0.15)
                    
                    time.sleep(0.1)
                
                # Éteindre toutes les LEDs et retour au bleu
                self._set_led(self.red_led_pin, self.red_pwm, False)
                self._set_led(self.green_led_pin, self.green_pwm, False)
                self._return_to_default_state()
                
            except Exception as e:
                self.logger.error(f"Erreur animation alerte: {e}")
                self._return_to_default_state()
        
        self.animation_thread = Thread(target=alert_animation, daemon=True)
        self.animation_thread.start()
        
        self.logger.info("Signal d'alerte activé")
    
    async def indicate_startup(self):
        """Signal de démarrage du système, puis retour à la LED bleue"""
        self.stop_current_animation()
        
        def startup_animation():
            try:
                # Éteindre la LED bleue temporairement
                self._set_led(self.blue_led_pin, self.blue_pwm, False)
                
                # Séquence de démarrage progressive
                
                # 1. LEDs qui s'allument progressivement
                self._led_fade_animation(self.green_led_pin, self.green_pwm, 
                                       duration=1.0, fade_in=True)
                
                time.sleep(0.5)
                
                self._led_fade_animation(self.red_led_pin, self.red_pwm, 
                                       duration=1.0, fade_in=True)
                
                # 2. Son de démarrage
                self._play_sound_pattern('startup')
                
                # 3. Clignotement synchronisé
                for i in range(2):
                    if self.stop_animation.is_set():
                        break
                    self._set_led(self.red_led_pin, self.red_pwm, False)
                    self._set_led(self.green_led_pin, self.green_pwm, False)
                    time.sleep(0.3)
                    self._set_led(self.red_led_pin, self.red_pwm, True)
                    self._set_led(self.green_led_pin, self.green_pwm, True)
                    time.sleep(0.3)
                
                # 4. Extinction progressive
                self._led_fade_animation(self.red_led_pin, self.red_pwm, 
                                       duration=1.0, fade_in=False)
                self._led_fade_animation(self.green_led_pin, self.green_pwm, 
                                       duration=1.0, fade_in=False)
                
                # 5. Retour à l'état par défaut (LED bleue)
                self._return_to_default_state()
                
            except Exception as e:
                self.logger.error(f"Erreur animation démarrage: {e}")
                self._return_to_default_state()
        
        self.animation_thread = Thread(target=startup_animation, daemon=True)
        self.animation_thread.start()
        
        self.logger.info("Signal de démarrage activé")
    
    
    def stop_current_animation(self):
        """Arrête l'animation en cours"""
        self.stop_animation.set()
        
        if self.animation_thread and self.animation_thread.is_alive():
            self.animation_thread.join(timeout=1.0)
        
        self.stop_animation.clear()
    
    def turn_off_all(self):
        """Éteint toutes les LEDs et arrête les sons"""
        self.stop_current_animation()
        
        if self.is_initialized:
            self._set_led(self.red_led_pin, self.red_pwm, False)
            self._set_led(self.green_led_pin, self.green_pwm, False)
            self._set_led(self.blue_led_pin, self.blue_pwm, False)
            
            if self.use_pwm and self.buzzer_pwm:
                self.buzzer_pwm.ChangeDutyCycle(0)
            else:
                GPIO.output(self.buzzer_pin, GPIO.LOW)
    
    async def turn_on_all(self):
        """Allume toutes les LEDs"""
        self.stop_current_animation()
        
        if self.is_initialized:
            self._set_led(self.red_led_pin, self.red_pwm, True)
            self._set_led(self.green_led_pin, self.green_pwm, True)
            self._set_led(self.blue_led_pin, self.blue_pwm, True)
            self.logger.info("Toutes les LEDs allumées")
    
    def set_brightness(self, brightness: int):
        """
        Définit la luminosité des LEDs
        
        Args:
            brightness: Intensité 0-100%
        """
        if 0 <= brightness <= 100:
            self.led_brightness = brightness
            self.logger.info(f"Luminosité réglée à {brightness}%")
        else:
            self.logger.warning("Luminosité doit être entre 0 et 100%")
    
    def set_buzzer_volume(self, volume: int):
        """
        Définit le volume du buzzer
        
        Args:
            volume: Volume 0-100%
        """
        if 0 <= volume <= 100:
            self.buzzer_volume = volume
            self.logger.info(f"Volume buzzer réglé à {volume}%")
        else:
            self.logger.warning("Volume doit être entre 0 et 100%")
    
    async def test_feedback(self):
        """Test de tous les composants de feedback"""
        self.logger.info("Début du test des composants feedback")
        
        try:
            # Test LED rouge
            self.logger.info("Test LED rouge...")
            self._set_led(self.red_led_pin, self.red_pwm, True)
            time.sleep(1)
            self._set_led(self.red_led_pin, self.red_pwm, False)
            
            time.sleep(0.5)
            
            # Test LED verte
            self.logger.info("Test LED verte...")
            self._set_led(self.green_led_pin, self.green_pwm, True)
            time.sleep(1)
            self._set_led(self.green_led_pin, self.green_pwm, False)
            
            time.sleep(0.5)
            
            # Test buzzer
            self.logger.info("Test buzzer...")
            self._play_tone(800, 0.5)
            
            time.sleep(0.5)
            
            # Test animations
            self.logger.info("Test animation succès...")
            await self.indicate_success()
            time.sleep(3)
            
            self.logger.info("Test animation échec...")
            await self.indicate_failure()
            time.sleep(3)
            
            self.logger.info("Test terminé avec succès")
            
        except Exception as e:
            self.logger.error(f"Erreur durant le test: {e}")
    
    def cleanup(self):
        """Nettoyage des ressources"""
        self.logger.info("Nettoyage FeedbackController...")
        
        # Stop any running animations first
        self.stop_current_animation()
        
        # Turn off all LEDs and buzzer without using GPIO.cleanup()
        self.turn_off_all()
        
        # Stop PWM objects properly
        if self.use_pwm:
            try:
                # Check if objects exist and stop them individually
                if hasattr(self, 'red_pwm') and self.red_pwm:
                    try:
                        self.red_pwm.stop()
                        self.red_pwm = None
                    except Exception as e:
                        self.logger.warning(f"Non-critique: Erreur lors de l'arrêt du PWM rouge: {e}")
                        
                if hasattr(self, 'green_pwm') and self.green_pwm:
                    try:
                        self.green_pwm.stop()
                        self.green_pwm = None
                    except Exception as e:
                        self.logger.warning(f"Non-critique: Erreur lors de l'arrêt du PWM vert: {e}")
                
                if hasattr(self, 'blue_pwm') and self.blue_pwm:
                    try:
                        self.blue_pwm.stop()
                        self.blue_pwm = None
                    except Exception as e:
                        self.logger.warning(f"Non-critique: Erreur lors de l'arrêt du PWM bleu: {e}")
                        
                if hasattr(self, 'buzzer_pwm') and self.buzzer_pwm:
                    try:
                        self.buzzer_pwm.stop()
                        self.buzzer_pwm = None
                    except Exception as e:
                        self.logger.warning(f"Non-critique: Erreur lors de l'arrêt du PWM buzzer: {e}")
                        
            except Exception as e:
                self.logger.error(f"Erreur lors de l'arrêt PWM: {e}")
        
        self.is_initialized = False
        self.logger.info("FeedbackController nettoyé")
    
    def __enter__(self):
        """Support du context manager"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Nettoyage automatique à la sortie du context manager"""
        self.cleanup()
        
    def __del__(self):
        """Destructeur pour s'assurer que les ressources sont libérées"""
        if hasattr(self, 'is_initialized') and hasattr(self, 'logger') and self.is_initialized:
            try:
                self.cleanup()
            except Exception as e:
                if hasattr(self, 'logger'):
                    self.logger.error(f"Erreur lors du nettoyage feedback dans le destructeur: {e}")
    
    async def play_pattern(self, pattern_name: str):
        """
        Joue un pattern d'animation prédéfini
        
        Args:
            pattern_name: Nom du pattern ('success', 'failure', 'error', 'startup', 'shutdown')
        """
        self.logger.info(f"Exécution du pattern '{pattern_name}'")
        
        if pattern_name == 'success':
            await self.indicate_success()
        elif pattern_name == 'failure' or pattern_name == 'error':
            await self.indicate_failure()
        elif pattern_name == 'startup':
            await self.indicate_startup()
        elif pattern_name == 'shutdown':
            # Animation d'arrêt - extinction progressive
            self.stop_current_animation()
            
            def shutdown_animation():
                try:
                    # Extinction graduelle
                    self._led_fade_animation(self.red_led_pin, self.red_pwm, 
                                          duration=1.0, fade_in=False)
                    self._led_fade_animation(self.green_led_pin, self.green_pwm, 
                                          duration=1.0, fade_in=False)
                    
                    # Son court
                    self._play_tone(400, 0.3)
                    
                except Exception as e:
                    self.logger.error(f"Erreur animation arrêt: {e}")
                    self.turn_off_all()
            
            self.animation_thread = Thread(target=shutdown_animation, daemon=True)
            self.animation_thread.start()
        else:
            self.logger.warning(f"Pattern inconnu: {pattern_name}")
            # Utiliser le pattern d'alerte par défaut
            await self.indicate_failure()