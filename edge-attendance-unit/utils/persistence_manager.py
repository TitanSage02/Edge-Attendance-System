"""
Gestionnaire de persistance pour les événements de présence
Assure la persistance des données en cas de déconnexion réseau
"""

import asyncio
import json
import logging
import os
import time
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable
import aiofiles
import aiofiles.os

from utils.logger import setup_logger

# Configuration du logger
logger = setup_logger("persistence_manager", level=logging.INFO)

class PersistenceManager:
    """
    Gestionnaire de persistance pour les événements de présence
    - Stockage local des événements en cas de déconnexion
    - Réémission automatique lors de la reconnexion
    - Gestion des files d'attente par type d'événement
    """
    
    def __init__(self, storage_dir: str = "data/queue"):
        """
        Initialise le gestionnaire de persistance
        
        Args:
            storage_dir: Répertoire de stockage des files d'attente
        """
        self.storage_dir = storage_dir
        self.queues = {
            "presence": [],
            "logs": [],
            "status": []
        }
        self.is_processing = False
        self.processing_task = None
        self.callbacks = {
            "presence": None,
            "logs": None,
            "status": None
        }
        self.reconnected_event = asyncio.Event()
        
        # Créer le répertoire de stockage s'il n'existe pas
        os.makedirs(self.storage_dir, exist_ok=True)
        
        logger.info(f"Gestionnaire de persistance initialisé ({storage_dir})")
    
    async def initialize(self):
        """
        Initialise le gestionnaire et charge les données persistées
        """
        logger.info("Chargement des données persistées...")
        await self._load_persisted_data()
    
    async def _load_persisted_data(self):
        """
        Charge les données persistées depuis les fichiers locaux
        """
        try:
            for queue_type in self.queues:
                queue_file = os.path.join(self.storage_dir, f"{queue_type}_queue.json")
                if os.path.exists(queue_file):
                    async with aiofiles.open(queue_file, "r") as f:
                        content = await f.read()
                        data = json.loads(content)
                        self.queues[queue_type] = data
                        logger.info(f"Chargé {len(data)} événements {queue_type} depuis {queue_file}")
                else:
                    logger.debug(f"Aucun fichier de queue pour {queue_type}")
        except Exception as e:
            logger.error(f"Erreur lors du chargement des données persistées: {e}")
    
    async def _save_queue(self, queue_type: str):
        """
        Sauvegarde une file d'attente sur le disque
        
        Args:
            queue_type: Type de file d'attente (presence, logs, status)
        """
        try:
            queue_file = os.path.join(self.storage_dir, f"{queue_type}_queue.json")
            async with aiofiles.open(queue_file, "w") as f:
                await f.write(json.dumps(self.queues[queue_type], default=self._json_serializer))
                
            logger.debug(f"File {queue_type} sauvegardée ({len(self.queues[queue_type])} événements)")
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde de la file {queue_type}: {e}")
    
    def _json_serializer(self, obj):
        """
        Sérialise les objets pour JSON
        
        Args:
            obj: Objet à sérialiser
            
        Returns:
            Version sérialisable de l'objet
        """
        if isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(f"Type non sérialisable: {type(obj)}")
    
    async def enqueue(self, queue_type: str, data: Dict[str, Any]) -> bool:
        """
        Ajoute un événement à une file d'attente
        
        Args:
            queue_type: Type d'événement (presence, logs, status)
            data: Données de l'événement
            
        Returns:
            bool: True si l'événement a été ajouté avec succès
        """
        try:
            # Ajouter un timestamp s'il n'y en a pas
            if "timestamp" not in data:
                data["timestamp"] = datetime.now().isoformat()
                
            # Ajouter à la file
            self.queues[queue_type].append(data)
            
            # Sauvegarder la file
            await self._save_queue(queue_type)
            
            logger.debug(f"Événement ajouté à la file {queue_type} ({len(self.queues[queue_type])} total)")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de l'ajout à la file {queue_type}: {e}")
            return False
    
    def register_callback(self, queue_type: str, callback: Callable[[Dict[str, Any]], None]):
        """
        Enregistre un callback pour traiter les événements d'une file
        
        Args:
            queue_type: Type d'événement (presence, logs, status)
            callback: Fonction à appeler pour traiter l'événement
        """
        self.callbacks[queue_type] = callback
        logger.debug(f"Callback enregistré pour la file {queue_type}")
    
    async def on_reconnection(self):
        """
        À appeler lorsque la connexion est rétablie pour traiter les files d'attente
        """
        logger.info("Connexion rétablie, traitement des files d'attente")
        self.reconnected_event.set()
        
        # Démarrer le traitement des files en arrière-plan
        if self.processing_task is None or self.processing_task.done():
            self.processing_task = asyncio.create_task(self._process_queues())
    
    async def _process_queues(self):
        """
        Traite les événements dans les files d'attente
        """
        if self.is_processing:
            logger.debug("Traitement des files déjà en cours")
            return
        
        self.is_processing = True
        
        try:
            for queue_type, callback in self.callbacks.items():
                if callback is None:
                    logger.warning(f"Pas de callback pour {queue_type}, ignoré")
                    continue
                
                queue = self.queues[queue_type].copy()
                if queue:
                    logger.info(f"Traitement de {len(queue)} événements {queue_type}")
                    
                    # Traiter les événements du plus ancien au plus récent
                    for event in queue:
                        try:
                            # Appeler le callback pour traiter l'événement
                            await callback(event)
                            
                            # Retirer l'événement traité de la file
                            if self.queues[queue_type]:
                                self.queues[queue_type].pop(0)
                            
                            # Sauvegarder la file périodiquement
                            if len(queue) > 0 and len(queue) % 10 == 0:
                                await self._save_queue(queue_type)
                            
                        except Exception as e:
                            logger.error(f"Erreur lors du traitement d'un événement {queue_type}: {e}")
                            # On arrête le traitement de cette file en cas d'erreur
                            break
                    
                    # Sauvegarder l'état final de la file
                    await self._save_queue(queue_type)
                else:
                    logger.debug(f"File {queue_type} vide")
            
        except Exception as e:
            logger.error(f"Erreur lors du traitement des files: {e}")
            
        finally:
            self.is_processing = False
            self.reconnected_event.clear()
    
    async def start_background_processing(self, interval: int = 60):
        """
        Démarre un traitement périodique des files d'attente en arrière-plan
        
        Args:
            interval: Intervalle en secondes entre les tentatives de traitement
        """
        logger.info(f"Démarrage du traitement périodique (intervalle: {interval}s)")
        
        # Vérifier si nous sommes dans une boucle asyncio
        try:
            loop = asyncio.get_running_loop()
            logger.info("✅ Boucle d'événements active détectée pour le traitement périodique")
        except RuntimeError:
            logger.error("❌ Pas de boucle d'événements asyncio active pour le traitement périodique")
            logger.warning("Le traitement périodique ne sera pas démarré - ce n'est pas critique")
            return
        
        try:
            while True:
                try:
                    # Attendre l'intervalle ou un signal de reconnexion
                    try:
                        await asyncio.wait_for(self.reconnected_event.wait(), timeout=interval)
                    except asyncio.TimeoutError:
                        pass
                    
                    # Traiter les files
                    if not self.is_processing:
                        await self._process_queues()
                        
                except asyncio.CancelledError:
                    logger.info("Traitement périodique annulé")
                    break
                    
                except Exception as e:
                    import traceback
                    logger.error(f"Erreur dans le traitement périodique: {e}")
                    logger.error(f"Détails: {traceback.format_exc()}")
                    await asyncio.sleep(5)  # Attendre un peu en cas d'erreur
        except Exception as e:
            import traceback
            logger.error(f"Erreur critique dans le traitement périodique: {e}")
            logger.error(f"Détails: {traceback.format_exc()}")
    
    def get_queue_sizes(self) -> Dict[str, int]:
        """
        Renvoie la taille actuelle de chaque file d'attente
        
        Returns:
            Dict[str, int]: Nombre d'événements dans chaque file
        """
        return {queue_type: len(queue) for queue_type, queue in self.queues.items()}
