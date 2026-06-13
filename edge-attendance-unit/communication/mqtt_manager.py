"""
Client MQTT pour Edge Attendance System
"""
from typing import Dict, Any, Callable, Optional, List, Tuple
import json
import time
import asyncio
import ssl
import os
import sys
from datetime import datetime, timedelta

import paho.mqtt.client as mqtt
from config import config

# Vérification de la compatibilité avec les versions de paho-mqtt
try:
    # Tenter d'utiliser la nouvelle API (paho-mqtt >= 2.0)
    MQTT_API_VERSION = mqtt.CallbackAPIVersion.VERSION2
    USE_NEW_API = True
except AttributeError:
    # Fallback pour les anciennes versions
    MQTT_API_VERSION = None
    USE_NEW_API = False

# Import des schémas standardisés
from schemas.schema import (
    MQTTMessage,
    PresenceBase,
    StatusMQTT,
    LogMQTT,
    CommandMQTT,
    ConfigUpdateMQTT,
    MQTTTopics
)

# Import du gestionnaire de persistance
from utils.persistence_manager import PersistenceManager

import logging
from utils.logger import setup_logger

# Configuration du logger spécifique pour MQTT
logger = setup_logger("mqtt_manager", logging.INFO)
logger.info("MQTT Manager initialisé")


class DateTimeEncoder(json.JSONEncoder):
    """Encodeur JSON personnalisé pour gérer les objets datetime et autres types complexes"""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        
        # Gestion des événements asyncio
        elif hasattr(obj, '__class__') and 'Event' in str(obj.__class__):
            return f"<Event object at {id(obj)}>"
        
        # Gestion des objets non sérialisables
        elif hasattr(obj, '__dict__'):
            try:
                return obj.__dict__
            except:
                return str(obj)
        
        # Fallback pour autres types
        try:
            return super().default(obj)
        except TypeError:
            return str(obj)


# Utilisation des topics standardisés depuis MQTTTopics
TOPIC_CONFIG = MQTTTopics.CONFIG
TOPIC_STATUS = MQTTTopics.status(config.MODULE_ID)
TOPIC_LOGS = MQTTTopics.logs(config.MODULE_ID)
TOPIC_PRESENCE = MQTTTopics.presence(config.MODULE_ID)
TOPIC_COMMAND = MQTTTopics.command(config.MODULE_ID)

class MQTTManager:
    """Client MQTT pour la communication avec le backend Edge Attendance System"""
    
    def __init__(self, test_mode=False):
        """Initialise le client MQTT"""
        self.client_id = f"crec_module_{config.MODULE_ID}_{int(time.time())}"
        
        # Déterminer le mode de connexion (local vs prod)
        self.connection_mode = self._determine_connection_mode()
        
        # Configuration du transport selon le mode
        # Configuration du client MQTT avec compatibilité des versions
        if self.connection_mode == "prod":
            if USE_NEW_API:
                self.client = mqtt.Client(
                    client_id=self.client_id, 
                    transport="websockets", 
                    protocol=mqtt.MQTTv5,
                    callback_api_version=MQTT_API_VERSION
                )
            else:
                self.client = mqtt.Client(
                    client_id=self.client_id, 
                    transport="websockets", 
                    protocol=mqtt.MQTTv5
                )
            logger.info("🌐 Mode PRODUCTION: Transport WebSocket activé")
        else:
            if USE_NEW_API:
                self.client = mqtt.Client(
                    client_id=self.client_id, 
                    protocol=mqtt.MQTTv5,
                    callback_api_version=MQTT_API_VERSION
                )
            else:
                self.client = mqtt.Client(
                    client_id=self.client_id, 
                    protocol=mqtt.MQTTv5
                )
            logger.info("🏠 Mode LOCAL: Transport natif MQTT")
        
        self._test_mode = test_mode or 'PYTEST_CURRENT_TEST' in os.environ
        
        # Callbacks asynchrones
        self.on_message_callbacks = {}
        self.on_connect_callbacks = []
        self.on_disconnect_callbacks = []
        
        # État du client
        self.connected = asyncio.Event()
        self.connecting = False
        self.subscribed_topics = set()
        self.message_buffer = []  # Buffer simple pour les messages en attente
        
        # Configuration selon le mode
        self._configure_connection_parameters()

        # Stockage des détections et statuts par étudiant
        self.presence_status = {}  # {student_id: {"timestamp": datetime, "status": bool}}
        
        # Configuration de l'authentification
        self.mqtt_user = config.MQTT_USERNAME
        self.mqtt_password = config.MQTT_PASSWORD
        
        # DÉSACTIVÉ TEMPORAIREMENT: Persistance complexe
        # self.persistence_manager = PersistenceManager()
        
        if self.mqtt_user and self.mqtt_password:
            self.client.username_pw_set(self.mqtt_user, self.mqtt_password)
            logger.info(f"Authentification MQTT configurée pour l'utilisateur: {self.mqtt_user}")
        else:
            logger.info("MQTT sans authentification (mode local)")
          
        # Configuration TLS si activée
        self._tls_configured = False
        if self.use_tls:
            try:
                context = self._get_ssl_context()
                self.client.tls_set_context(context)
                self._tls_configured = True
                logger.info("🔐 Configuration TLS activée")
                
            except Exception as e:
                logger.error(f"❌ Erreur TLS: {e}")
                if getattr(config, 'USE_TLS', False):
                    raise RuntimeError("TLS requis pour MQTT mais configuration impossible")
                else:
                    logger.warning("⚠️  TLS non disponible, connexion non sécurisée autorisée par la config")
                    self.use_tls = False
        
        # Configuration des callbacks
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message
        
        # Dernier temps d'activité pour la gestion des watchdogs
        self.last_activity = time.time()
        
        logger.info(f"Client MQTT initialisé : {self.client_id} (Mode: {self.connection_mode})")
    
    def _determine_connection_mode(self) -> str:
        """
        Détermine le mode de connexion (local ou prod) basé sur la configuration
        
        Returns:
            str: "local" ou "prod"
        """
        # Mode forcé dans la configuration
        forced_mode = getattr(config, 'MQTT_CONNECTION_MODE', 'auto')
        if forced_mode in ['local', 'prod']:
            logger.info(f"Mode forcé via config: {forced_mode}")
            return forced_mode
        
        # Détection automatique
        broker = getattr(config, 'MQTT_BROKER', '')
        use_websockets = getattr(config, 'MQTT_USE_WEBSOCKETS', False)
        
        # Mode prod détecté si:
        # - WebSockets explicitement activé
        # - Broker contient un nom de domaine (pas IP locale)
        # - Port WSS configuré différent de 443
        if (use_websockets or 
            self._is_production_domain(broker) or
            getattr(config, 'MQTT_WSS_PORT', 443) != 443):
            logger.info(f"Mode PROD détecté: broker={broker}, ws={use_websockets}")
            return "prod"
        
        logger.info(f"Mode LOCAL par défaut: broker={broker}")
        return "local"
    
    def _is_production_domain(self, broker: str) -> bool:
        """
        Vérifie si le broker utilise un domaine de production
        
        Args:
            broker: Adresse du broker
            
        Returns:
            bool: True si c'est un domaine externe (production)
        """
        if not broker:
            return False
            
        # Exclure les IPs et domaines locaux
        local_patterns = [
            '192.168.', '10.', '172.', '127.', 'localhost', 
            '.local', '.lan', '.home'
        ]
        broker_lower = broker.lower()
        
        if any(broker_lower.startswith(pattern) or pattern in broker_lower 
               for pattern in local_patterns):
            return False
            
        # Si ça contient un point et ce n'est pas une IP locale, 
        # c'est probablement un domaine externe
        if '.' in broker and not self._is_ip_address(broker):
            return True
            
        return False
    
    def _is_ip_address(self, address: str) -> bool:
        """
        Vérifie si l'adresse est une adresse IP
        
        Args:
            address: Adresse à vérifier
            
        Returns:
            bool: True si c'est une adresse IP
        """
        import re
        ip_pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
        return bool(re.match(ip_pattern, address))
    
    def _configure_connection_parameters(self):
        """
        Configure les paramètres de connexion selon le mode
        """
        self.broker = config.MQTT_BROKER
        
        if self.connection_mode == "prod":
            # Mode production: WebSocket sécurisé via Cloudflare
            self.port = getattr(config, 'MQTT_WSS_PORT', 443)
            self.use_tls = True
            logger.info(f"🌐 Mode PROD: {self.broker}:{self.port} (WebSocket + TLS)")
        else:
            # Mode local: MQTT natif
            self.port = getattr(config, 'MQTT_PORT', 1883)
            self.use_tls = getattr(config, 'USE_TLS', False)
            
            # Utiliser le port TLS si configuré en local
            if self.use_tls and hasattr(config, 'MQTT_TLS_PORT'):
                self.port = config.MQTT_TLS_PORT
                
            logger.info(f"🏠 Mode LOCAL: {self.broker}:{self.port} (TLS: {self.use_tls})")
        
    def _get_ssl_context(self) -> ssl.SSLContext:
        """
        Crée un contexte SSL pour la connexion TLS
        
        Returns:
            Contexte SSL configuré
        """
        context = ssl.create_default_context()
        
        # Si un certificat CA personnalisé est fourni
        ca_cert = config.mqtt_ca_cert
        if ca_cert and os.path.exists(ca_cert):
            context.load_verify_locations(cafile=ca_cert)
            logger.info(f"🔐 Certificat CA personnalisé chargé: {ca_cert}")
        else:
            logger.info("🔐 Utilisation des certificats système (Let's Encrypt)")
        
        # Mode insecure pour développement (ignore la vérification du certificat)
        if hasattr(config, 'MQTT_INSECURE_TLS') and config.MQTT_INSECURE_TLS:
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            logger.warning("⚠️  Mode TLS insécurisé activé (développement uniquement)")
            
        # Certificats client (optionnel pour authentification mutuelle)
        client_cert = config.mqtt_client_cert
        client_key = config.mqtt_client_key
        if client_cert and client_key and os.path.exists(client_cert) and os.path.exists(client_key):
            context.load_cert_chain(certfile=client_cert, keyfile=client_key)
            logger.info("🔐 Certificats client chargés pour authentification mutuelle")
        
        return context

    def _on_connect(self, client : mqtt.Client, userdata, flags, rc, properties=None):
        """
        Callback appelé lors de la connexion au broker MQTT - VERSION SIMPLIFIÉE
        """
        if rc == mqtt.CONNACK_ACCEPTED:
            logger.info("✅ Connecté au broker MQTT")
            self.connected.set()
            self.connecting = False
            self.last_activity = time.time()
            
            # Réabonner aux topics
            for topic in self.subscribed_topics:
                client.subscribe(topic, qos=1)
                logger.debug(f"Réabonnement au topic: {topic}")
            
            # Envoyer les messages en attente
            while self.message_buffer:
                topic, payload, qos, retain = self.message_buffer.pop(0)
                client.publish(topic, payload, qos=qos, retain=retain)
                logger.debug(f"Envoi du message en attente: {topic}")
            
            logger.info("🚀 MQTT prêt pour les publications")
        else:
            logger.error(f"❌ Échec de connexion au broker MQTT, code: {rc}")
            self.connected.clear()
            self.connecting = False
    
    def _on_disconnect(self, client, userdata, rc, properties=None):
        """
        Callback appelé lors de la déconnexion du broker MQTT
        
        Args:
            client: Le client MQTT
            userdata: Données utilisateur (non utilisé)
            rc: Code de retour
            properties: Propriétés MQTTv5 (si applicable)
        """
        self.connected.clear()
        if rc == 0:
            logger.info("Déconnexion normale du broker MQTT")
        else:
            logger.warning(f"⚠️ Déconnexion inattendue du broker MQTT, code: {rc}")
            
            # Planifier une reconnexion de manière thread-safe
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(self._reconnect())
                logger.info("✅ Tâche de reconnexion planifiée")
            except RuntimeError:
                # Pas de boucle d'événements active, créer une tâche séparée
                logger.warning("⚠️ Pas de boucle d'événements pour la reconnexion immédiate")
                logger.info("Tentative de création d'une nouvelle boucle pour la reconnexion...")
                
                # Créer un thread pour gérer la reconnexion
                def reconnect_thread():
                    try:
                        asyncio.run(self._reconnect())
                    except Exception as e:
                        logger.error(f"❌ Erreur lors de la reconnexion dans un thread séparé: {e}")
                
                import threading
                threading.Thread(target=reconnect_thread, daemon=True).start()
                logger.info("✅ Thread de reconnexion démarré")
        
        # Exécuter les callbacks asynchrones
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self._run_disconnect_callbacks(rc))
            logger.debug("✅ Callbacks de déconnexion planifiés")
        except RuntimeError:
            # Pas de boucle d'événements active
            logger.warning("⚠️ Pas de boucle d'événements pour les callbacks de déconnexion")
    
    def _on_message(self, client, userdata, msg : mqtt.MQTTMessage):
        """
        Callback appelé lors de la réception d'un message
        
        Args:
            client: Le client MQTT
            userdata: Données utilisateur (non utilisé)
            msg: Le message reçu
        """
        self.last_activity = time.time()
        try:
            payload_str = msg.payload.decode('utf-8')
            payload = json.loads(payload_str)
            
            logger.debug(f"Message reçu sur {msg.topic}: {payload_str[:50]}...")
            
            # Exécuter les callbacks pour ce topic
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(self._dispatch_message(msg.topic, payload))
                logger.debug(f"✅ Tâche de dispatch créée pour le message sur {msg.topic}")
            except RuntimeError:
                # Pas de boucle d'événements active, traiter directement
                logger.warning(f"⚠️ Pas de boucle d'événements pour le message sur {msg.topic}, création d'une nouvelle boucle")
                try:
                    # Créer une nouvelle boucle d'événements pour ce message
                    asyncio.run(self._dispatch_message(msg.topic, payload))
                    logger.debug(f"✅ Message sur {msg.topic} traité dans une nouvelle boucle")
                except Exception as e:
                    import traceback
                    logger.error(f"❌ Erreur lors du traitement du message dans une nouvelle boucle: {e}")
                    logger.error(f"Détails: {traceback.format_exc()}")
        
        except json.JSONDecodeError:
            logger.warning(f"⚠️ Message reçu sur {msg.topic} n'est pas un JSON valide")
       
        except Exception as e:
            import traceback
            logger.error(f"❌ Erreur lors du traitement du message MQTT: {e}")
            logger.error(f"Détails: {traceback.format_exc()}")
    
    async def _dispatch_message(self, topic: str, payload: Dict[str, Any]):
        """
        Distribue un message aux callbacks enregistrés
        
        Args:
            topic: Le topic du message
            payload: Le contenu du message
        """
        # Exact match
        if topic in self.on_message_callbacks:
            for callback in self.on_message_callbacks[topic]:
                try:
                    await callback(topic, payload)
                except Exception as e:
                    logger.error(f"Erreur dans le callback pour {topic}: {e}")
        
        # Wildcard matches
        for registered_topic, callbacks in self.on_message_callbacks.items():
            if self._topic_matches_subscription(registered_topic, topic) and registered_topic != topic:
                for callback in callbacks:
                    try:
                        await callback(topic, payload)
                    except Exception as e:
                        logger.error(f"Erreur dans le callback wildcard pour {topic} ({registered_topic}): {e}")
    
    def _topic_matches_subscription(self, subscription: str, topic: str) -> bool:
        """
        Vérifie si un topic correspond à un pattern de souscription
        
        Args:
            subscription: Le pattern de souscription (peut contenir des wildcards)
            topic: Le topic à vérifier
            
        Returns:
            True si le topic correspond au pattern
        """
        if subscription == topic:
            return True
        
        sub_parts = subscription.split('/')
        topic_parts = topic.split('/')
        
        if len(sub_parts) > len(topic_parts):
            return False
        
        for i, part in enumerate(sub_parts):
            if part == '#':
                return True
            if part != '+' and part != topic_parts[i]:
                return False
            if i == len(sub_parts) - 1 and i < len(topic_parts) - 1 and part != '#':
                return False
        
        return len(sub_parts) == len(topic_parts)
    
    async def _run_connect_callbacks(self):
        """Exécute les callbacks de connexion"""
        for callback in self.on_connect_callbacks:
            try:
                await callback()
            except Exception as e:
                logger.error(f"Erreur dans un callback de connexion: {e}")
    
    async def _run_disconnect_callbacks(self, rc: int):
        """
        Exécute les callbacks de déconnexion
        
        Args:
            rc: Code de retour de la déconnexion
        """
        for callback in self.on_disconnect_callbacks:
            try:
                await callback(rc)
            except Exception as e:
                logger.error(f"Erreur dans un callback de déconnexion: {e}")
    
    async def _reconnect(self):
        """Tente de se reconnecter au broker MQTT"""
        if self.connecting or self.connected.is_set():
            return
        
        self.connecting = True
        wait_time = 5  # Temps d'attente initial
        max_wait = 60  # Temps d'attente maximal
        
        while not self.connected.is_set() and self.connecting:
            logger.info(f"Tentative de reconnexion dans {wait_time} secondes...")
            await asyncio.sleep(wait_time)
            
            try:
                if self.use_tls and not self._tls_configured:
                    ssl_context = self._get_ssl_context()
                    self.client.tls_set_context(ssl_context)
                    self._tls_configured = True
                
                self.client.reconnect()
                
                # Attendre la connexion avec timeout
                try:
                    await asyncio.wait_for(self.connected.wait(), timeout=10)
                    logger.info("Reconnexion réussie")
                    break
                except asyncio.TimeoutError:
                    logger.warning("Timeout lors de la reconnexion")
                
                # Augmenter le temps d'attente de façon exponentielle
                wait_time = min(wait_time * 2, max_wait)
            
            except Exception as e:
                logger.error(f"Erreur lors de la tentative de reconnexion: {e}")
                wait_time = min(wait_time * 2, max_wait)
        
        self.connecting = False
    
    async def connect(self) -> bool:
        """
        Se connecte au broker MQTT - VERSION SIMPLIFIÉE
        
        Returns:
            True si connecté avec succès
        """
        if self.connected.is_set():
            return True
        
        if self.connecting:
            await self.connected.wait()
            return self.connected.is_set()
        
        self.connecting = True
        
        try:
            logger.info(f"🔄 Connexion simple au broker MQTT: {self.broker}:{self.port}")
            
            # Configuration TLS si nécessaire
            if self.use_tls and not self._tls_configured:
                try:
                    ssl_context = self._get_ssl_context()
                    self.client.tls_set_context(ssl_context)
                    self._tls_configured = True
                    logger.info("🔒 Configuration TLS appliquée")
                except Exception as e:
                    logger.error(f"❌ Erreur TLS: {e}")
                    return False
            
            # Connexion directe sans persistance complexe
            self.client.connect(self.broker, port=self.port, keepalive=60)
            self.client.loop_start()
            
            # Attendre la connexion
            await asyncio.wait_for(self.connected.wait(), timeout=1.0)
            logger.info("✅ Connexion MQTT établie avec succès")
            self.connecting = False
            return True
                    
        except asyncio.TimeoutError:
            logger.error("⏱️ Timeout lors de la connexion MQTT")
            self.client.disconnect()
            self.client.loop_stop()
            self.connecting = False
            return False
        except Exception as e:
            logger.error(f"❌ Erreur lors de la connexion MQTT: {e}")
            self.connecting = False
            return False
    
    async def disconnect(self):
        """Se déconnecte du broker MQTT"""
        logger.info("Déconnexion du broker MQTT")
        
        try:
            # Only disconnect if connected
            if self.connected.is_set():
                try:
                    self.client.disconnect()
                    logger.info("Requête de déconnexion envoyée au broker MQTT")
                except Exception as e:
                    logger.warning(f"Non-critique: Erreur lors de la déconnexion MQTT: {e}")
            else:
                logger.info("Client MQTT déjà déconnecté")
            
            # Always stop the loop to ensure resources are freed
            try:
                self.client.loop_stop()
                logger.info("Boucle MQTT arrêtée")
            except Exception as e:
                logger.warning(f"Non-critique: Erreur lors de l'arrêt de la boucle MQTT: {e}")
            
            # Clear the connected flag in any case
            self.connected.clear()
            logger.info("Déconnecté normalement du broker MQTT")
            
        except Exception as e:
            logger.error(f"Erreur lors de la déconnexion MQTT: {e}")
            # Still clear the connected flag in case of error
            self.connected.clear()
    
    async def subscribe(self, topic: str, callback: Callable[[str, Dict[str, Any]], None]) -> bool:
        """
        S'abonne à un topic MQTT
        
        Args:
            topic: Topic à suivre
            callback: Fonction appelée lors de la réception d'un message
            
        Returns:
            True si l'abonnement a réussi
        """
        logger.debug(f"Abonnement au topic: {topic}")
        
        # Enregistrer le callback
        if topic not in self.on_message_callbacks:
            self.on_message_callbacks[topic] = []
        self.on_message_callbacks[topic].append(callback)
        
        # S'abonner si connecté
        if self.connected.is_set():
            result, _ = self.client.subscribe(topic, qos=1)
            if result == mqtt.MQTT_ERR_SUCCESS:
                self.subscribed_topics.add(topic)
                return True
            else:
                logger.error(f"Échec d'abonnement au topic {topic}")
                return False
        else:
            # Ajouter à la liste pour s'abonner après connexion
            self.subscribed_topics.add(topic)
            return True
    
    async def unsubscribe(self, topic: str, callback: Optional[Callable] = None) -> bool:
        """
        Se désabonne d'un topic MQTT
        
        Args:
            topic: Topic à quitter
            callback: Callback à supprimer (si None, tous les callbacks sont supprimés)
            
        Returns:
            True si le désabonnement a réussi
        """
        logger.debug(f"Désabonnement du topic: {topic}")
        
        # Supprimer le callback
        if topic in self.on_message_callbacks:
            if callback is None:
                self.on_message_callbacks.pop(topic)
            else:
                try:
                    self.on_message_callbacks[topic].remove(callback)
                except ValueError:
                    pass
                
                if not self.on_message_callbacks[topic]:
                    self.on_message_callbacks.pop(topic)
        
        # Se désabonner si connecté et si aucun callback restant
        if topic not in self.on_message_callbacks and self.connected.is_set():
            result, _ = self.client.unsubscribe(topic)
            if result == mqtt.MQTT_ERR_SUCCESS:
                self.subscribed_topics.discard(topic)
                return True
            else:
                logger.error(f"Échec de désabonnement du topic {topic}")
                return False
        
        # Retirer de la liste si aucun callback restant
        if topic not in self.on_message_callbacks:
            self.subscribed_topics.discard(topic)
            
        return True
    
    def on_connect(self, callback: Callable[[], None]):
        """
        Enregistre un callback pour la connexion
        
        Args:
            callback: Fonction appelée lors de la connexion
        """
        self.on_connect_callbacks.append(callback)
    
    def on_disconnect(self, callback: Callable[[int], None]):
        """
        Enregistre un callback pour la déconnexion
        
        Args:
            callback: Fonction appelée lors de la déconnexion
        """
        self.on_disconnect_callbacks.append(callback)
    
    async def publish(self, topic: str, payload: Dict[str, Any], qos: int = 1, retain: bool = False) -> bool:
        """
        Publie un message sur un topic MQTT
        """
        self.last_activity = time.time()
        
        try:
            # Sérialiser en JSON
            payload_str = json.dumps(payload, cls=DateTimeEncoder)
            
            # Si connecté, publier directement
            if self.connected.is_set():
                result = self.client.publish(topic, payload_str, qos=qos, retain=retain)
                if result.rc == mqtt.MQTT_ERR_SUCCESS:
                    logger.debug(f"Message publié sur {topic}")
                    return True
                else:
                    logger.error(f"Échec de publication sur {topic}: {result.rc}")
                    return False
            else:
                # Si pas connecté, mettre en buffer simple
                logger.debug(f"Client non connecté, mise en buffer du message pour {topic}")
                self.message_buffer.append((topic, payload_str, qos, retain))
                
                # Limiter la taille du buffer
                if len(self.message_buffer) > 50:  # Réduits de 100 à 50
                    self.message_buffer.pop(0)
                
                return False
                
        except Exception as e:
            logger.error(f"Erreur lors de la publication sur {topic}: {e}")
            return False
    
    def _get_queue_type_from_topic(self, topic: str) -> Optional[str]:
        """
        Détermine le type de file correspondant à un topic
        
        Args:
            topic: Topic MQTT
            
        Returns:
            str: Type de file ('presence', 'logs', 'status') ou None
        """
        if "/presence" in topic:
            return "presence"
        elif "/logs" in topic:
            return "logs"
        elif "/status" in topic:
            return "status"
        return None
    
    async def _process_persisted_presence(self, data: Dict[str, Any]) -> bool:
        """
        Traite un événement de présence persisté
        
        Args:
            data: Données de présence
            
        Returns:
            bool: True si traitement réussi
        """
        if not self.connected.is_set():
            raise Exception("Non connecté au broker MQTT")
            
        try:
            topic = MQTTTopics.presence(data.get("module_uid", config.MODULE_ID))
            payload_str = json.dumps(data, cls=DateTimeEncoder)
            result = self.client.publish(topic, payload_str, qos=1)
            return result.rc == mqtt.MQTT_ERR_SUCCESS
        except Exception as e:
            logger.error(f"Erreur lors de la publication d'un événement de présence persisté: {e}")
            raise
    
    async def _process_persisted_log(self, data: Dict[str, Any]) -> bool:
        """
        Traite un événement de log persisté
        
        Args:
            data: Données de log
            
        Returns:
            bool: True si traitement réussi
        """
        if not self.connected.is_set():
            raise Exception("Non connecté au broker MQTT")
            
        try:
            topic = MQTTTopics.logs(data.get("module_uid", config.MODULE_ID))
            payload_str = json.dumps(data, cls=DateTimeEncoder)
            result = self.client.publish(topic, payload_str, qos=1)
            return result.rc == mqtt.MQTT_ERR_SUCCESS
        except Exception as e:
            logger.error(f"Erreur lors de la publication d'un log persisté: {e}")
            raise
    
    async def _process_persisted_status(self, data: Dict[str, Any]) -> bool:
        """
        Traite un événement de statut persisté
        
        Args:
            data: Données de statut
            
        Returns:
            bool: True si traitement réussi
        """
        if not self.connected.is_set():
            raise Exception("Non connecté au broker MQTT")
            
        try:
            topic = MQTTTopics.status(data.get("module_uid", config.MODULE_ID))
            payload_str = json.dumps(data, cls=DateTimeEncoder)
            result = self.client.publish(topic, payload_str, qos=1)
            return result.rc == mqtt.MQTT_ERR_SUCCESS
        except Exception as e:
            logger.error(f"Erreur lors de la publication d'un statut persisté: {e}")
            raise
    
    async def publish_presence(self, presence_data: Dict[str, Any]) -> bool:
        """
        Publie une détection de présence sur MQTT, gérant les entrées/sorties avec cooldown
        
        Args:
            presence_data: Données de présence au format attendu par le backend
            
        Returns:
            bool: True si la publication a réussi ou si le cooldown est actif, False en cas d'erreur
        """
        try:
            # Vérifier le student_id
            student_id = presence_data.get('student_id')
            if not student_id:
                logger.error("❌ student_id manquant dans les données de présence")
                return False

            # Obtenir l'heure courante et le statut précédent
            current_time = datetime.now().astimezone()
            previous_status = self.presence_status.get(student_id)
            
            if previous_status:
                cooldown_delta = timedelta(seconds=config.PRESENCE_COOLDOWN)
                time_since_last = current_time - previous_status["timestamp"]
                
                if time_since_last < cooldown_delta:
                    # Si en cooldown, ignorer la détection
                    logger.info(f"⏳ Cooldown actif pour l'étudiant {student_id} - "
                             f"Prochaine détection possible dans {(cooldown_delta - time_since_last).seconds} secondes")
                    return True
                else:
                    # Si le cooldown est expiré, on publie une présence
                    presence_data["status"] = True
                    logger.info(f"🚶‍♂️ Cooldown expiré pour l'étudiant {student_id}, ")
            
            # S'assurer que module_uid est un entier
            if "module_uid" in presence_data and not isinstance(presence_data["module_uid"], int):
                try:
                    presence_data["module_uid"] = int(presence_data["module_uid"])
                except (ValueError, TypeError):
                    logger.error(f"❌ module_uid '{presence_data['module_uid']}' invalide, doit être un entier")
                    return False
                    
            # Vérifier que le module_uid est présent et valide
            if "module_uid" not in presence_data or presence_data["module_uid"] is None:
                presence_data["module_uid"] = int(config.MODULE_ID)
                logger.warning(f"⚠️ module_uid non spécifié, utilisation du MODULE_ID par défaut: {config.MODULE_ID}")
            
            # Ajouter un timestamp s'il n'est pas présent
            if "timestamp" not in presence_data or presence_data["timestamp"] is None:
                presence_data["timestamp"] = current_time
            
            # Validation des données avec le schéma Pydantic
            presence_msg = PresenceBase(**presence_data)
            
            # Utiliser directement le topic défini par MQTTTopics.presence
            topic = f"crec/modules/{presence_data['module_uid']}/presence"
            
            # Publier de manière asynchrone avec QoS 2 pour garantir la livraison
            success = await self.publish(topic, presence_msg.model_dump(), qos=2, retain=False)
            
            if success:
                # Si c'est une nouvelle détection (pas une sortie automatique)
                if not previous_status or time_since_last >= cooldown_delta:
                    self.presence_status[student_id] = {
                        "timestamp": current_time,
                        "status": True
                    }
                    presence_status = "entrée" if presence_data.get("status", True) else "sortie"
                    logger.info(f"✅ {presence_status.title()} publiée sur {topic} - Student: {student_id}")
                return True
            else:
                logger.error(f"❌ Échec de la publication de présence sur {topic}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erreur lors de la publication de présence: {str(e)}")
            import traceback
            logger.debug(f"Détails: {traceback.format_exc()}")
            return False
    
    async def publish_status(self, status_data: Dict[str, Any]) -> bool:
        """
        Publie l'état du module sur le topic de statut
        """
        try:
            # S'assurer que module_uid est présent
            if "module_uid" not in status_data:
                status_data["module_uid"] = config.MODULE_ID
                
            # Publier directement sur le topic
            topic = MQTTTopics.status(config.MODULE_ID)
            logger.info(f"📤 Publication statut sur topic: {topic}")
            logger.info(f"📦 Données à publier: {status_data}") 
            logger.info(f"🔌 Client connecté: {self.client.is_connected() if self.client else False}")
            logger.info(f"🆔 Module ID utilisé: {config.MODULE_ID}")
            
            # Publier directement sur le topic
            result = await self.publish(topic, status_data)
            
            if result:
                logger.info(f"✅ Statut publié avec succès sur {topic}")
            else:
                logger.error(f"❌ Échec de publication sur {topic}")
                
            return result
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la publication du statut: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return False
    
    async def publish_log(self, log_data: Dict[str, Any]) -> bool:
        """
        Publie un message de log sur le topic de logs
        """
        try:
            # S'assurer que module_uid est présent
            if "module_uid" not in log_data:
                log_data["module_uid"] = config.MODULE_ID
                
            # Publier directement sur le topic
            topic = MQTTTopics.logs(config.MODULE_ID)
            return await self.publish(topic, log_data)
            
        except Exception as e:
            logger.error(f"Erreur lors de la publication de log: {e}")
            return False
    
    async def _handle_config_updates(self, topic: str, payload: Dict[str, Any]):
        """
        Gère les mises à jour de configuration
        
        Args:
            topic: Topic du message
            payload: Contenu du message
        """
        try:
            # Essayer de parser en utilisant le schéma ConfigUpdateMQTT
            config_update = ConfigUpdateMQTT(**payload)
            
            # Vérifier si la configuration s'applique à ce module
            if config_update.module_uid is not None and config_update.module_uid != config.MODULE_ID:
                logger.debug(f"Configuration ignorée: destinée au module {config_update.module_uid}")
                return
            
            if config_update.type == "auth_threshold":
                self.auth_threshold = config_update.value
                logger.info(f"Seuil d'authentification mis à jour: {config_update.value}")
                
            elif config_update.type == "notifications":
                self.notifications_enabled = config_update.value
                logger.info(f"État des notifications mis à jour: {config_update.value}")
                
            else:
                logger.warning(f"Type de configuration non reconnu: {config_update.type}")
                
        except Exception as e:
            logger.error(f"Erreur lors du traitement de la configuration: {e}")
            # Fallback au format legacy
            try:
                update_type = payload.get("type")
                value = payload.get("value")
                
                if update_type == "auth_threshold":
                    self.auth_threshold = value
                    logger.info(f"Seuil d'authentification mis à jour (legacy): {value}")
                    
                elif update_type == "notifications":
                    self.notifications_enabled = value
                    logger.info(f"État des notifications mis à jour (legacy): {value}")
                    
                else:
                    logger.warning(f"Type de configuration non reconnu (legacy): {update_type}")
            except Exception as e2:
                logger.error(f"Échec complet du traitement de la configuration: {e2}")
                
    async def _handle_commands(self, topic: str, payload: Dict[str, Any]):
        """
        Gère les commandes reçues - VERSION SIMPLIFIÉE
        """
        try:
            command = payload.get("command")
            
            if command == "restart":
                logger.info("Commande de redémarrage reçue")
                # TODO: Implémenter la logique de redémarrage
                
            elif command == "status":
                logger.info("Commande de statut reçue")
                await self.publish_status({
                    "status": "online",
                    "version": getattr(config, 'VERSION', '1.0.0'),
                    "uptime": self._get_uptime(),
                    "module_uid": config.MODULE_ID,
                    "timestamp": datetime.now().isoformat()
                })
                
            else:
                logger.warning(f"Commande inconnue reçue: {command}")
                
        except Exception as e:
            logger.error(f"Erreur lors du traitement de la commande: {e}")
    
    def _get_uptime(self) -> int:
        """Calcule le temps d'uptime en secondes"""
        import time
        return int(time.time() - time.process_time())
