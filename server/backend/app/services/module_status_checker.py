import asyncio
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from typing import List

from app.models.module_status import ModuleStatus
from app.schemas.module_status import ModuleStatusCreate
from app.models.module import ModuleStatus as ModuleStatusEnum
from app.services.module_status_service import update_module_status
from app.services.log_service import db_logger
from app.api.v1.deps import get_db
from app.db.session import AsyncSessionLocal

# Durée d'inactivité après laquelle un module est considéré comme hors ligne
OFFLINE_THRESHOLD = timedelta(minutes=2)  # 2 minutes

async def check_modules_status():
    """
    Vérifie périodiquement le statut de tous les modules.
    Si un module n'a pas envoyé de statut depuis OFFLINE_THRESHOLD, le marquer comme offline.
    """
    try:
        async for db in get_db():
            # Récupérer tous les modules actuellement "online"
            query = select(ModuleStatus).filter(ModuleStatus.status == ModuleStatusEnum.online)
            result = await db.execute(query)
            modules = result.scalars().all()
            
            now = datetime.now(timezone.utc)
            offline_modules_count = 0
            
            for module in modules:
                # Vérifier si le module n'a pas envoyé de statut depuis OFFLINE_THRESHOLD
                if module.last_seen and (now - module.last_seen) > OFFLINE_THRESHOLD:
                    # Le module est considéré comme offline
                    await db_logger.debug(
                        f"Module {module.module_uid} inactif depuis {(now - module.last_seen).total_seconds() // 60} minutes, marqué comme offline 🔴",
                        source="module_status_checker",
                        module_uid=module.module_uid
                    )
                    
                    # Créer un objet status pour la mise à jour
                    status_data = ModuleStatusCreate(
                        module_uid=module.module_uid,
                        status="offline",
                        version=module.version,
                        uptime=module.uptime,
                        memory_usage=module.memory_usage,
                        cpu_usage=module.cpu_usage
                    )
                    
                    # Mettre à jour le statut et diffuser via WebSocket
                    await update_module_status(db, status_data, check_alerts=True)
                    offline_modules_count += 1
            
            if offline_modules_count > 0:
                await db_logger.debug(
                    f"{offline_modules_count} module(s) marqué(s) comme offline après timeout 🔴",
                    source="module_status_checker"
                )
            break  # Sortir de la boucle async generator après la première itération
    
    except Exception as e:
        await db_logger.debug(
            f"Erreur lors de la vérification du statut des modules: {str(e)} 🚨",
            source="module_status_checker"
        )

async def run_status_checker():
    """
    Fonction principale qui exécute la vérification périodique du statut des modules.
    """
    await db_logger.debug(
        "🕒 Démarrage du vérificateur de statut des modules",
        source="module_status_checker"
    )
    
    CHECK_INTERVAL = 60  # Vérifier toutes les 60 secondes
    
    while True:
        await check_modules_status()
        await asyncio.sleep(CHECK_INTERVAL)
