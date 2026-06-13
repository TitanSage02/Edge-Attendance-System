"""
Service pour la gestion des paramètres de l'application.
"""

import json
import os
from datetime import datetime
from typing import Optional, Dict, Any, List
from pathlib import Path
from app.core.config import settings
from app.schemas.settings import AllSettings, SystemSettings, BackupSettings
from app.services.log_service import db_logger
from app.services.system_backup_service import system_backup_service
from app.services.mqtt_service import mqtt_client


class SettingsService:
    """Service de gestion des paramètres de l'application."""
    
    def __init__(self):
        self.settings_file = Path(settings.SETTINGS_FILE_PATH)
        self.settings_file.parent.mkdir(exist_ok=True)
        self._default_settings = self._get_default_settings()
    
    def _get_default_settings(self) -> AllSettings:
        """Retourne les paramètres par défaut."""
        return AllSettings(
            system=SystemSettings(
                current_promotion="2024-2025",
                notifications_enabled=True,
                max_login_attempts=5
            ),

            backup=BackupSettings(
                auto_backup_enabled=True,
                backup_frequency_hours=24,
                max_backup_files=10,
                include_database=True,
                include_config=True,
                include_logs=False
            )
        )
    
    async def get_settings(self) -> Dict[str, Any]:
        """Récupère tous les paramètres avec métadonnées."""
        try:
            if self.settings_file.exists():
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Valider les données
                settings = AllSettings(**data.get('settings', {}))
                
                return {
                    'settings': settings.model_dump(),
                    'last_updated': data.get('last_updated'),
                    'updated_by': data.get('updated_by'),
                    'message': 'Paramètres récupérés avec succès'
                }
            
            else:
                # Créer le fichier avec les paramètres par défaut
                await self.save_settings(self._default_settings, "system")
                return {
                    'settings': self._default_settings.model_dump(),
                    'last_updated': None,
                    'updated_by': None,
                    'message': 'Paramètres par défaut initialisés'
                }
            
        except Exception as e:
            await db_logger.error(
                f"Une erreur s'est produite lors de la récupération des paramètres. Erreur : {str(e)}",
                source="settings_service"
            )

            return {
                'settings': self._default_settings.dict(),
                'last_updated': None,
                'updated_by': None,
                'message': 'Paramètres par défaut (erreur de lecture)'
            }

    async def save_settings(self, settings: AllSettings, updated_by: str) -> Dict[str, Any]:
        """Sauvegarde les paramètres."""
        try:
            # Vérifier si nous avons besoin de propager le seuil d'alerte d'authentification
            old_auth_threshold = None
            new_auth_threshold = settings.system.max_login_attempts
            
            # Récupérer l'ancienne valeur si le fichier existe
            if self.settings_file.exists():
                try:
                    with open(self.settings_file, 'r', encoding='utf-8') as f:
                        old_data = json.load(f)
                    old_settings = old_data.get('settings', {})
                    old_system = old_settings.get('system', {})
                    old_auth_threshold = old_system.get('max_login_attempts')
                except Exception:
                    pass
            
            data = {
                'settings': settings.model_dump(),
                'last_updated': datetime.now().isoformat(),
                'updated_by': updated_by
            }
            
            # Sauvegarde avec backup de l'ancien fichier
            if self.settings_file.exists():
                backup_file = self.settings_file.with_suffix('.backup')
                # Supprimer le fichier de sauvegarde s'il existe déjà
                if backup_file.exists():
                    backup_file.unlink()
                self.settings_file.rename(backup_file)
            
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            await db_logger.debug(
                f"Paramètres sauvegardés par {updated_by}",
                source="settings_service"
            )
            
            # Propager le seuil d'alerte d'authentification aux modules via MQTT si changé
            if old_auth_threshold is None or old_auth_threshold != new_auth_threshold:
                try:
                    await mqtt_client.publish_auth_threshold_update(new_auth_threshold)
                    await db_logger.debug(
                        f"Le seuil d'alerte des modules a été mis à jour à {new_auth_threshold} par {updated_by}",
                        source="settings_service"
                    )

                except Exception as e:
                    await db_logger.error(
                        f" Une erreur s'est produite lors de la propagation du seuil d'alerte d'authentification. Erreur : {str(e)}",
                        source="settings_service"
                    )
            
            return {
                'settings': settings.model_dump(),
                'last_updated': data['last_updated'],
                'updated_by': updated_by,
                'message': 'Paramètres sauvegardés avec succès'
            }
        
        except Exception as e:
            await db_logger.error(
                f"Une erreur s'est produite lors de la sauvegarde des paramètres: {str(e)}",
                source="settings_service"
            )

            raise Exception(f"Impossible de sauvegarder les paramètres: {str(e)}")

    async def update_partial_settings(self, 
                                    updates: Dict[str, Any], 
                                    updated_by: str) -> Dict[str, Any]:
        """Met à jour partiellement les paramètres."""
        current_data = await self.get_settings()
        current_settings = AllSettings(**current_data['settings'])
        
        # Vérifier si le seuil d'alerte d'authentification est mis à jour
        auth_threshold_updated = False
        new_auth_threshold = None
        
        # Appliquer les mises à jour
        if 'system' in updates:
            for key, value in updates['system'].items():
                if hasattr(current_settings.system, key):
                    # Vérifier si c'est le paramètre max_login_attempts
                    if key == 'max_login_attempts' and value != getattr(current_settings.system, key):
                        auth_threshold_updated = True
                        new_auth_threshold = value
                    setattr(current_settings.system, key, value)
        
        if 'security' in updates:
            for key, value in updates['security'].items():
                if hasattr(current_settings.security, key):
                    setattr(current_settings.security, key, value)

        if 'backup' in updates:
            for key, value in updates['backup'].items():
                if hasattr(current_settings.backup, key):
                    setattr(current_settings.backup, key, value)
        
        result = await self.save_settings(current_settings, updated_by)
        
        # Propager le seuil d'alerte d'authentification aux modules via MQTT
        if auth_threshold_updated and new_auth_threshold is not None:
            try:
                await mqtt_client.publish_auth_threshold_update(new_auth_threshold)
                await db_logger.debug(
                    f"Le seuil d'alerte d'authentification pour les modules a été mis à jour à {new_auth_threshold} par {updated_by}",
                    source="settings_service"
                )

            except Exception as e:
                await db_logger.error(
                    f"Une erreur s'est produite lors de la propagation du seuil d'alerte d'authentification. Erreur : {str(e)}",
                    source="settings_service"
                )
        
        return result
    
    async def republish_system_settings(self):
        """Republier les paramètres système via MQTT après modification."""
        try:
            from app.services.mqtt_service import publish_system_settings
            await publish_system_settings()
        except Exception as e:
            await db_logger.error(
                f"Erreur lors de la republication des paramètres système sur le broker MQTT. Erreur : {str(e)}",
                source="settings_service",
            )
    
    async def reset_to_defaults(self, updated_by: str) -> Dict[str, Any]:
        """Remet les paramètres aux valeurs par défaut."""
        return await self.save_settings(self._default_settings, updated_by)

    async def get_system_info(self) -> Dict[str, Any]:
        """Retourne des informations système."""
        
        from app.db.session import AsyncSessionLocal
        from sqlalchemy import text
        
        try:
            settings_data = await self.get_settings()
            
            # Vérification de la base de données
            db_status = "healthy"
            active_users = 0
            
            try:
                async with AsyncSessionLocal() as db:
                    # Test de connexion DB
                    await db.execute(text("SELECT 1"))
                    # Compter les utilisateurs actifs (connectés dans les dernières 24h)
                    result = await db.execute(text("""
                        SELECT COUNT(*) FROM users 
                        WHERE last_login > NOW() - INTERVAL '1 day'
                    """))
                    active_users = result.scalar() or 0
                    
            except Exception as db_err:
                await db_logger.error(f"Erreur DB lors de get_system_info: {str(db_err)}")
                db_status = "error"
            
            # Vérification de l'état MQTT
            mqtt_status = "disconnected"
            try:
                from app.services.mqtt_service import mqtt_client
                if mqtt_client and mqtt_client.connected:
                    mqtt_status = "connected"
            except Exception as mqtt_err:
                await db_logger.error(f"Erreur MQTT lors de get_system_info: {str(mqtt_err)}")
                mqtt_status = "error"
            
            # Vérification de la dernière sauvegarde
            backup_dir = Path(settings.BACKUP_DIR)
            last_backup = None
            backup_files = list(backup_dir.glob("settings.backup*"))
            if backup_files:
                latest_backup = max(backup_files, key=lambda f: f.stat().st_mtime)
                last_backup = datetime.fromtimestamp(latest_backup.stat().st_mtime).isoformat()
            
            # Santé générale du système
            system_health = "healthy"
            if db_status != "healthy" or mqtt_status == "error":
                system_health = "warning"
            
            return {
                'current_promotion': settings_data['settings']['system']['current_promotion'],
                'notifications_enabled': settings_data['settings']['system']['notifications_enabled'],
                'last_backup': last_backup,
                'system_health': system_health,
                'version': '1.0.0',
                'active_users': active_users,
                'database_status': db_status,
                'mqtt_status': mqtt_status
            }
            
        except Exception as e:
            await db_logger.error(
                f"Une erreur s'est produite lors de la récupération des informations système: {str(e)}",
                source="settings_service"
            )

            return {
                'current_promotion': '2024-2025',
                'notifications_enabled': True,
                'last_backup': None,
                'system_health': 'unknown',
                'version': '1.0.0',
                'active_users': 0,
                'database_status': 'unknown',
                'mqtt_status': 'unknown'
            }
    
    async def create_backup(self, backup_name: Optional[str] = None, created_by: str = "system") -> Dict[str, Any]:
        """Crée une sauvegarde système complète."""
        try:
            # Obtenir les paramètres de sauvegarde actuels
            current_settings = await self.get_settings()
            backup_settings = current_settings.get('settings', {}).get('backup', {})
            
            # Utiliser le nouveau service de sauvegarde système
            result = await system_backup_service.create_system_backup(
                backup_name=backup_name,
                include_database=backup_settings.get('include_database', True),
                include_config=backup_settings.get('include_config', True),
                include_logs=backup_settings.get('include_logs', False),
                created_by=created_by
            )
            
            await db_logger.debug(
                f"Une sauvegarde système {result['backup_name']} a été créée par {created_by}",
                source="settings_service"
            )
            
            return result
            
        except Exception as e:
            await db_logger.error(
                f"Une erreur s'est produite lors de la création de sauvegarde système. Erreur : {str(e)}",
                source="settings_service"
            )

            raise Exception(f"Impossible de créer la sauvegarde système: {str(e)}")
    
    async def restore_backup(self, backup_name: str, restored_by: str) -> Dict[str, Any]:
        """Restaure une sauvegarde système."""
        try:
            # Utiliser le nouveau service de restauration système
            result = await system_backup_service.restore_system_backup(backup_name, restored_by)
            
            # Recharger les paramètres après restauration
            await self.refresh_settings()
            
            await db_logger.debug(
                f"{restored_by} a restauré la sauvegarde système {backup_name}.",
                source="settings_service"
            )
            
            return result
            
        except Exception as e:
            await db_logger.error(
                f"Une erreur s'est produite lors de la restauration de sauvegarde système. Erreur : {str(e)}",
                source="settings_service"
            )
            raise Exception(f"Impossible de restaurer la sauvegarde système: {str(e)}")
    
    async def list_backups(self) -> List[Dict[str, Any]]:
        """Liste toutes les sauvegardes système disponibles."""
        try:
            backups = await system_backup_service.list_system_backups()
            return backups
            
        except Exception as e:
            await db_logger.error(
                f"Erreur lors de la liste des sauvegardes système: {str(e)}",
                source="settings_service"
            )
            return []
    
    async def refresh_settings(self) -> None:
        """Recharge les paramètres depuis le fichier."""
        # Cette méthode sera utilisée après une restauration
        # A implémenter dans les versions suivantes
        pass


# Instance singleton
settings_service = SettingsService()
