#!/usr/bin/env python3
"""
Point d'entrée principal d'Edge Attendance System
"""

import asyncio
import logging
import signal
import sys
from pathlib import Path
from datetime import datetime

# Configuration du chemin pour les imports
sys.path.append(str(Path(__file__).parent))

from utils.logger import setup_logger
from communication.mqtt_manager import MQTTManager  
from auth.auth_manager import AuthenticationManager
from sensors.camera import CameraController
from sensors.rfid import RFIDController
from sensors.feedback import FeedbackController
from data_manager import DataManager

from sensors.sensor import VL065XController
from config import config

class PresenceSystem:
    """Système principal de gestion de présence"""
    
    def __init__(self):

        self.feedback_controller = FeedbackController()
        self.feedback_controller.indicate_startup() # Indicateur visuel de démarrage

        self.logger = setup_logger(
            name="crec_presence_main",
            level=logging.DEBUG,
            console_level=logging.DEBUG,
            file_level=logging.DEBUG
        )
        
        self.data_manager = DataManager()
        self.camera_controller = CameraController(force_usb=False)
        self.rfid_controller = RFIDController()
        
        # Initialisation des composants
        self.mqtt_manager = MQTTManager()
        self.auth_manager = AuthenticationManager(
            data_manager=self.data_manager,
            camera_controller=self.camera_controller,
            rfid_controller=self.rfid_controller
        )

        # Capteur 
        self.sensor = VL065XController()

        # État du système
        self.is_running = False
        self.shutdown_event = asyncio.Event()
        
        # Statistiques
        self.detections_count = 0
        self.errors_count = 0
        
        self.logger.info("🚀 Edge Attendance System initialisé ")
        self.startup_time = datetime.now()
        
    async def initialize(self):
        """Initialise tous les composants du système"""
        try:
            self.logger.info("🔧 Initialisation des composants...")
            
            # Initialiser MQTT
            await self.mqtt_manager.connect()
            self.logger.info("✅ MQTT Manager initialisé")
            
            # Publier le statut "online" maintenant que MQTT est connecté
            try:
                status_data = {
                    "status": "online",
                    "module_uid": config.MODULE_ID,
                    "uptime": int((datetime.now() - self.startup_time).total_seconds()) if hasattr(self, 'startup_time') else 0,
                    "memory_usage": self._get_memory_usage(),
                    "cpu_usage": self._get_cpu_usage(),
                    "version": getattr(config, "VERSION", "1.0.0"),
                    "timestamp": datetime.now().isoformat()
                }
                
                # self.logger.info(f"📤 Tentative de publication du statut: {status_data}")
                # self.logger.info(f"🔌 État de connexion MQTT: {self.mqtt_manager.client.is_connected() if self.mqtt_manager.client else 'Client non initialisé'}")
                
                success = await self.mqtt_manager.publish_status(status_data)
                
                if not success:
                    self.logger.error("❌ Échec de la publication du statut 'online' sur MQTT")

                    # Tentative de reconnexion si échec
                    self.logger.info("🔄 Tentative de reconnexion MQTT...")
                    await self.mqtt_manager.disconnect()
                    await asyncio.sleep(2)
                    await self.mqtt_manager.connect()
                    
                    # Nouvelle tentative
                    success = await self.mqtt_manager.publish_status(status_data)
                    if success:
                        self.logger.info("✅ Statut 'online' publié sur MQTT après reconnexion")
                    else:
                        self.logger.error("❌ Échec définitif de la publication du statut")
                else:
                    self.logger.info("✅ Statut 'online' publié sur MQTT avec succès")
                    
            except Exception as e:
                self.logger.error(f"Erreur lors de la publication du statut: {e}")
                
                import traceback
                self.logger.error(f"Traceback: {traceback.format_exc()}")
            
            # Récupération des données des apprenants
            students_data = await self.data_manager.fetch_students_data()
            
            if students_data:
                self.logger.info(f"✅ Données des apprenants récupérées avec succès ({len(students_data)} étudiants)")
            else:
                self.logger.warning("⚠️ Aucune donnée étudiant disponible - Fonctionnement en mode démo/test")
            
            # # Initialiser et démarrer le capteur de présence
            # if self.sensor:
            #     await self.sensor.start_monitoring(
            #         callback=self.on_presence_detected,
            #         polling_interval=0.5
            #     )
            #     self.logger.info("✅ Capteur de présence initialisé et démarré")
            
            self.logger.info("🎉 Tous les composants sont initialisés avec succès")
            
        except Exception as e:
            self.logger.error(f"❌ Erreur lors de l'initialisation: {e}")
            raise
    
    async def on_presence_detected(self):
        """Callback appelé lors de détection de présence"""
        try:
            self.logger.info("🎯 Début du callback de présence...")
            self.detections_count += 1
            self.logger.info(f"👤 Présence détectée ! (Détection numéro: {self.detections_count})")
            
            # on appelle auth_manager pour vérifier l'authentification
            self.logger.info("🔄 Appel de l'authentification...")
            result = await self.auth_manager.authenticate_student()

            if result and result.success:
                # Feedback de succès
                await self.feedback_controller.indicate_success()


                self.logger.info(f"✅ Authentification réussie pour l'étudiant ID: {result.student_id} avec méthode {result.method} (confiance: {result.confidence})")
                
                # Créer le message de présence MQTT
                presence_msg = {
                    "student_id": result.student_id,
                    "status": True,  # True pour présent
                    "module_uid": config.MODULE_ID,  # Identifiant unique du module
                    "timestamp": datetime.now().isoformat()
                }
                
                # Publier sur MQTT
                try:
                    await self.mqtt_manager.publish_presence(presence_msg)
                    self.logger.info("✅ Présence publiée sur MQTT")
                except Exception as mqtt_error:
                    self.logger.error(f"❌ Erreur lors de la publication MQTT: {mqtt_error}")
                    self.errors_count += 1
                
            else:
                await self.feedback_controller.indicate_failure()
                self.errors_count += 1
                error_msg = result.error if result else "Pas de résultat d'authentification"
                self.logger.warning(f"⚠️ Authentification échouée: {error_msg}")
            
            self.logger.info("🏁 Fin du callback de présence")

        except Exception as e:
            self.errors_count += 1
            self.logger.error(f"❌ Erreur lors du traitement de présence: {e}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")
    
    # async def start_monitoring(self):
    #     """Démarre la surveillance des capteurs"""
    #     try:
    #         self.logger.info("🔍 Démarrage de la surveillance...")
            
    #         while True:
               
    #             # Sortir de la boucle si le capteur est actif
    #             break
                
    #         self.logger.info("✅ Surveillance active - En attente de détections...")
                
    #     except Exception as e:
    #         self.logger.error(f"❌ Erreur lors du démarrage de la surveillance: {e}")
    #         raise
    
    # async def stop_monitoring(self):
    #     """Arrête la surveillance des capteurs"""
    #     try:
    #         self.logger.info("⏹️ Arrêt de la surveillance...")
            
    #         if self.sensor and hasattr(self.sensor, 'stop_monitoring'):
    #             self.sensor.stop_monitoring()
    #             self.logger.info("✅ Surveillance du capteur arrêtée")
                
    #     except Exception as e:
    #         self.logger.error(f"❌ Erreur lors de l'arrêt de la surveillance: {e}")
    
    async def cleanup(self):
        """Nettoie les ressources"""
        try:
            self.logger.info("🧹 Nettoyage des ressources...")
            
            # Publier le statut "offline" avant fermeture
            if self.mqtt_manager:
                try:
                    await self.mqtt_manager.publish_status({
                        "status": "offline",
                        "module_uid": config.MODULE_ID,
                        "uptime": int((datetime.now() - self.startup_time).total_seconds()) if hasattr(self, 'startup_time') else 0,
                        "shutdown_time": datetime.now().isoformat(),
                        "version": getattr(config, "VERSION", "1.0.0")
                    })
                    self.logger.info("✅ Statut 'offline' publié sur MQTT")
                except Exception as e:
                    self.logger.warning(f"⚠️ Erreur lors de la publication du statut offline: {e}")
            
            # # Arrêter la surveillance
            # await self.stop_monitoring()
            
            # Fermer MQTT
            if self.mqtt_manager:
                await self.mqtt_manager.disconnect()
                self.logger.info("✅ MQTT déconnecté")
            
            # Nettoyer le data manager
            if self.data_manager:
                # TODO : nettoyer datamanager
                self.logger.info("✅ Data Manager nettoyé")
            
            self.logger.info("🎉 Nettoyage terminé")
            
        except Exception as e:
            self.logger.error(f"❌ Erreur lors du nettoyage: {e}")
    
    def setup_signal_handlers(self):
        """Configure les gestionnaires de signaux"""
        def signal_handler(signum, frame):
            self.logger.info(f"📡 Signal {signum} reçu, arrêt en cours...")
            self.is_running = False
            self.shutdown_event.set()
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        self.logger.info("📡 Gestionnaires de signaux configurés")
    
    async def run(self):
        """Boucle principale du système"""
        try:
            self.logger.info("🚀 Démarrage d'Edge Attendance System")
            
            # Configurer les gestionnaires de signaux
            self.setup_signal_handlers()
            
            # Initialiser les composants
            await self.initialize()
            
            # Démarrer la surveillance
            # await self.start_monitoring()
            
            self.is_running = True
            self.logger.info("✅ Système opérationnel - En attente de détections...")
            
            # Variables de log de heartbeat
            last_heartbeat = asyncio.get_event_loop().time()
            last_status_update = asyncio.get_event_loop().time()
            heartbeat_interval = 5  # secondes
            status_update_interval = 30  # Publier le statut toutes les 30 secondes
            
            # Boucle principale
            while self.is_running:
                try:
                    # Log de heartbeat périodique
                    current_time = asyncio.get_event_loop().time()
                    if current_time - last_heartbeat >= heartbeat_interval:
                        self.logger.info(f"💓 Système actif ")
                        last_heartbeat = current_time
                    
                    # Publication périodique du statut pour maintenir la connexion
                    if current_time - last_status_update >= status_update_interval:
                        try:
                            status_data = {
                                "status": "online",
                                "module_uid": config.MODULE_ID,
                                "uptime": int((datetime.now() - self.startup_time).total_seconds()),
                                "memory_usage": self._get_memory_usage(),
                                "cpu_usage": self._get_cpu_usage(),
                                "version": getattr(config, "VERSION", "1.0.0"),
                                "timestamp": datetime.now().isoformat()
                            }
                            await self.mqtt_manager.publish_status(status_data)
                            self.logger.debug("📡 Statut heartbeat publié")
                            last_status_update = current_time
                        except Exception as e:
                            self.logger.warning(f"⚠️ Erreur publication heartbeat: {e}")

                    if not self.sensor:
                        self.logger.warning("⚠️ Aucun capteur disponible")
                        continue
                        
                    detection = self.sensor.detect_presence()
                    if detection:
                        self.logger.info("👤 Présence détectée par le capteur")
                        await self.on_presence_detected()
                        # Pause plus longue après une détection pour éviter les détections multiples
                        await asyncio.sleep(2)
                    else:
                        # Log moins fréquent pour les non-détections
                        current_time = asyncio.get_event_loop().time()
                        if current_time - last_heartbeat >= heartbeat_interval:
                            self.logger.debug("🔍 En attente de présence...")

                    # Pause courte entre les vérifications
                    await asyncio.sleep(0.5)  # Réduit de 3s à 0.5s pour plus de réactivité

                    # Vérifier l'événement de shutdown avec timeout court
                    try:
                        await asyncio.wait_for(self.shutdown_event.wait(), timeout=0.1)
                        # Si on arrive ici, c'est qu'un signal a été reçu
                        self.logger.info("🛑 Signal d'arrêt reçu")
                        break
                    except asyncio.TimeoutError:
                        # Timeout normal, continuer la boucle
                        continue
                        
                except Exception as e:
                    self.errors_count += 1
                    self.logger.error(f"❌ Erreur dans la boucle principale: {e}")

            self.logger.info("🏁 Arrêt du système demandé")
            
        except Exception as e:
            self.logger.error(f"❌ Erreur critique dans le système: {e}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            raise
        finally:
            self.is_running = False
            await self.cleanup()
            self.logger.info("🎯 Système arrêté proprement")

    def _get_memory_usage(self) -> float:
        """
        Obtient l'utilisation mémoire actuelle (en MB)
        
        Returns:
            float: Utilisation mémoire en MB
        """
        try:
            import psutil
            process = psutil.Process()
            memory_info = process.memory_info()
            return memory_info.rss / 1024 / 1024  # Convertir en MB
        except Exception as e:
            self.logger.warning(f"Impossible d'obtenir l'utilisation mémoire: {e}")
            return 0.0
            
    def _get_cpu_usage(self) -> float:
        """
        Obtient l'utilisation CPU actuelle (en pourcentage)
        
        Returns:
            float: Utilisation CPU en pourcentage (0-100)
        """
        try:
            import psutil
            return psutil.cpu_percent(interval=0.1)
        except Exception as e:
            self.logger.warning(f"Impossible d'obtenir l'utilisation CPU: {e}")
            return 0.0

async def main():
    """Point d'entrée principal"""
    # Configuration du logging
    logger = setup_logger(
        name="crec_presence_main",
        level=logging.DEBUG,
        console_level=logging.DEBUG,
        file_level=logging.DEBUG
    )

    logger.info("=" * 60)
    logger.info("🚀 DÉMARRAGE D'EDGE ATTENDANCE SYSTEM")
    logger.info("=" * 60)
    
    try:
        # Créer et lancer le système
        system = PresenceSystem()
        await system.run()
        
    except KeyboardInterrupt:
        logger.info("🛑 Interruption clavier détectée")
    except Exception as e:
        logger.error(f"❌ Erreur fatale: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        sys.exit(1)
    
    logger.info("👋 Au revoir !")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Arrêt forcé par l'utilisateur")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Erreur lors du démarrage: {e}")
        sys.exit(1)
