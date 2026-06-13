"""
Module de configuration du logging pour Edge Attendance Unit
Centralise la configuration des logs pour tous les composants
"""

import logging
import logging.handlers
import os
import sys
from datetime import datetime
from typing import Optional

from config import config

# Constantes
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
LOG_DIR = "logs"

def setup_logger(name: Optional[str] = None, 
                 level: int = logging.INFO,
                 console_level: Optional[int] = None,
                 file_level: Optional[int] = None) -> logging.Logger:
    """
    Configure et retourne un logger pour le module spécifié
    
    Args:
        name: Nom du module ou logger (None pour root logger)
        level: Niveau de logging global (default: INFO)
        console_level: Niveau de log pour la console (si None, utilise level)
        file_level: Niveau de log pour le fichier (si None, utilise level)
        
    Returns:
        Logger configuré
    """
    # Créer le dossier de logs s'il n'existe pas
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)
        
    # Nom du fichier de log avec date
    today = datetime.now().strftime("%Y-%m-%d")
    log_file = os.path.join(LOG_DIR, f"crec-presence-{today}.log")
    
    # Utiliser les niveaux spécifiés ou le niveau global
    console_level = console_level if console_level is not None else level
    file_level = file_level if file_level is not None else level
    
    # S'assurer que le niveau du logger est le plus permissif des deux
    logger_level = min(console_level, file_level)
    
    # Formatteur commun
    formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)
    
    # Logger principal
    logger = logging.getLogger(name)
    logger.setLevel(logger_level)
    
    # Éviter les gestionnaires en double
    if not logger.handlers:
        # Handler pour console
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.setLevel(console_level)
        logger.addHandler(console_handler)
        
        # Handler pour fichier (rotation quotidienne)
        file_handler = logging.handlers.TimedRotatingFileHandler(
            log_file, 
            when="midnight",
            backupCount=30  # Garder 30 jours de logs
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(file_level)
        logger.addHandler(file_handler)
        
        # Afficher un message sur l'emplacement du fichier de log si c'est un nouveau logger
        # Mais uniquement dans la console, pour ne pas polluer le fichier de log lui-même
        if name:  # Ne pas afficher ce message pour le root logger
            console_handler.emit(
                logging.LogRecord(
                    name=name,
                    level=logging.INFO,
                    pathname="",
                    lineno=0,
                    msg=f"🔍 Logs écrits dans le fichier: {os.path.abspath(log_file)}",
                    args=(),
                    exc_info=None
                )
            )
    
    return logger

# Désactiver les logs excessifs des bibliothèques tierces
def silence_noisy_loggers():
    """Réduit le niveau de log des bibliothèques verbeuses"""
    loggers_to_silence = [
        "urllib3.connectionpool",
        "PIL.Image",
        "paho.mqtt.client",
        "chromadb.api",
        "insightface"
    ]
    
    for logger_name in loggers_to_silence:
        logging.getLogger(logger_name).setLevel(logging.WARNING)

# Configuration au chargement du module
silence_noisy_loggers()