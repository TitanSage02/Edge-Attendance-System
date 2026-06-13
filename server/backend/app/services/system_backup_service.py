"""
Service de sauvegarde système complète.
Permet de sauvegarder la base de données, les fichiers de configuration et autres éléments critiques.
"""

import os
import json
import shutil
import sqlite3
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
import tempfile

from app.core.config import settings
from app.services.log_service import db_logger


class SystemBackupService:
    """Service de sauvegarde système complète."""
    
    def __init__(self):
        # Utiliser les configurations centralisées
        self.backup_dir = Path(settings.BACKUP_DIR)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Chemins des éléments à sauvegarder depuis la configuration
        self.database_path = Path(settings.backup_database_path)
        self.config_dir = Path(settings.BACKUP_CONFIG_DIR)
        self.logs_dir = Path(settings.BACKUP_LOGS_DIR)
        self.env_file = Path(settings.BACKUP_ENV_FILE)
        
        # Créer les répertoires nécessaires s'ils n'existent pas
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        
        # Paramètres de sauvegarde depuis la configuration
        self.max_backups = settings.BACKUP_MAX_COUNT
        self.compression_level = settings.BACKUP_COMPRESSION_LEVEL
        self.logs_retention_days = settings.BACKUP_LOGS_RETENTION_DAYS
        
    async def create_system_backup(
        self, 
        backup_name: Optional[str] = None,
        include_database: bool = True,
        include_config: bool = True,
        include_logs: bool = False,
        created_by: str = "system"
    ) -> Dict[str, Any]:
        """Crée une sauvegarde complète du système."""
        try:
            # Générer le nom de sauvegarde
            if not backup_name:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_name = f"system_backup_{timestamp}.zip"
            elif not backup_name.endswith('.zip'):
                backup_name += '.zip'
            
            backup_path = self.backup_dir / backup_name
            
            # Créer un dossier temporaire pour assembler la sauvegarde
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                
                # Métadonnées de la sauvegarde
                metadata = {
                    'created_at': datetime.now().isoformat(),
                    'created_by': created_by,
                    'backup_type': 'system_complete',
                    'includes': {
                        'database': include_database,
                        'config': include_config,
                        'logs': include_logs
                    },
                    'version': '1.0.0'
                }
                  # Sauvegarde de la base de données
                if include_database and self.database_path.exists():
                    await self._backup_database(temp_path)
                    # await db_logger.debug("Base de données incluse dans la sauvegarde", source="system_backup")
                
                # Sauvegarde des fichiers de configuration
                if include_config:
                    await self._backup_config_files(temp_path)
                    # await db_logger.debug("Fichiers de configuration inclus dans la sauvegarde", source="system_backup")
                
                # Sauvegarde des logs (optionnel)
                if include_logs and self.logs_dir.exists():
                    await self._backup_logs(temp_path)
                    # await db_logger.debug("Fichiers de logs inclus dans la sauvegarde", source="system_backup")
                
                # Sauvegarde des métadonnées
                metadata_file = temp_path / "backup_metadata.json"
                with open(metadata_file, 'w', encoding='utf-8') as f:
                    json.dump(metadata, f, indent=2, ensure_ascii=False)
                
                # Créer l'archive ZIP
                await self._create_zip_archive(temp_path, backup_path)
            
            # Calculer la taille du fichier
            file_size = backup_path.stat().st_size
            
            # Nettoie des anciennes sauvegardes si nécessaire
            await self._cleanup_old_backups()
            await db_logger.debug(
                f"💾 Sauvegarde système {backup_name} créée avec succès par {created_by}. Taille : {file_size // 1024} KB",
                source="sauvegarde"
            )
            
            return {
                'success': True,
                'backup_path': str(backup_path),
                'backup_name': backup_name,
                'size': file_size,
                'created_at': metadata['created_at'],
                'created_by': created_by,
                'includes': metadata['includes']
            }
        
        except Exception as e:
            await db_logger.error(
                f"💾 Erreur lors de la création de sauvegarde système. Erreur : {str(e)}",
                source="sauvegarde"
            )

            raise Exception(f"Impossible de créer la sauvegarde système: {str(e)}")
    
    async def _backup_database(self, temp_dir: Path) -> None:
        """Sauvegarde la base de données SQLite."""
        try:
            db_backup_dir = temp_dir / "database"
            db_backup_dir.mkdir(exist_ok=True)
            
            # Copie le fichier de base de données principal
            if self.database_path.exists():
                shutil.copy2(self.database_path, db_backup_dir / self.database_path.name)
            
            # # Copie les fichiers WAL et SHM si ils existent (SQLite)
            # for ext in ['-wal', '-shm']:
            #     wal_file = Path(str(self.database_path) + ext)
            #     if wal_file.exists():
            #         shutil.copy2(wal_file, db_backup_dir / wal_file.name)        
        except Exception as e:
            await db_logger.error(
                f"💾 Erreur lors de la sauvegarde de la base de données ❌. Erreur : {str(e)}.", 
                source="sauvegarde", 
                )
            raise
    
    async def _backup_config_files(self, temp_dir: Path) -> None:
        """Sauvegarde les fichiers de configuration."""
        try:
            config_backup_dir = temp_dir / "config"
            config_backup_dir.mkdir(exist_ok=True)
            
            # Copier tous les fichiers de configuration
            if self.config_dir.exists():
                for item in self.config_dir.iterdir():
                    if item.is_file() and not item.name.startswith('backup'):
                        # Évite de sauvegarder les fichiers de sauvegarde existants
                        if not any(pattern in item.name.lower() for pattern in ['backup', '.tmp', '.log']):
                            shutil.copy2(item, config_backup_dir / item.name)
                    elif item.is_dir() and item.name != 'backups':
                        shutil.copytree(item, config_backup_dir / item.name, ignore=shutil.ignore_patterns('*.tmp', '*.log'))
            
            # Copier le fichier de configuration principal si il existe
            if self.env_file.exists():
                shutil.copy2(self.env_file, config_backup_dir / self.env_file.name)
     
        except Exception as e:
            await db_logger.error(
                f"⚙️ Erreur lors de la sauvegarde des fichiers de configuration. Erreur : {str(e)}", 
                source="sauvegarde"
                )
            raise
    
    async def _backup_logs(self, temp_dir: Path) -> None:
        """Sauvegarde les fichiers de logs."""
        try:
            logs_backup_dir = temp_dir / "logs"
            logs_backup_dir.mkdir(exist_ok=True)
            
            if self.logs_dir.exists():
                # Copier seulement les logs récents selon la configuration
                cutoff_time = datetime.now().timestamp() - (self.logs_retention_days * 24 * 3600)
                
                for log_file in self.logs_dir.glob("*.log"):
                    if log_file.stat().st_mtime > cutoff_time:
                        shutil.copy2(log_file, logs_backup_dir / log_file.name)
        
        except Exception as e:
            await db_logger.error(
                f"📄 Erreur lors de la sauvegarde des logs ❌. Erreur : {str(e)}.", 
                source="sauvegarde", 
                )
            raise
    
    async def _create_zip_archive(self, source_dir: Path, output_path: Path) -> None:
        """Crée une archive ZIP de la sauvegarde."""
        try:
            with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=self.compression_level) as zipf:
                for root, dirs, files in os.walk(source_dir):
                    for file in files:
                        file_path = Path(root) / file
                        arcname = file_path.relative_to(source_dir)
                        zipf.write(file_path, arcname)
        
        except Exception as e:
            await db_logger.error(
                f"📦 Erreur lors de la création de l'archive ZIP. Erreur : {str(e)}.",
                  source="sauvegarde" 
                )
            raise
    
    async def _cleanup_old_backups(self) -> None:
        """Nettoie les anciennes sauvegardes selon la politique de rétention."""
        try:
            # Utiliser la configuration pour le nombre maximum de sauvegardes
            backup_files = list(self.backup_dir.glob("system_backup_*.zip"))
            backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
           
            # Supprimer les anciennes sauvegardes
            for old_backup in backup_files[self.max_backups:]:
                old_backup.unlink()
                await db_logger.warning(
                    f"Ancienne sauvegarde {old_backup.name} supprimée.", 
                    source="system_backup"
                    )
                
        except Exception as e:
            await db_logger.error(
                f"Erreur lors du nettoyage des anciennes sauvegardes: {str(e)}", 
                source="system_backup"
                )
            pass
    
    async def list_system_backups(self) -> List[Dict[str, Any]]:
        """Liste toutes les sauvegardes système disponibles."""
        try:
            backups = []
            
            for backup_file in self.backup_dir.glob("system_backup_*.zip"):
                try:
                    stat = backup_file.stat()
                    
                    # Essayer de lire les métadonnées depuis l'archive
                    metadata = {}
                    try:
                        with zipfile.ZipFile(backup_file, 'r') as zipf:
                            if 'backup_metadata.json' in zipf.namelist():
                                with zipf.open('backup_metadata.json') as f:
                                    metadata = json.loads(f.read().decode('utf-8'))
                    except:
                        pass
                    
                    backups.append({
                        'name': backup_file.name,
                        'size': stat.st_size,
                        'created_at': metadata.get('created_at', datetime.fromtimestamp(stat.st_mtime).isoformat()),
                        'created_by': metadata.get('created_by', 'inconnu'),
                        'backup_type': metadata.get('backup_type', 'system_complete'),
                        'includes': metadata.get('includes', {}),
                        'path': str(backup_file)
                    })
                except Exception as e:
                    await db_logger.warning(
                        f"⚠️ Erreur lors de la lecture des métadonnées pour {backup_file.name}. Erreur : {str(e)}", 
                        source="system_backup"
                        )
                    continue
            
            # Trier par date de création (plus récent en premier)
            backups.sort(key=lambda x: x['created_at'], reverse=True)
            
            return backups
        
        except Exception as e:
            await db_logger.error(
                f"📋 Une erreur s'est produite lors de la liste des sauvegardes système. Erreur : {str(e)}", 
                source="system_backup"
            )
            return []

    async def restore_system_backup(self, backup_name: str, restored_by: str) -> Dict[str, Any]:
        """Restaure une sauvegarde système (ATTENTION: opération critique)."""
        try:
            backup_path = self.backup_dir / backup_name
            
            if not backup_path.exists():
                raise FileNotFoundError(f"Sauvegarde système non trouvée: {backup_name}")
            
            # Créer une sauvegarde de sécurité avant restauration
            security_backup = await self.create_system_backup(
                backup_name=f"pre_restore_security_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                created_by=f"auto_before_restore_by_{restored_by}"
            )
            
            await db_logger.warning(
                f"🛡️ Sauvegarde de sécurité créée: {security_backup['backup_name']} par {restored_by}.",
                source="system_backup"
            )
            
            # Extraire et restaurer la sauvegarde
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                
                # Extraire l'archive
                with zipfile.ZipFile(backup_path, 'r') as zipf:
                    zipf.extractall(temp_path)
                
                # Lire les métadonnées
                metadata_file = temp_path / "backup_metadata.json"
                if metadata_file.exists():
                    with open(metadata_file, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                else:
                    metadata = {}
                
                includes = metadata.get('includes', {})
                
                # Restaurer la base de données si incluse
                if includes.get('database', False):
                    await self._restore_database(temp_path)
                
                # Restaurer les fichiers de configuration si inclus
                if includes.get('config', False):
                    await self._restore_config_files(temp_path)
                    await db_logger.warning(
                                    f"🔄 Restauration système initiée par {restored_by} terminée avec succès. Nom de la sauvegarde : {backup_name}.",
                                    source="restauration"                                 
                                )
            
            return {
                'success': True,
                'restored_from': backup_name,
                'restored_by': restored_by,
                'restored_at': datetime.now().isoformat(),
                'security_backup': security_backup['backup_name'],
                'includes': includes
            }
        
        except Exception as e:           
            await db_logger.error(
                f"❌ ÉCHEC DE LA RESTAURATION SYSTÈME",
                source="system_backup",              
            )

        raise Exception(f"Impossible de restaurer la sauvegarde système: {str(e)}")
    
    async def _restore_database(self, backup_dir: Path) -> None:
        """Restaure la base de données depuis la sauvegarde."""
        try:
            db_backup_dir = backup_dir / "database"
            if not db_backup_dir.exists():
                return
            
            # TODO : Fermer les connexions existantes si possible
            # (Note: cela nécessiterait une gestion plus sophistiquée en prod ...) 
            
            backup_db_file = db_backup_dir / self.database_path.name
            if backup_db_file.exists():
                # Sauvegarder l'ancienne base de données
                if self.database_path.exists():
                    old_db = self.database_path.with_suffix('.old')
                    if old_db.exists():
                        old_db.unlink()

                    shutil.move(self.database_path, old_db)
                
                # Restaurer la nouvelle base de données
                shutil.copy2(backup_db_file, self.database_path)
                await db_logger.debug(
                    "💾 Base de données restaurée avec succès",
                    source="system_backup"
                )

        except Exception as e:            
            await db_logger.error(
                "❌ Échec de restauration de la base de données",
                source="restauration"
            )
            raise
    
    async def _restore_config_files(self, backup_dir: Path) -> None:
        """Restaure les fichiers de configuration depuis la sauvegarde."""
        try:
            config_backup_dir = backup_dir / "config"
            if not config_backup_dir.exists():
                return
            
            # Sauvegarder les anciens fichiers de config
            old_config_dir = self.config_dir.parent / "config_old"
            if old_config_dir.exists():
                shutil.rmtree(old_config_dir)
            
            if self.config_dir.exists():
                shutil.copytree(self.config_dir, old_config_dir)
            
            # Restaurer les nouveaux fichiers de configuration
            for item in config_backup_dir.iterdir():
                target_path = self.config_dir / item.name

                if item.is_file():
                    if target_path.exists():
                        target_path.unlink()
                    shutil.copy2(item, target_path)
               
                elif item.is_dir():
                    if target_path.exists():
                        shutil.rmtree(target_path)
                    shutil.copytree(item, target_path)
            
            await db_logger.debug(
                "✅ Configuration système restaurée avec succès",
                source="system_backup"
            )
            
        except Exception as e:            
            await db_logger.error(
                "❌ Échec de restauration de la configuration",
                source="system_backup"
            )
            raise


# Instance singleton
system_backup_service = SystemBackupService()