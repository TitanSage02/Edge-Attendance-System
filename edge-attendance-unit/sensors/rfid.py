###################################
# RFID sensor module 
###################################

import time
import logging
from utils.logger import setup_logger
import threading
from typing import Optional, Callable, Dict, Any
import spidev
from mfrc522 import SimpleMFRC522
import RPi.GPIO as GPIO
from threading import Event, Thread
import hashlib
import asyncio
import atexit

from config import config

class RFIDController:
    """
    Contrôleur pour lecteur RFID MFRC522
    Gestion de la lecture de cartes et mapping avec les étudiants
    """
    
    def __init__(self, 
                 spi_bus: int = 0, 
                 spi_device: int = 0, 
                 rst_pin = config.RFID_PIN):
        
        """
        Initialise le contrôleur RFID
        
        Args:
            spi_bus: Bus SPI
            spi_device: Device SPI
            rst_pin: Pin GPIO pour le reset 
        """
        self.logger = setup_logger(
            name="rfid_reader",
            level=logging.INFO,
            console_level=logging.INFO
        )
        
        self.spi_bus = spi_bus
        self.spi_device = spi_device
        self.rst_pin = rst_pin
        self.reader = None
        self.is_active = True
        self.is_reading = False
        self.reading_thread = None

        self.memory = {}  # Dictionnaire pour stocker les données des cartes [card_id: student_id] (à construire dans communication avec la base de données)
            
        self.stop_event = Event()
        
        # Configuration du lecteur
        self.reader_config = {
            'read_timeout': 5.0,  # Timeout en secondes
            'retry_attempts': 3,
            'card_present_delay': 0.1  # Délai entre les vérifications
        }
        
        # Cache des cartes lues récemment 
        self.recent_cards = {}
        self.cache_duration = 2.0  # Durée du cache en secondes
        
        # Statistics
        self.stats = {
            'successful_reads': 0,
            'failed_reads': 0,
            'total_attempts': 0
        }
        
        # Pour éviter les lectures répétées
        self._last_read_uid = None
        self._last_read_time = 0
        
        # Configurer le logger pour filtrer les erreurs d'authentification
        self._configure_logger()
        
        self._initialize_reader()
    
    def _initialize_reader(self):
        """Initialise le lecteur RFID MFRC522"""
        try:
            # Configuration GPIO
            if GPIO.getmode() is None:
                GPIO.setmode(GPIO.BOARD)
            GPIO.setwarnings(False)
            
            # Initialiser le lecteur MFRC522
            self.reader = SimpleMFRC522()
            
            # Test de lecture rapide pour vérifier la connexion
            self._test_reader_connection()
            
            self.logger.info("Lecteur RFID MFRC522 initialisé avec succès")
            
        except Exception as e:
            self.logger.error(f"Erreur initialisation RFID: {e}")
            raise RuntimeError(f"Impossible d'initialiser le lecteur RFID: {e}")
    
    def _test_reader_connection(self):
        """Test rapide de la connexion au lecteur"""
        try:
            # Test non-bloquant pour vérifier si le lecteur répond
            import signal
            
            def timeout_handler(signum, frame):
                raise TimeoutError("Test de connexion timeout")
            
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(1)  # 1 seconde de timeout
            
            try:
                # Tentative de lecture très courte
                self.reader.read_no_block()
                signal.alarm(0)  # Annuler l'alarme
            except TimeoutError:
                signal.alarm(0)
                raise RuntimeError("Lecteur RFID ne répond pas")
            except Exception as e:
                signal.alarm(0)
                # Filtrer les erreurs d'authentification qui sont normales lors du test
                if "AUTH ERROR" in str(e):
                    self.logger.debug("Test de connexion RFID: Erreur d'authentification normale détectée")
                else:
                    self.logger.debug(f"Test de connexion RFID: {e}")
                pass
                
        except Exception as e:
            self.logger.warning(f"Test de connexion RFID: {e}")
    
    
    def read_card(self, timeout: float = None) -> Optional[str]:
        """
        Lit une carte RFID
        
        Args:
            timeout: Timeout en secondes (par défaut utilise la config)
            
        Returns:
            str: UID de la carte au format hexadécimal tronqué ou None si échec
        """
        try:
            self.logger.debug("Lecture de carte RFID en cours...")
            
            # Lecture avec timeout
            start_time = time.time()
            card_id = None
            card_text = None
            
            while time.time() - start_time < timeout:
                try:
                    # Tentative de lecture non-bloquante
                    card_id, card_text = self.reader.read_no_block()
                    if card_id:
                        break
                 
                    time.sleep(self.reader_config['card_present_delay'])

                except Exception as read_error:
                    # Filtrer les erreurs d'authentification qui sont courantes
                    if "AUTH ERROR" not in str(read_error):
                        self.logger.debug(f"Erreur de lecture: {read_error}")
                    
                    # Continuer à essayer jusqu'au timeout
                    time.sleep(self.reader_config['card_present_delay'])
                    continue
            
            if not card_id:
                self.logger.debug("Aucune carte détectée dans le délai imparti")
                self.stats['failed_reads'] += 1
                return None

            # Convertir en hex tronqué
            uid_hex = self._format_uid_hex(card_id)
            
            # Vérifier le cache pour éviter les doubles lectures
            if self._is_recent_card(uid_hex):
                self.logger.debug(f"Carte déjà lue récemment, ignorée: {uid_hex}")
                return None
            
            # Ajouter au cache
            self._add_to_cache(uid_hex)

            self.logger.info(f"Carte RFID lue: {uid_hex}")
            return uid_hex

        except Exception as e:
            self.stats['failed_reads'] += 1
            self.logger.error(f"Erreur lors de la lecture RFID: {e}")
            return None
    
   
    
    def _is_recent_card(self, card_id: str) -> bool:
        """Vérifie si la carte a été lue récemment"""
        current_time = time.time()
        
        # Nettoyer le cache des anciennes entrées
        expired_cards = [
            cid for cid, timestamp in self.recent_cards.items()
            if current_time - timestamp > self.cache_duration
        ]
        for cid in expired_cards:
            del self.recent_cards[cid]
        
        return card_id in self.recent_cards
    
    def _add_to_cache(self, card_id: str):
        """Ajoute une carte au cache"""
        self.recent_cards[card_id] = time.time()

    def get_student_id(self, card_id: str) -> Optional[str]:
        """
        Récupère l'ID étudiant depuis les données de carte
        Cette méthode doit être adaptée selon votre logique de mapping
        
        Args:
            card_id: Données de la carte RFID
            
        Returns:
            str: ID de l'étudiant ou None si non trouvé
        """
        if not card_id:
            return None
        
        # extraire le student_id d'un dictionnaire de données
        student_id = self.memory.get(card_id, None)

        if not student_id:
            self.logger.warning("Aucun ID étudiant trouvé")
            return None

        self.logger.debug(f"Student ID mappé: {student_id}")
        return student_id
    
    def start_continuous_reading(self, callback: Callable[[Dict[str, Any]], None]):
        """
        Démarre la lecture continue de cartes
        
        Args:
            callback: Fonction appelée à chaque carte lue
        """
        if self.is_reading:
            self.logger.warning("Lecture continue déjà active")
            return
     
        self.is_reading = True
        self.stop_event.clear()
        
        def reading_loop():
            """Boucle de lecture continue"""
            self.logger.info("Lecture continue RFID démarrée")
            
            while not self.stop_event.is_set():
                try:
                    card_id = self.read_card(timeout=1.0)
                    if card_id:
                        try:
                            callback(card_id)
                        except Exception as e:
                            self.logger.error(f"Erreur dans le callback RFID: {e}")
                    
                except Exception as e:
                    self.logger.error(f"Erreur dans la boucle de lecture RFID: {e}")
                    time.sleep(0.5)
            
            self.logger.info("Lecture continue RFID arrêtée")
        
        # Démarrer le thread de lecture
        self.reading_thread = Thread(target=reading_loop, daemon=True)
        self.reading_thread.start()
    
    def stop_reading(self):
        """Arrête la lecture continue"""
        if not self.is_reading:
            return
        
        self.logger.info("Arrêt de la lecture continue RFID...")
        self.stop_event.set()
        self.is_reading = False
        
        # Attendre l'arrêt du thread
        if self.reading_thread and self.reading_thread.is_alive():
            self.reading_thread.join(timeout=2.0)
            if self.reading_thread.is_alive():
                self.logger.warning("Le thread de lecture RFID n'a pas pu être arrêté proprement")
    

    def cleanup(self):
        """Nettoie les ressources du lecteur RFID"""
        try:
            self.stop_reading()
            
            # Don't call GPIO.cleanup() directly here as it will be handled in the main cleanup
            # to avoid multiple GPIO cleanup calls that can cause segfaults
            
            self.is_active = False
            self.logger.info("Ressources RFID nettoyées")
            
        except Exception as e:
            self.logger.error(f"Erreur lors du nettoyage RFID: {e}")
    
    def __del__(self):
        """Destructeur pour nettoyer automatiquement"""
        if hasattr(self, 'is_active') and hasattr(self, 'logger') and self.is_active:
            try:
                self.stop_reading()
                self.is_active = False
                if hasattr(self, 'logger'):
                    self.logger.info("RFID cleanup appelé par destructeur")
            except Exception as e:
                if hasattr(self, 'logger'):
                    self.logger.error(f"Erreur lors du nettoyage RFID dans le destructeur: {e}")
    
    async def read_async(self, timeout: float = 5.0) -> Optional[str]:
        """
        Lecture asynchrone d'une carte RFID
        
        Args:
            timeout: Délai maximum d'attente en secondes
            
        Returns:
            str: UID de la carte au format hexadécimal tronqué ou None si timeout/erreur
        """
        if not self.reader:
            self.logger.error("Lecteur RFID non initialisé")
            return None
            
        start_time = time.time()
        
        try:
            self.logger.info("Attente de présentation d'une carte RFID...")
            
            # Boucle de lecture non-bloquante avec timeout
            while (time.time() - start_time) < timeout:
                try:
                    # Lecture non-bloquante
                    uid, text = self.reader.read_no_block()
                    
                    # Si une carte est détectée
                    if uid is not None:
                        # Convertir en format hex tronqué
                        uid_hex = self._format_uid_hex(uid)
                        
                        # Vérifier le cache des lectures récentes
                        if self._is_recent_card(uid_hex):
                            self.logger.debug(f"Ignoré lecture répétée de carte: {uid_hex}")
                            return None
                            
                        # Mettre en cache
                        self._add_to_cache(uid_hex)
                        
                        self.logger.info(f"Carte RFID lue: {uid_hex}")
                        return uid_hex
                        
                except Exception as e:
                    # Filtrer les erreurs d'authentification qui sont courantes
                    if "AUTH ERROR" not in str(e):
                        self.logger.debug(f"Tentative de lecture RFID: {e}")
                    
                # Attente courte avant la prochaine tentative
                await asyncio.sleep(0.1)
                
            # Timeout atteint sans lecture
            self.logger.debug("Timeout de lecture RFID atteint")
            return None
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la lecture RFID: {e}")
            return None
        
    def _format_uid_hex(self, uid) -> str:
        """
        Convertit un UID RFID en format hexadécimal standard (tronqué des 2 derniers caractères)
        
        Args:
            uid: L'UID RFID (int ou str)
            
        Returns:
            str: UID formaté en hexadécimal sans les 2 derniers caractères
        """
        try:
            # Si c'est déjà au format hex tronqué, le retourner tel quel
            if isinstance(uid, str) and all(c in '0123456789ABCDEFabcdef' for c in uid):
                formatted = uid.upper()
                return formatted[:-2] if len(formatted) > 2 else formatted
            
            # Convertir en entier si c'est une chaîne
            uid_int = int(str(uid).strip())
            
            # Formater en hexadécimal (majuscules, sans préfixe '0x')
            uid_hex = format(uid_int, 'X')
            
            # Ajouter des zéros au début si nécessaire pour avoir une longueur paire
            if len(uid_hex) % 2 != 0:
                uid_hex = '0' + uid_hex
                
            # Supprimer les 2 derniers caractères si la longueur le permet
            if len(uid_hex) > 2:
                return uid_hex[:-2]
            
            self.logger.warning(f"UID hexadécimal trop court pour tronquer: {uid_hex}")
            return uid_hex
                
        except (ValueError, TypeError) as e:
            self.logger.error(f"Impossible de formater l'UID en hexadécimal: {e}")
            if isinstance(uid, str):
                return uid.upper()  # Retourner la chaîne en majuscules si impossible de convertir
            return str(uid)
        
    def _configure_logger(self):
        """Configure le logger pour filtrer les erreurs d'authentification trop verboses"""
        # Configuration du logger pour le module MFRC522
        mfrc522_logger = logging.getLogger('mfrc522Logger')
        
        # Définir un niveau plus élevé pour réduire la verbosité des erreurs d'authentification
        # qui sont courantes et généralement non critiques
        mfrc522_logger.setLevel(logging.CRITICAL)
        
        class AuthErrorFilter(logging.Filter):
            """Filtre les erreurs d'authentification RFID courantes"""
            def filter(self, record):
                # Rejette les messages d'erreur d'authentification courants
                if "AUTH ERROR" in record.getMessage():
                    return False
                return True
                
        # Appliquer le filtre au logger
        mfrc522_logger.addFilter(AuthErrorFilter())
        self.logger.info("Logger MFRC522 configuré pour filtrer les erreurs d'authentification courantes")