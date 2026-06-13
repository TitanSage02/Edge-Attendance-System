from sqlalchemy import select, desc, func
from sqlalchemy.ext.asyncio import AsyncSession

from typing import List, Dict, Any, Optional
import json
import datetime

import logging
from pathlib import Path

from app.models.log import Log
from app.schemas.log import LogCreate
from app.core.config import settings

# Configuration des logs fichiers - utilise le chemin absolu
LOG_DIR = Path(settings.LOG_DIR).resolve()
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Configuration du logger fichier avec rotation quotidienne
from concurrent_log_handler import ConcurrentRotatingFileHandler
import shutil

class DateSuffixRotatingFileHandler(ConcurrentRotatingFileHandler):
    """
    Handler custom qui ajoute la date au nom du fichier lors de la rotation.
    Exemple : app_2024-05-16.log
    """
    def doRollover(self):
        super().doRollover()
        
        # Renomme le dernier backup avec la date du jour
        import datetime
        base_log = str(self.baseFilename)
        today_now = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        dated_name = base_log.replace('.log', f'_{today_now}.log')
        # Le dernier backup est base_log + ".1"
        backup_name = base_log + ".1"
        try:
            shutil.move(backup_name, dated_name)
        except Exception as e:
            # Si le fichier existe déjà ou autre erreur, ignorer
            pass

# Utilisation du handler custom
file_handler = DateSuffixRotatingFileHandler(
    LOG_DIR / "app.log",
    maxBytes=0.5*1024*1024,  # 0.5 Mo
    backupCount=180,
    encoding='utf-8',
    delay=False  # Créer le fichier immédiatement pour vérifier les permissions
)


# Logger pour les logs fichiers
file_logger = logging.getLogger('file_logger')
if settings.LOG_LEVEL == 'DEBUG':
    file_logger.setLevel(logging.DEBUG)
else:
    file_logger.setLevel(logging.INFO)


# Format des logs avec plus de détails
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s - %(levelname)s - [%(name)s] - %(message)s'
))

file_logger.addHandler(file_handler)

# Niveaux de log qui doivent aller en DB
DB_LOG_LEVELS = settings.DB_LOG_LEVELS

async def create_log(db: AsyncSession, log_data: LogCreate) -> Optional[Log]:
    """Crée un nouveau log"""
    try:
        # Convertir les détails en JSON si nécessaire
        details_str = None
        if log_data.details:
            # Fonction pour sérialiser les dates et autres types complexes
            def serialize_custom(obj):
                if isinstance(obj, (datetime.datetime, datetime.date)):
                    return obj.isoformat()
                elif hasattr(obj, '__dict__'):
                    return str(obj)
                elif hasattr(obj, 'name') and hasattr(obj, 'value'):
                    # Gestion des énumérations
                    return obj.name if hasattr(obj, 'name') else str(obj)
                return str(obj)
            
            # Sérialiser les détails avec gestion des dates et types complexes
            try:
                details_str = json.dumps(log_data.details, default=serialize_custom)
            except Exception as e:
                file_logger.error(f"❌ Erreur de sérialisation JSON: {str(e)}")
                # Fallback: convertir tous les détails en chaînes de caractères
                sanitized_details = {k: str(v) for k, v in log_data.details.items()}
                details_str = json.dumps(sanitized_details)
        
        # Créer l'entrée de log avec un timestamp
        current_time = datetime.datetime.now()
        db_log = Log(
            level=log_data.level,
            message=log_data.message,
            source=log_data.source,
            module_uid=log_data.module_uid,
            user_id=log_data.user_id,
            details=details_str,
            timestamp=current_time
        )
        
        # Enregistrer en DB uniquement si c'est requis
        if log_data.level in DB_LOG_LEVELS:
            try:
                db.add(db_log)
                await db.flush()
                await db.commit()
                await db.refresh(db_log)
                
            except Exception as e:
                # En cas d'erreur de base de données, on log dans le fichier                
                file_logger.error(
                    f"❌ Problème de journalisation en base de données: {str(e)}",
                    extra={
                        'source': 'système'
                    }
                )
                # On continue l'exécution même si l'enregistrement en DB échoue
        
        return db_log
        
    except Exception as e:
        file_logger.error(
            f"❌ Échec de la journalisation", 
            extra={
                'source': 'log_service'
            }
        )
        return None

async def get_logs(
    db: AsyncSession, 
    skip: int = 0, 
    limit: int = 100,
    level: Optional[str] = None,
    source: Optional[str] = None,
    module_uid: Optional[int] = None
) -> List[Log]:
    """Récupère les logs avec filtres optionnels."""
    query = select(Log).order_by(desc(Log.timestamp))
    
    if level:
        query = query.filter(Log.level == level)
    if source:
        query = query.filter(Log.source == source)
    if module_uid:
        query = query.filter(Log.module_uid == module_uid)
    
    result = await db.execute(query.offset(skip).limit(limit))
    return result.scalars().all()

async def count_logs_by_level(db: AsyncSession, level: str) -> int:
    """Compte le nombre de logs pour un niveau spécifique."""
    query = select(func.count(Log.id)).filter(Log.level == level)
    result = await db.execute(query)
    count = result.scalar_one_or_none()
    return count if count is not None else 0

# Fonction utilitaire pour journaliser facilement
async def log_event(
    db: AsyncSession, 
    level: str,
    message: str,
    source: str,
    module_uid: Optional[int] = None,
    user_id: Optional[int] = None,
    details: Optional[Dict[str, Any]] = None
) -> Optional[Log]:
    """Utilitaire pour créer facilement un log."""
    
    # Sanitize details pour éviter les erreurs de sérialisation
    if details:
        try:
            # Tester la sérialisation
            def serialize_custom(obj):
                if isinstance(obj, (datetime.datetime, datetime.date)):
                    return obj.isoformat()
                elif hasattr(obj, '__dict__'):
                    return str(obj)
                elif hasattr(obj, 'name') and hasattr(obj, 'value'):
                    # Gestion des énumérations
                    return obj.name if hasattr(obj, 'name') else str(obj)
                return str(obj)
            
            # Vérifier que les détails sont sérialisables
            json.dumps(details, default=serialize_custom)
        except Exception as e:
            # En cas d'erreur, convertir tous les éléments en chaînes
            details = {k: str(v) for k, v in details.items()}
    
    log_data = LogCreate(
        level=level,
        message=message,
        source=source,
        module_uid=module_uid,
        user_id=user_id,
        details=details
    )

    # Log dans le fichier pour tous les niveaux
    log_message = f"[{source}] {message}"
    if details:
        try:
            log_message += f" {json.dumps(details, default=lambda x: str(x))}"
        except:
            log_message += f" Details: [non-serializable]"
    
    if level == 'ERROR':
        file_logger.error(log_message)
    elif level == 'WARNING':
        file_logger.warning(log_message)
    elif level == 'INFO':
        file_logger.info(log_message)
    elif level == 'DEBUG':
        file_logger.debug(log_message)
    elif level == 'CRITICAL':
        file_logger.critical(log_message)

    return await create_log(db, log_data)

class Logger:
    """Classe pour la gestion des logs"""
    
    async def _log(self, level: str, msg: str, source: str = None, module_uid: int = None, user_id: int = None, **kwargs):
        """Méthode interne pour gérer tous les niveaux de log"""
        from app.db.session import AsyncSessionLocal
        
        # Sanitize kwargs pour éviter les erreurs de sérialisation
        if kwargs:
            sanitized_kwargs = {}
            for k, v in kwargs.items():
                try:
                    # Tester si la sérialisation est possible
                    json.dumps({k: v}, default=lambda x: str(x))
                    sanitized_kwargs[k] = v
                except:
                    # En cas d'erreur, convertir en chaîne
                    sanitized_kwargs[k] = str(v)
            kwargs = sanitized_kwargs
        
        # Obtenir une session de base de données
        try:
            # Créer explicitement une session avec un gestionnaire de contexte
            async with AsyncSessionLocal() as db:
                await log_event(
                    db=db,
                    level=level,
                    message=msg,
                    source=source,
                    module_uid=module_uid,
                    user_id=user_id,
                    details=kwargs if kwargs else None
                )

        except Exception as e:
            # Si la journalisation échoue, imprimer l'erreur (en dernier recours)
            print(f"❗ ERREUR SYSTÈME CRITIQUE - Journalisation impossible : {str(e)}")
            
            # Essayer de faire un log de base dans le fichier sans passer par la DB
            try:
                file_logger.error(f"[{source}] {msg} - Échec de journalisation DB: {str(e)}")
            except:
                pass
        
    async def info(self, msg, source=None, module_uid=None, user_id=None, **kwargs):
        return await self._log("INFO", msg, source, module_uid, user_id, **kwargs)

    async def warning(self, msg, source=None, module_uid=None, user_id=None, **kwargs):
        return await self._log("WARNING", msg, source, module_uid, user_id, **kwargs)

    async def error(self, msg, source=None, module_uid=None, user_id=None, **kwargs):
        return await self._log("ERROR", msg, source, module_uid, user_id, **kwargs)

    async def debug(self, msg, source=None, module_uid=None, user_id=None, **kwargs):
        return await self._log("DEBUG", msg, source, module_uid, user_id, **kwargs)
    
    async def critical(self, msg, source=None, module_uid=None, user_id=None, **kwargs):
        return await self._log("CRITICAL", msg, source, module_uid, user_id, **kwargs)
    
db_logger = Logger()