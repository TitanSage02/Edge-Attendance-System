#############################
# Gestionnaire des capteurs #
#############################

import time
import asyncio
import logging
from utils.logger import setup_logger
import threading
from typing import Callable, Optional
import board
import busio
import adafruit_vl53l0x
from threading import Event, Thread

from config import config

class VL065XController:
    """
    Contrôleur pour le capteur de distance VL53L0X (VL065X)
    Détection de présence avec surveillance continue
    """
    
    def __init__(self, 
                 threshold: float = config.DISTANCE_THRESHOLD_MM, 
                 i2c_address: int = 0x29):
        """
        Initialise le contrôleur VL065X
        
        Args:
            threshold: Distance en mm en dessous de laquelle un objet est détecté
            i2c_address: Adresse I2C du capteur (par défaut 0x29)
        """

        self.logger = setup_logger(
            name="VL065X_Controller",
            level=logging.INFO,
            console_level=logging.INFO
        )
        
        self.threshold = threshold
        self.i2c_address = i2c_address
        self.sensor = None
        self.is_monitoring = False
        self.monitoring_thread = None
        self.stop_event = Event()
        
        self.logger.info(f"Initialisation du capteur VL065X - Seuil défini: {self.threshold}mm")
        
        # Configuration du capteur
        self.sensor_config = {
            'measurement_timing_budget': 200000,  # 200ms en microsecondes
            'signal_rate_limit': 0.1,
            'pre_range_vcsel_period': 18,
            'final_range_vcsel_period': 14
        }
        
        self._initialize_sensor()
    
    def _initialize_sensor(self):
        """Initialise le capteur VL53L0X"""
        try:
            # Initialiser I2C
            i2c = busio.I2C(board.SCL, board.SDA)
            
            # Créer l'objet capteur
            self.sensor = adafruit_vl53l0x.VL53L0X(i2c, address=self.i2c_address)
            
            # Appliquer la configuration
            self._configure_sensor()
            
            # Test de lecture
            test_distance = self.sensor.range
            self.logger.info(f"VL065X initialisé - Distance test: {test_distance}mm")
            
        except Exception as e:
            self.logger.error(f"Erreur initialisation VL065X: {e}")
            raise RuntimeError(f"Impossible d'initialiser le capteur VL065X: {e}")
    
    def _configure_sensor(self):
        """Configure les paramètres avancés du capteur"""
        try:
            # Configuration du timing budget (précision vs vitesse)
            self.sensor.measurement_timing_budget = self.sensor_config['measurement_timing_budget']
            
            # Configuration de la limite de taux de signal
            self.sensor.signal_rate_limit = self.sensor_config['signal_rate_limit']
            
            # Configuration des périodes VCSEL
            self.sensor.pre_range_vcsel_period = self.sensor_config['pre_range_vcsel_period']
            self.sensor.final_range_vcsel_period = self.sensor_config['final_range_vcsel_period']
            
            self.logger.debug("Configuration avancée du capteur appliquée")
            
        except Exception as e:
            self.logger.warning(f"Impossible d'appliquer la configuration avancée: {e}")
    
    def read_distance(self) -> Optional[float]:
        """
        Lit la distance mesurée par le capteur
        
        Returns:
            float: Distance en mm, None si erreur
        """
        if not self.sensor:
            self.logger.error("Capteur non initialisé")
            return None
        
        try:
            distance = max(0, self.sensor.range)

           
            self.logger.debug(f"Distance mesurée: {distance}mm")
            return distance
            
        except Exception as e:
            self.logger.error(f"Erreur lecture capteur: {e}")
            return None
    
    def detect_presence(self) -> bool:
        """
        Détecte si un obstacle est présent selon le seuil défini
        
        Returns:
            bool: True si un objet est détecté dans le seuil
        """
        distance = self.read_distance()
        
        if distance is None:
            self.logger.warning("Impossible de lire la distance")
            return False
        
        is_detected = distance <= self.threshold
        
        if is_detected:
            self.logger.info(f"👤 Présence détectée à {distance:.1f}mm (seuil: {self.threshold}mm)")
        else:
            self.logger.debug(f"Distance mesurée: {distance:.1f}mm (seuil: {self.threshold}mm)")
        
        return is_detected
    
    async def start_monitoring(self, 
                               callback: Callable, 
                               polling_interval: float = 0.1) -> bool:
        """
        Lance la surveillance continue du capteur dans un thread séparé
        
        Args:
            callback: Fonction appelée lors de changement d'état (peut être async)
            polling_interval: Intervalle entre les mesures en secondes
            
        Returns:
            bool: True si le monitoring a démarré avec succès, False sinon
        """

        if self.is_monitoring:
            self.logger.warning("Surveillance déjà active")
            return False
        
        self.logger.info("🔍 Démarrage de la surveillance du capteur VL53L0X...")
        
        # Lecture test pour vérifier que le capteur est opérationnel
        test_distance = self.read_distance()
        if test_distance is None:
            self.logger.error("❌ Impossible de lire la distance initiale - Le capteur est-il connecté?")
            return False
            
        self.logger.info(f"✅ Capteur VL53L0X opérationnel - Distance initiale: {test_distance:.1f}mm")
        
        # Capturer la boucle d'événements principale ici
        try:
            main_loop = asyncio.get_running_loop()
        except RuntimeError:
            self.logger.error("❌ Pas de boucle d'événements active pour le monitoring")
            return False
        
        self.is_monitoring = True
        self.stop_event.clear()
        
        def monitoring_loop():
            """Boucle de surveillance"""
            # previous_state = False
            # stable_count = 0
            # required_stable_readings = 2  # Nombre de lectures stables requises
            
            self.logger.info(f"👀 Surveillance active - Seuil: {self.threshold}mm, Intervalle: {polling_interval}s")
            self.logger.info(f"⏳ En attente de détection...")
            
            while not self.stop_event.is_set():
                try:
                    # Détecter la présence
                    current_state = self.detect_presence()

                    if current_state:
                        try:
                            # Utiliser la boucle principale capturée
                            self.logger.info("🎯 Présence détectée - Préparation du callback...")
                            
                            # Créer un événement pour suivre l'exécution
                            done_event = threading.Event()
                            error_message = None
                            
                            def done_callback(future):
                                try:
                                    future.result()  # Ceci va lever l'exception si le future a échoué
                                    self.logger.info("✅ Callback de présence exécuté avec succès")
                                except Exception as e:
                                    nonlocal error_message
                                    error_message = str(e)
                                finally:
                                    done_event.set()
                            
                            # Soumettre le callback à la boucle principale
                            future = asyncio.run_coroutine_threadsafe(callback(), main_loop)
                            future.add_done_callback(done_callback)
                            self.logger.info("✅ Callback soumis à la boucle principale")
                            
                            # Attendre que le callback soit terminé
                            if not done_event.wait(timeout=10.0):
                                self.logger.error("⏰ Timeout lors de l'exécution du callback")
                                self.logger.warning("⚠️ L'authentification a pris trop de temps")
                                future.cancel()
                            elif error_message:
                                self.logger.error(f"❌ Erreur dans le callback: {error_message}")
                            
                            # Pause après la détection pour éviter les détections multiples
                            time.sleep(2.0)
                            
                        except Exception as e:
                            self.logger.error(f"❌ Erreur dans le déclenchement du callback: {e}")
                            import traceback
                            self.logger.error(f"Stack trace: {traceback.format_exc()}")
                        
                        # Pause après une détection (qu'elle soit réussie ou non)
                        time.sleep(1.0)
                    time.sleep(polling_interval)
                        
                except Exception as e:
                    self.logger.error(f"❌ Erreur dans la boucle de surveillance: {e}")
                    time.sleep(polling_interval * 2)
            
            self.logger.info("Surveillance arrêtée")
        
        # Démarrer le thread de surveillance
        try:
            self.monitoring_thread = Thread(target=monitoring_loop, daemon=True)
            self.monitoring_thread.start()
            self.logger.info("🚀 Thread de surveillance démarré avec succès")
            return True
        except Exception as e:
            self.logger.error(f"❌ Erreur lors du démarrage du thread de surveillance: {e}")
            self.is_monitoring = False
            return False
    
    def stop_monitoring(self):
        """Arrête la surveillance continue"""
        if not self.is_monitoring:
            self.logger.warning("Surveillance déjà arrêtée")
            return
        
        self.logger.info("Arrêt de la surveillance...")
        self.stop_event.set()
        self.is_monitoring = False
        
        # Attendre l'arrêt du thread
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            self.monitoring_thread.join(timeout=2.0)
            if self.monitoring_thread.is_alive():
                self.logger.warning("Le thread de surveillance n'a pas pu être arrêté proprement")
    
    def calibrate_threshold(self, samples: int = 10) -> float:
        """
        Calibre automatiquement le seuil basé sur la distance ambiante
        
        Args:
            samples: Nombre d'échantillons pour le calibrage
            
        Returns:
            float: Nouveau seuil recommandé
        """
        self.logger.info(f"Calibrage du seuil avec {samples} échantillons...")
        
        distances = []
        for i in range(samples):
            distance = self.read_distance()
            if distance is not None:
                distances.append(distance)
            time.sleep(0.1)
        
        if not distances:
            self.logger.error("Aucune mesure valide pour le calibrage")
            return self.threshold
        
        # Calculer la distance moyenne et proposer un seuil
        avg_distance = sum(distances) / len(distances)
        min_distance = min(distances)
        max_distance = max(distances)
        
        # Seuil à 70% de la distance moyenne minimum
        recommended_threshold = min(distances) * 0.7
        
        self.logger.info(f"Distances mesurées - Min: {min_distance}mm, "
                        f"Max: {max_distance}mm, Moyenne: {avg_distance:.1f}mm")
        
        self.logger.info(f"Seuil recommandé: {recommended_threshold:.1f}mm")
        
        return recommended_threshold
    
    def set_threshold(self, new_threshold: float):
        """
        Modifie le seuil de détection
        
        Args:
            new_threshold: Nouveau seuil en mm
        """
        old_threshold = self.threshold
        self.threshold = new_threshold
        self.logger.info(f"Seuil modifié: {old_threshold}mm → {new_threshold}mm")
    
    
    async def cleanup(self):
        """Nettoie les ressources du capteur"""
        try:
            # First stop monitoring if running
            await self.stop_monitoring()
            
            # Clear references to release resources
            self.sensor = None
            self.logger.info("Capteur VL065X nettoyé proprement")
        except Exception as e:
            self.logger.error(f"Erreur lors du nettoyage du capteur: {e}")
    
    def __del__(self):
        """Destructeur pour nettoyer automatiquement"""
        if hasattr(self, 'is_monitoring') and hasattr(self, 'logger'):
            if self.is_monitoring:
                self.stop_event.set()
                self.is_monitoring = False
                try:
                    self.logger.info("Signal d'arrêt de surveillance envoyé")
                except:
                    pass  # Logger might be destroyed already