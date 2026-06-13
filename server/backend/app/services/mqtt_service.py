import json
import asyncio
import os
import ssl
import datetime
from typing import Dict, Any, Optional, Callable
from pathlib import Path
from paho.mqtt import client as mqtt
from paho.mqtt.client import MQTTMessage
from pydantic import ValidationError

from app.core.config import settings
from app.services.log_service import db_logger

MQTT_BROKER = settings.MQTT_BROKER
MQTT_PORT = settings.MQTT_PORT
MQTT_CA_CERT = settings.MQTT_CA_CERT
MQTT_CLIENT_CERT = settings.MQTT_CLIENT_CERT
MQTT_CLIENT_KEY = settings.MQTT_CLIENT_KEY

# Instance globale du client MQTT
mqtt_client = None

class MQTTClient:
    """Client MQTT pour la communication avec les modules du système Edge Attendance System."""
    def __init__(self):
        self.client = None
        self.connected = False
        self.message_buffer = []
        self.reconnect_interval = 5  # seconds
        self.topic_handlers = {}
        self.max_buffer_size = 100  # taille maximale du tampon
        self.loop = None
        self.subscribed_modules = set()  # Suivi des modules abonnés
        
    async def connect(self):
        """Établit une connexion sécurisée au broker MQTT."""
        
        # Get the current event loop
        self.loop = asyncio.get_running_loop()
        
        # Configuration du client MQTT
        self.client = mqtt.Client(
            client_id=f"crec-server-{id(self)}",
            protocol=mqtt.MQTTv5,
            transport="tcp"
        )

        # Configuration de l'authentification
        if settings.mqtt_user and settings.mqtt_password:
            self.client.username_pw_set(settings.mqtt_user, settings.mqtt_password)
            await db_logger.debug(
                f"L'authentification MQTT a été configurée avec succès pour l'utilisateur '{settings.mqtt_user}'. Le système peut maintenant communiquer de manière sécurisée avec les modules de présence.",
                source="mqtt_service",
            )
        else:
            await db_logger.warning(
                "Attention : Aucune authentification MQTT n'est configurée. Le système fonctionne en mode non sécurisé, ce qui peut poser des risques de sécurité si le broker MQTT est accessible depuis l'extérieur.",
                source="mqtt_service",
            )

        # Configuration TLS/SSL si nécessaire
        if settings.mqtt_port == 8883:  # Port TLS standard
            context = ssl.create_default_context()
            context.load_verify_locations(cafile=MQTT_CA_CERT)
            self.client.tls_set_context(context)
        
        # Définir les callbacks synchrones qui appelleront les versions asynchrones
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message
        
        # Connexion au broker
        try:
            # await db_logger.info(
            #     f"🔌 Tentative de connexion MQTT vers {settings.mqtt_host}:{settings.mqtt_port}",
            #     source="mqtt_service",
            #     details={
            #         "host": settings.mqtt_host,
            #         "port": settings.mqtt_port,
            #         "user": settings.mqtt_user,
            #         "tls": settings.MQTT_USE_TLS
            #     }
            # )
            
            self.client.connect(
                settings.mqtt_host,
                settings.mqtt_port,
                keepalive=60
            )
            self.client.loop_start()

            # Attendre jusqu'à 10 secondes pour la connexion avec logs détaillés
            for i in range(10):
                if self.client.is_connected():
                    self.connected = True
                    break
                await db_logger.debug(
                    f"⏳ Attente connexion MQTT... ({i+1}/10)",
                    source="mqtt_service"
                )
                await asyncio.sleep(1)
                
            if not self.connected:
                await db_logger.error(
                    "🔌 Échec de connexion au broker MQTT après 10 secondes ❌",
                    source="mqtt_service",
                    details={
                        "host": settings.mqtt_host, 
                        "port": settings.mqtt_port,
                        "timeout": "10s",
                        "client_connected": self.client.is_connected()
                    }
                )
                return False
            
            # Envoyer les messages tamponnés
            if self.message_buffer:
                await db_logger.debug(
                    f"Le système va maintenant traiter {len(self.message_buffer)} messages MQTT qui étaient en attente pendant la reconnexion. Ces messages contiennent des données importantes des modules de présence.",
                    source="mqtt_service",
                )

                for topic, payload, qos, retain in self.message_buffer:
                    self.client.publish(topic, payload, qos, retain)
                self.message_buffer.clear()
            
            await db_logger.debug(
                f"Connexion établie avec succès au serveur MQTT. Le système peut maintenant recevoir les données des modules de présence en temps réel. Serveur: {settings.mqtt_host}:{settings.mqtt_port}",
                source="mqtt_service",
            )

            return True

        except Exception as e:
            await db_logger.error(
                "❌ Erreur lors de la connexion au broker MQTT",
                source="mqtt_service",
            )
            return False

    # Synchronous callback wrappers
    def _on_connect(self, client, userdata, flags, rc, properties=None):
        """Synchronous wrapper for on_connect that schedules the async callback"""
        asyncio.run_coroutine_threadsafe(
            self._on_connect_async(client, userdata, flags, rc, properties),
            self.loop
        )

    def _on_disconnect(self, client, userdata, rc, properties=None):
        """Synchronous wrapper for on_disconnect that schedules the async callback"""
        asyncio.run_coroutine_threadsafe(
            self._on_disconnect_async(client, userdata, rc, properties),
            self.loop
        )

    def _on_message(self, client, userdata, msg):
        """Synchronous wrapper for on_message that schedules the async callback"""
        asyncio.run_coroutine_threadsafe(
            self._on_message_async(client, userdata, msg),
            self.loop
        )

    async def _on_connect_async(self, client, userdata, flags, rc, properties=None):
        """Callback appelé lors de la connexion ou reconnexion au broker."""
        
        # Messages d'erreur MQTT détaillés
        error_messages = {
            0: "Connexion réussie",
            1: "Version de protocole incorrecte",
            2: "Identifiant client invalide", 
            3: "Serveur indisponible",
            4: "Nom d'utilisateur ou mot de passe incorrect",
            5: "Non autorisé"
        }
        
        if rc == 0:
            self.connected = True
            await db_logger.debug(
                f"Connexion MQTT établie avec succès. Le système peut maintenant communiquer avec tous les modules de présence. Code de réponse: {rc} ({error_messages.get(rc, 'Code inconnu')})",
                source="mqtt_service",
            )
            
            for topic in self.topic_handlers.keys():
                client.subscribe(topic, qos=1)
                await db_logger.debug(
                    f"Abonnement configuré au topic '{topic}' pour recevoir les messages des modules. Le système surveillera maintenant les événements sur ce canal de communication.",
                    source="mqtt_service",
                )
        
        else:
            self.connected = False
            error_msg = error_messages.get(rc, f"Erreur inconnue: {rc}")
            await db_logger.error(
                f"Échec de la connexion au serveur MQTT. Le système ne peut pas communiquer avec les modules de présence. Erreur: {error_msg}. Vérifiez la configuration du serveur MQTT et les paramètres de connexion.",
                source="mqtt_service",
                details={
                    "return_code": rc,
                    "message": error_msg,
                    "host": settings.mqtt_host,
                    "port": settings.mqtt_port,
                    "user": settings.mqtt_user,
                    "auth_configured": bool(settings.mqtt_user and settings.mqtt_password)
                }
            )
    
    async def _on_disconnect_async(self, client, userdata, rc, properties=None):
        """Callback appelé lors de la déconnexion du broker."""
        self.connected = False
        if rc != 0:
            asyncio.create_task(self._reconnect())

        else:
            # await db_logger.info(
            #     "📡 Déconnexion normale du broker MQTT ✅",
            #     source="mqtt_service"
            # )
            pass
    
    async def _reconnect(self):
        """Tente de se reconnecter au broker MQTT après une déconnexion."""        
        # await db_logger.info(
        #     f"🔄 Tentative de reconnexion au broker MQTT dans {self.reconnect_interval} secondes",
        #     source="mqtt_service"
        # )

        await asyncio.sleep(self.reconnect_interval)
        if not self.client.is_connected():
            await self.connect()
    
    async def _on_message_async(self, client, userdata, msg: MQTTMessage):
        """Callback appelé lors de la réception d'un message."""
        topic = msg.topic
        payload = msg.payload.decode('utf-8')
        
        await db_logger.debug(
            f"Message reçu du module via MQTT sur le topic '{topic}'. Le système va maintenant traiter cette information pour mettre à jour l'état du module.",
            source="mqtt_service",
        )
        
        if topic in self.topic_handlers: # Filtre uniquement les topics enregistrés
            try:
                json_payload = json.loads(payload)
                for handler in self.topic_handlers[topic]:
                    asyncio.create_task(handler(topic, json_payload))
            
            except json.JSONDecodeError as e:
                await db_logger.error(
                    f"Erreur de format dans le message reçu du module. Le message sur le topic '{topic}' n'est pas au format JSON valide. Cela peut indiquer un problème de communication avec le module. Erreur: {str(e)}",
                    source="mqtt_service",
                )

            except Exception as e:
                await db_logger.error(
                    f"Erreur inattendue lors du traitement du message MQTT reçu sur '{topic}'. Le système n'a pas pu traiter correctement les données du module. Erreur: {str(e)}",
                    source="mqtt_service",
                )
    
    async def subscribe(self, topic: str, handler: Callable):
        """
        S'abonne à un topic MQTT et enregistre un handler pour les messages.
        
        Args:
            topic: Le topic MQTT auquel s'abonner
            handler: Une fonction async qui sera appelée avec (topic, json_payload)
        """
        if topic not in self.topic_handlers:
            self.topic_handlers[topic] = []

            if self.connected:
                self.client.subscribe(topic, qos=1)
                await db_logger.debug(
                    f"📡 Abonnement au topic MQTT: {topic} ✅",
                    source="mqtt_service"
                )
        
        self.topic_handlers[topic].append(handler)
    
    async def unsubscribe(self, topic: str, handler: Optional[Callable] = None):
        """
        Se désabonne d'un topic MQTT.
        
        Args:
            topic: Le topic MQTT auquel se désabonner
            handler: Handler spécifique à supprimer, ou None pour tous
        """
        if topic in self.topic_handlers:
            if handler:
                self.topic_handlers[topic].remove(handler)
                if not self.topic_handlers[topic]:
                    self.client.unsubscribe(topic)
                    del self.topic_handlers[topic]
                
                    await db_logger.debug(
                        f"🚫 Désabonnement du topic MQTT: {topic} ✅",
                        source="mqtt_service"
                    )
            else:
                self.client.unsubscribe(topic)
                
                del self.topic_handlers[topic]
                await db_logger.debug(
                    f"🚫 Désabonnement du topic MQTT: {topic} ✅",
                    source="mqtt_service"
                )
    
    async def publish(self, topic: str, payload: Dict[str, Any], qos: int = 1, retain: bool = False):
        """
        Publie un message sur un topic MQTT.
        
        Args:
            topic: Le topic MQTT sur lequel publier
            payload: Les données à publier (seront converties en JSON)
            qos: Niveau de qualité de service (0, 1, ou 2)
            retain: Si le message doit être conservé par le broker
        """
        if not self.connected:
            await db_logger.warning(
                "📨 Tentative de publication MQTT sans connexion ⚠️",
                source="mqtt_service",
                details={"topic": topic}
            )
            self.message_buffer.append((topic, json.dumps(payload), qos, retain))
            return False

        try:
            result = self.client.publish(
                topic,
                json.dumps(payload),
                qos=qos,
                retain=retain
            )
            result.wait_for_publish()
            
            if result.rc != 0:
                await db_logger.error(
                    f"📨 Échec de publication MQTT sur {topic} ❌",
                    source="mqtt_service",
                    details={
                        "topic": topic,
                        "code": result.rc,
                        "payload": str(payload)[:200]
                    }
                )
                return False
            else :  
                await db_logger.debug(
                    f"📨 Message MQTT publié sur {topic} ✅",
                    source="mqtt_service",
                    details={"topic": topic, "payload": str(payload)[:200]}
                )
                return True
                
        except Exception as e:
            await db_logger.error(
                f"💥 Erreur lors de la publication MQTT sur {topic} 🚨",
                source="mqtt_service",
                details={
                    "erreur": str(e),
                    "topic": topic,
                    "payload": str(payload)[:200]
                }
            )
            return False

    async def publish_config_update(self, update_type: str, data: any):
        """
        Publie une mise à jour de configuration sur le topic 'crec/modules/config_updates'.
        
        Args:
            update_type: Le type de mise à jour (ex: 'rfid', 'facial_recognition', 'max_login_attempts')
            data: Les données spécifiques à la mise à jour (booléen, nombre, ou autre)
        """
        payload = {
            "type": update_type, # rfid, facial_recognition, max_login_attempts
            "value": data,
            "timestamp": datetime.datetime.utcnow().isoformat()
            }

        topic = "crec/modules/config_updates"
        await db_logger.debug(
            f"⚙️ Envoi d'une mise à jour de configuration: {update_type} 📤",
            source="mqtt_service",
            details={"type": update_type, "value": data}
        )
        
        await self.publish(topic, payload)

        await db_logger.debug(
            f"⚙️ Mise à jour de configuration envoyée sur {topic} ✅",
            source="mqtt_service"
        )
    
    async def disconnect(self):
        """Déconnecte proprement le client MQTT."""
        if self.client and self.connected:
            self.client.loop_stop()
            self.client.disconnect()

            await db_logger.info(
                "🚪 Déconnexion du broker MQTT ✅",
                source="mqtt_service"
            )

    async def restart_module(self, module_uid: int) -> bool:
        """
        Envoie une commande de redémarrage à un module via MQTT.
        
        Args:
            module_uid: L'UID du module à redémarrer
            
        Returns:
            bool: True si la commande a été envoyée avec succès
        """
        topic = f"crec/modules/{module_uid}/command"
        payload = {
            "command": "restart",
            "timestamp": datetime.datetime.utcnow().isoformat()
        }
        
        success = await self.publish(topic, payload, qos=2)  # QoS 2 pour garantir la livraison
        
        if success:
            await db_logger.debug(
                f"🔄 Commande de redémarrage envoyée au module {module_uid} ✅",
                source="mqtt_service",
                details={"module_uid": module_uid}
            )
        else:
            await db_logger.error(
                f"🔄 Échec d'envoi de la commande de redémarrage au module {module_uid} ❌",
                source="mqtt_service",
                details={"module_uid": module_uid}
            )
        
        return success

    async def publish_auth_threshold_update(self, threshold: int):
        """
        Publie une mise à jour du seuil d'alerte d'authentification sur le topic 'crec/modules/config_updates'.
        
        Args:
            threshold: Le nombre d'échecs d'authentification successifs avant déclenchement d'une alerte
        """
        payload = {
            "type": "auth_threshold",
            "value": threshold,
            "timestamp": datetime.datetime.utcnow().isoformat()
        }

        topic = "crec/modules/config_updates"
        
        await db_logger.debug(
            f"🔐 Envoi de la mise à jour du seuil d'alerte d'authentification: {threshold} 📤",
            source="mqtt_service",
            details={"threshold": threshold}
        )
        
        await self.publish(topic, payload)

        await db_logger.debug(
            f"🔐 Le seuil d'alerte à {threshold} envoyé sur {topic} ✅",
            source="mqtt_service"
        )

    async def subscribe_to_module(self, module_uid: int):
        """
        S'abonne aux topics spécifiques d'un module.
        
        Args:
            module_uid: L'UID du module pour lequel s'abonner
        """
        if module_uid in self.subscribed_modules:
            await db_logger.warning(
                f"📡 Module {module_uid} déjà abonné ⚠️",
                source="mqtt_service",
                details={"module_uid": module_uid}
            )
            return
            
        # Topics spécifiques au module
        module_topics = [
            f"crec/modules/{module_uid}/status",
            f"crec/modules/{module_uid}/logs", 
            f"crec/modules/{module_uid}/presence"
        ]
        
        for topic in module_topics:
            if topic.endswith("/status"):
                await self.subscribe(topic, handle_module_status)

            elif topic.endswith("/logs"):
                await self.subscribe(topic, handle_module_logs)

            elif topic.endswith("/presence"):
                await self.subscribe(topic, handle_presence_events)
        
        self.subscribed_modules.add(module_uid)
        
        await db_logger.debug(
            f"📡 Abonnement aux topics du module {module_uid} effectué ✅",
            source="mqtt_service"
        )
    
    async def unsubscribe_from_module(self, module_uid: int):
        """
        Se désabonne des topics spécifiques d'un module.
        
        Args:
            module_uid: L'UID du module pour lequel se désabonner
        """
        if module_uid not in self.subscribed_modules:
            await db_logger.warning(
                f"📡 Module {module_uid} n'est pas abonné ⚠️",
                source="mqtt_service",
                details={"module_uid": module_uid}
            )
            return
            
        # Topics spécifiques au module
        module_topics = [
            f"crec/modules/{module_uid}/status",
            f"crec/modules/{module_uid}/logs",
            f"crec/modules/{module_uid}/presence"
        ]
        
        for topic in module_topics:
            await self.unsubscribe(topic)
        
        self.subscribed_modules.discard(module_uid)
        
        await db_logger.debug(
            f"🚫 Désabonnement des topics du module {module_uid} effectué ✅",
            source="mqtt_service",
            details={"module_uid": module_uid, "topics": module_topics}
        )
    
    async def subscribe_to_all_modules(self):
        """
        S'abonne aux topics de tous les modules existants en base de données.
        """
        try:
            from app.services.module_service import get_modules
            from app.api.v1.deps import get_db
            
            async for db in get_db():
                modules = await get_modules(db, skip=None, limit=None)  # Récupérer tous les modules

                for module in modules:
                    await self.subscribe_to_module(module.uid)
                
                await db_logger.debug(
                    f"📡 Abonnement global effectué à tous les {len(modules)} modules ✅",
                    source="mqtt_service",
                )
                break  # Sortir de la boucle async generator
                
        except Exception as e:
            await db_logger.error(
                f"❌ Erreur lors de l'abonnement global aux modules: {str(e)} 🚨",
                source="mqtt_service",
                details={"erreur": str(e)}
            )

    async def disconnect(self):
        """Déconnecte proprement le client MQTT."""
        if self.client and self.connected:
            self.client.loop_stop()
            self.client.disconnect()
            await db_logger.debug(
                "🚪 Déconnexion du broker MQTT ✅",
                source="mqtt_service"
            )

async def publish_system_settings():
    """
    Publie tous les paramètres système importants sur MQTT lors du démarrage.
    Cette fonction récupère les paramètres actuels et les publie sur le canal approprié.
    """
    from app.services.settings_service import settings_service
    
    try:
        # Récupérer les paramètres système actuels
        settings_data = await settings_service.get_settings()
        if not settings_data or 'settings' not in settings_data:
            await db_logger.error(
                "❌ Impossible de récupérer les paramètres système pour publication MQTT",
                source="mqtt_service"
            )
            return
            
        system_settings = settings_data['settings'].get('system', {})
        
        # Publier le seuil d'alerte d'authentification
        if 'max_login_attempts' in system_settings:
            await mqtt_client.publish_auth_threshold_update(system_settings['max_login_attempts'])
            
        # Publier d'autres paramètres système importants au besoin
        if 'notifications_enabled' in system_settings:
            await mqtt_client.publish_config_update('notifications', system_settings['notifications_enabled'])
      
        await db_logger.debug(
            "⚙️ Configuration système des modules publiée sur MQTT avec succès ✅",
            source="mqtt_service",
            details={"parameters": list(system_settings.keys())}
        )

    except Exception as e:
        await db_logger.error(
            f"💥 Erreur lors de la publication des paramètres système sur MQTT: {str(e)} 🚨",
            source="mqtt_service",
            details={"error": str(e)}
        )

async def initialize_mqtt():
    """Initialise la connexion MQTT et les abonnements de base."""
    await mqtt_client.connect()
    
    # Abonnements globaux 
    await mqtt_client.subscribe("crec/modules/config_updates", handle_config_updates)
    
    # await mqtt_client.subscribe("crec/system/commands", handle_system_commands)
    
    # Abonnements spécifiques par module
    await mqtt_client.subscribe_to_all_modules()
    
    # Publier les paramètres système actuels
    await publish_system_settings()

async def handle_module_status(topic: str, payload: Dict[str, Any]):
    """Traite les messages de statut des modules avec auto-enregistrement."""
    from app.schemas.module_status import ModuleStatusCreate
    from app.services.module_status_service import update_module_status
    from app.services.module_registration_service import register_module_if_not_exists
    from app.api.v1.deps import get_db
    
    await db_logger.debug(
        f"Signal de statut reçu du module via MQTT. Le système va maintenant analyser et enregistrer l'état actuel du module. Topic: {topic}, Données: {payload}",
        source="mqtt_service",
    )
    
    try:
        # Extraire l'UID du module depuis le topic
        # Format: crec/modules/{module_uid}/status
        topic_parts = topic.split('/')
        if len(topic_parts) >= 4 and topic_parts[0] == 'crec' and topic_parts[1] == 'modules' and topic_parts[3] == 'status':
            module_uid = int(topic_parts[2])
            await db_logger.debug(
                f"Module identifié depuis l'URL de communication: Module #{module_uid}",
                source="mqtt_service"
            )
        else:
            # Fallback vers le payload si le topic ne contient pas l'UID
            module_uid = payload.get("module_uid")
            await db_logger.debug(
                f"Module identifié depuis les données du message: Module #{module_uid}",
                source="mqtt_service",
            )

            if module_uid is None:
                await db_logger.warning(
                    "Impossible d'identifier le module expéditeur. Le message de statut ne contient pas d'identifiant valide. Le système ne peut pas traiter cette information.",
                    source="mqtt_service",
                )
                return
        
        # Convertir en int si c'est une string
        if isinstance(module_uid, str):
            module_uid = int(module_uid)
        
        async for db in get_db():
            await db_logger.debug(
                f"Début du traitement des données de statut pour le Module #{module_uid}. Le système va maintenant vérifier l'existence du module et mettre à jour ses informations d'état.",
                source="mqtt_service",             
                module_uid=module_uid
            )
            
            # Auto-enregistrement du module s'il n'existe pas
            await register_module_if_not_exists(db, module_uid, payload)
            await db_logger.debug(
                f"Enregistrement automatique du Module #{module_uid} terminé. Le module est maintenant reconnu dans le système et peut participer au contrôle de présence.",
                source="mqtt_service",
                module_uid=module_uid
            )
    
            # Mise à jour du statut du module
            status_data = ModuleStatusCreate(
                module_uid=module_uid,
                status=payload.get("status", "unknown"),
                version=payload.get("version"),
                uptime=payload.get("uptime"),
                memory_usage=payload.get("memory_usage"),
                cpu_usage=payload.get("cpu_usage"),
                details=payload.get("details")
            )
            
            status_info = f"Status={status_data.status}, Version={status_data.version}, Uptime={status_data.uptime}s, RAM={status_data.memory_usage}MB, CPU={status_data.cpu_usage}%"
            await db_logger.debug(
                f"Préparation des données de statut pour le Module #{module_uid}: {status_info}",
                source="mqtt_service",
                module_uid=module_uid
            )
            
            await update_module_status(db, status_data)
            
            status_description = {
                "online": "en ligne et opérationnel",
                "offline": "hors ligne",
                "idle": "en veille",
                "warning": "avec des alertes",
                "error": "en erreur"
            }.get(payload.get("status"), "dans un état inconnu")
            
            await db_logger.debug(
                f"Mise à jour du statut du Module #{module_uid} terminée avec succès. Le module est maintenant {status_description}. Les utilisateurs peuvent voir cette information en temps réel sur l'interface web.",
                source="mqtt_service",
                module_uid=module_uid
            )
            break  # Sortir de la boucle async generator
            
    except (ValueError, IndexError) as e:
        await db_logger.error(
            f"📊 Erreur d'extraction de l'UID du module depuis le topic {topic}: {str(e)} ❌",
            source="mqtt_service",
            details={"topic": topic, "erreur": str(e)}
        )

    except Exception as e:
        await db_logger.error(
            f"📊 Erreur lors du traitement du statut du module: {str(e)} 🚨",
            source="mqtt_service",
            details={"erreur": str(e), "payload": payload, "topic": topic}
        )
        import traceback
        await db_logger.error(
            f"📊 Traceback: {traceback.format_exc()}",
            source="mqtt_service"
        )

async def handle_module_logs(topic: str, payload: Dict[str, Any]):
    """Traite les messages de logs des modules."""
    from app.services.log_service import db_logger
    
    try:
        # Extraire l'UID du module depuis le topic
        # Format: crec/modules/{module_uid}/logs
        topic_parts = topic.split('/')
        if len(topic_parts) >= 4 and topic_parts[0] == 'crec' and topic_parts[1] == 'modules' and topic_parts[3] == 'logs':
            module_uid = int(topic_parts[2])
        else:
            # Fallback vers le payload si le topic ne contient pas l'UID
            module_uid = payload.get("module_uid")
            if module_uid is None:
                await db_logger.warning(
                    "📝 Impossible d'extraire l'UID du module depuis le topic ou le payload ⚠️",
                    source="mqtt_service",
                    details={"topic": topic, "payload": payload}
                )
                return
        
        # Traiter le payload selon la structure attendue
        log_data = {
            "module_uid": module_uid,
            "message": payload.get("message"),
            "timestamp": payload.get("timestamp")
        }
        
        # Enregistrer le log dans la base de données ou effectuer d'autres actions
        await db_logger.debug(
            f"📝 Log reçu du module {log_data['module_uid']}: {log_data['message']} 📥",
            source="mqtt_service",
            module_uid=log_data["module_uid"],
            details=log_data
        )
        
    except (ValueError, IndexError) as e:
        await db_logger.error(
            f"📝 Erreur d'extraction de l'UID du module depuis le topic {topic}: {str(e)} ❌",
            source="mqtt_service",
            details={"topic": topic, "erreur": str(e)}
        )

    except Exception as e:
        await db_logger.error(
            f"📝 Erreur lors du traitement des logs du module: {str(e)} 🚨", 
            source="mqtt_service",
            details={"erreur": str(e), "payload": payload, "topic": topic}
        )

async def handle_presence_events(topic: str, payload: Dict[str, Any]):
    """Traite les événements de présence."""
    from app.schemas.presence import PresenceCreate # Format des messages envoyés par les modules par MQTT
    from app.services.presence_service import save_presence
    from app.services.student_service import get as get_student_by_id  # Pour récupérer les informations d'un étudiant grâce à son id
    from app.api.v1.deps import get_db
    
    # class PresenceBase(BaseModel):
    # student_id: str
    # status: bool = Field(default=True, description="True pour présent, False pour absent")
    # module_uid: int = Field(default=0, description="ID du module (0 pour présence manuelle)")
    # timestamp: Optional[datetime] = None
    # Format de payload : payload = {student_id : str, status=1, module_uid}

    try:
        # Assurer que le timestamp a une timezone
        if "timestamp" in payload and payload["timestamp"]:
            try:
                # Si le timestamp est une string ISO
                if isinstance(payload["timestamp"], str):
                    ts = datetime.datetime.fromisoformat(payload["timestamp"])
                    if ts.tzinfo is None:
                        payload["timestamp"] = ts.astimezone()
                # Si c'est déjà un datetime
                elif isinstance(payload["timestamp"], datetime.datetime):
                    if payload["timestamp"].tzinfo is None:
                        payload["timestamp"] = payload["timestamp"].astimezone()
            except Exception as e:
                await db_logger.warning(
                    f"👥 Erreur lors de la conversion du timestamp: {str(e)} ⚠️",
                    source="mqtt_service",
                    details={"timestamp": payload.get("timestamp")}
                )
                payload["timestamp"] = datetime.datetime.now().astimezone()
        
        # Le payload est déjà un dictionnaire Python (parsé par le handler MQTT)
        presence_data = PresenceCreate.model_validate(payload)
    except Exception as e:
        await db_logger.error(
            f"👥 Erreur de validation du payload de présence: {str(e)} ❌",
            source="mqtt_service",
            details={"payload": payload, "topic": topic, "erreur": str(e)}
        )
        return

    try:
        # Extraire l'UID du module depuis le topic
        # Format: crec/modules/{module_uid}/presence
        topic_parts = topic.split('/')
        if len(topic_parts) >= 4 and topic_parts[0] == 'crec' and topic_parts[1] == 'modules' and topic_parts[3] == 'presence':
            module_uid = int(topic_parts[2])
            
            # Vérifiez si l'ID indiqué par le module correspond au topic où il devrait publier 
            if module_uid != presence_data.module_uid:
                await db_logger.warning(
                    f"Il y a incohérence entre l'UID du module dans le topic ({module_uid}) et dans le payload ({presence_data.module_uid})",
                    source="mqtt_service",
                    module_uid=presence_data.module_uid
                )
            
        else:
            # Vérifier si l'UID est dans le payload
            module_uid = presence_data.module_uid
            if module_uid is None:
                await db_logger.warning(
                    "👥 Impossible d'extraire l'UID du module depuis le topic ou le payload ⚠️",
                    source="mqtt_service",
                    details={"topic": topic, "payload": payload}
                )
                return
        
        async for db in get_db():
            try:
                # Tenter d'enregistrer la présence
                await save_presence(db, presence_data)

                # await db_logger.info(
                #     f"👥 Présence enregistrée à {datetime.datetime.now()} pour {presence_data.student_id} - Module {presence_data.module_uid} ✅",
                #     source="mqtt_service",
                #     module_uid=presence_data.module_uid
                # )

                student = await get_student_by_id(db, presence_data.student_id)
                if student:
                    student_name = student.firstName + " " + student.lastName 

                    if presence_data.status:
                        status_text = "présent"
                    else:
                        status_text = "absent"

                    # Logger la présence
                    await db_logger.info(
                        f"L'etudiant {student_name} (ID: {presence_data.student_id}) est maintenant {status_text} d'après le module {presence_data.module_uid}.",
                        source="module" if presence_data.module_uid else student_name,
                        module_uid=presence_data.module_uid
                    )
    
                    # details={
                    #     "student_id": presence_data.student_id,
                    #     "status": presence_data.status,
                    #     "timestamp": presence_data.timestamp.isoformat()
                    # }
                

            except ValueError as ve:
                # Gestion spécifique des erreurs de validation (étudiant non trouvé, etc.)
                await db_logger.warning(
                    f"👥 Validation échouée pour la présence: {str(ve)} ⚠️",
                    source="mqtt_service",
                    module_uid=presence_data.module_uid,
                    details={
                        "student_id": presence_data.student_id,
                        "erreur": str(ve),
                        "action": "presence_ignored"
                    }
                )
                # On n'interrompt pas le processus, on log juste l'erreur
                
            except Exception as e:
                await db_logger.error(
                    f"👥 Erreur lors de l'enregistrement de la présence: {str(e)} ❌",
                    source="mqtt_service",
                    module_uid=presence_data.module_uid,
                    details={
                        "student_id": presence_data.student_id,
                        "erreur": str(e)
                    }
                )

            break  # Sortir de la boucle async generator
            
    except (ValueError, IndexError) as e:
        await db_logger.error(
            f"👥 Erreur d'extraction de l'UID du module depuis le topic {topic}: {str(e)} ❌",
            source="mqtt_service",
            details={"topic": topic, "erreur": str(e)}
        )

    except Exception as e:
        await db_logger.error(
            f"👥 Erreur lors du traitement de l'événement de présence: {str(e)} 🚨",
            source="mqtt_service",
            details={"erreur": str(e), "payload": payload, "topic": topic}
        )

async def publish_mqtt_update(action: str, student_id: str):
    """
    Publie une mise à jour sur l'action effectuée sur un étudiant.
    
    Args:
        action: L'action effectuée ("create")
        student_id: L'ID de l'étudiant concerné
    """

    payload = {
        "action": action,
        "student_id": student_id,
        "timestamp": datetime.datetime.utcnow().isoformat()
    }
    
    await mqtt_client.publish("crec/students/updates", payload)

async def handle_config_updates(topic: str, payload: Dict[str, Any]):
    """
    Traite les messages de mise à jour de configuration.
    
    Args:
        topic: Le topic MQTT du message
        payload: Les données de configuration reçues
    """
    try:
        config_type = payload.get("type")
        config_value = payload.get("value")
        timestamp = payload.get("timestamp")
        
        await db_logger.debug(
            f"⚙️ Mise à jour de configuration reçue: {config_type} = {config_value} ⚡",
            source="mqtt_service",
            details={"type": config_type, "value": config_value, "timestamp": timestamp}
        )
        
        # Traiter selon le type de configuration
        if config_type == "auth_threshold":
            # Traitement spécifique pour le seuil d'authentification
            await db_logger.debug(
                f"🔐 Seuil d'authentification mis à jour: {config_value}",
                source="mqtt_service",
                details={"threshold": config_value}
            )

        elif config_type == "notifications":
            # Traitement pour les notifications
            await db_logger.debug(
                f"🔔 Configuration des notifications mise à jour: {config_value}",
                source="mqtt_service",
                details={"notifications_enabled": config_value}
            )

        else:
            await db_logger.warning(
                f"⚙️ Type de configuration non reconnu: {config_type} ⚠️",
                source="mqtt_service",
                details={"type": config_type, "value": config_value}
            )
            
    except Exception as e:
        await db_logger.error(
            f"⚙️ Erreur lors du traitement de la mise à jour de configuration: {str(e)} 🚨",
            source="mqtt_service",
            details={"erreur": str(e), "payload": payload}
        )

async def handle_system_commands(topic: str, payload: Dict[str, Any]):
    """
    Traite les commandes système reçues via MQTT.
    
    Args:
        topic: Le topic MQTT du message
        payload: Les données de commande reçues
    """
    try:
        command = payload.get("command")
        command_data = payload.get("data", {})
        timestamp = payload.get("timestamp")
        
        await db_logger.debug(
            f"🖥️ Commande système reçue: {command} ⚡",
            source="mqtt_service",
            details={"command": command, "data": command_data, "timestamp": timestamp}
        )
        
        # Traiter selon le type de commande
        if command == "shutdown":
            await db_logger.warning(
                "🔌 Commande d'arrêt système reçue 🚨",
                source="mqtt_service",
                details={"command": command}
            )
            
        elif command == "restart":
            await db_logger.warning(
                "🔄 Commande de redémarrage système reçue 🚨",
                source="mqtt_service",
                details={"command": command}
            )
            
        elif command == "refresh_modules":
            await db_logger.debug(
                "📡 Commande de rafraîchissement des modules reçue 🔄",
                source="mqtt_service",
                details={"command": command}
            )

            # Ré-abonner aux modules
            if mqtt_client:
                await mqtt_client.subscribe_to_all_modules()
                
        else:
            await db_logger.warning(
                f"🖥️ Commande système non reconnue: {command} ⚠️",
                source="mqtt_service",
                details={"command": command, "data": command_data}
            )
            
    except Exception as e:
        await db_logger.error(
            f"🖥️ Erreur lors du traitement de la commande système: {str(e)} 🚨",
            source="mqtt_service",
            details={"erreur": str(e), "payload": payload}
        )

# Instance globale du client MQTT
mqtt_client = MQTTClient()