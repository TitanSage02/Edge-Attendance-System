from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from datetime import datetime
from typing import List, Optional
import json

from app.models.module_status import ModuleStatus
from app.schemas.module_status import ModuleStatusCreate

from app.schemas.log import LogCreate
from app.core.websocket_manager import ws_manager
from app.services.log_service import db_logger

async def update_module_status(db: AsyncSession, status_data: ModuleStatusCreate, check_alerts: bool = True) -> ModuleStatus:
    """Met à jour le statut d'un module et le diffuse via WebSocket."""
    
    await db_logger.debug(
        f"Traitement d'une mise à jour de statut pour le Module #{status_data.module_uid}. Le système va maintenant enregistrer le nouvel état: {status_data.status}",
        source="module_status_service",
        module_uid=status_data.module_uid,
        details={"status": status_data.status}
    )
    
    # Vérifier si le statut existe déjà pour ce module
    query = select(ModuleStatus).filter(ModuleStatus.module_uid == status_data.module_uid)
    result = await db.execute(query)
    existing = result.scalar_one_or_none()
    
    if existing:
        await db_logger.debug(
            f"Module #{status_data.module_uid} déjà enregistré dans le système. Mise à jour des données existantes.",
            source="module_status_service",
            module_uid=status_data.module_uid
        )
    else:
        await db_logger.debug(
            f"Nouveau Module #{status_data.module_uid} détecté. Création d'un premier enregistrement de statut dans le système.",
            source="module_status_service"         
        )
    
    # Convertir les détails en JSON si nécessaire
    details_str = None
    if status_data.details:
        details_str = json.dumps(status_data.details)
    
    if existing:
        # Mise à jour du statut existant
        for key, value in status_data.model_dump(exclude_unset=True).items():
            if key == "details":
                setattr(existing, key, details_str)
            else:
                setattr(existing, key, value)
        
        existing.last_seen = datetime.now()
        db_status = existing
        await db_logger.debug(
            f"Statut du Module #{status_data.module_uid} mis à jour avec succès. Les nouvelles informations remplacent les données précédentes dans le système.",
            source="module_status_service",
            module_uid=status_data.module_uid
        )
    else:
        # Création d'un nouveau statut
        db_status = ModuleStatus(
            module_uid=status_data.module_uid,
            status=status_data.status,
            version=status_data.version,
            uptime=status_data.uptime,
            memory_usage=status_data.memory_usage,
            cpu_usage=status_data.cpu_usage,
            details=details_str,
            last_seen=datetime.now()
        )
        db.add(db_status)
        await db_logger.debug(
            f"Nouveau enregistrement de statut créé pour le Module #{status_data.module_uid}. Le module vient d'être ajouté à la base de données du système.",
            source="module_status_service",
            module_uid=status_data.module_uid
        )
    
    await db.commit()
    await db.refresh(db_status)

    await db_logger.debug(
        f"Statut du Module #{status_data.module_uid} enregistré avec succès dans la base de données (ID d'enregistrement: {db_status.id}). Les informations sont maintenant disponibles pour tous les utilisateurs.",
        source="module_status_service",
        module_uid=status_data.module_uid
    )
    
    # Convertir les détails JSON en dictionnaire pour la diffusion
    details = None
    if db_status.details:
        try:
            details = json.loads(db_status.details)
        except:
            details = {"raw": db_status.details}
    
    # Préparer les données WebSocket
    websocket_data = {
        "type": "module_status",
        "data": {
            "id": db_status.id,
            "module_uid": db_status.module_uid,
            "status": db_status.status.value,  # Convertir l'enum en string
            "version": db_status.version,
            "last_seen": db_status.last_seen.isoformat() if db_status.last_seen else None,  # Convertir datetime en string ISO
            "uptime": db_status.uptime,
            "memory_usage": db_status.memory_usage,
            "cpu_usage": db_status.cpu_usage,
            "details": details
        }
    }
    
    await db_logger.debug(
        f"Préparation des données de diffusion en temps réel pour le Module #{status_data.module_uid}. Les utilisateurs connectés vont recevoir la mise à jour immédiatement via WebSocket.",
        source="module_status_service",
        module_uid=status_data.module_uid
    )
    
    # Diffuser via WebSocket
    await ws_manager.broadcast(
        websocket_data,
        channel="modules"
    )
    
    await db_logger.debug(
        f"Mise à jour du Module #{status_data.module_uid} diffusée en temps réel. Tous les utilisateurs connectés au système ont maintenant été informés du changement d'état.",
        source="module_status_service",
        module_uid=status_data.module_uid
    )
    
    previous_status = getattr(existing, "status", None) if existing else None
    if check_alerts and status_data.status in ["error", "offline"] and previous_status != status_data.status:
        alert_data = LogCreate(
            level="critical" if status_data.status == "error" else "warning",
            message=f"Le module {status_data.module_uid} est passé en état {status_data.status}",
            source="module",
            module_uid=status_data.module_uid,
            details=status_data.details
        )
        
        # Enregistrement de l'alerte dans la base de données
        db_logger.debug(
            f"📡 Alerte module: le module {status_data.module_uid} est passé en état {status_data.status} 🔔",
            module_uid=status_data.module_uid,
            status=status_data.status,
            details=status_data.details
        )
        # Envoi de l'alerte via WebSocket
        await ws_manager.broadcast(
            {
                "type": "alert",
                "data": {
                    "level": alert_data.level,
                    "message": alert_data.message,
                    "source": alert_data.source,
                    "module_uid": alert_data.module_uid,
                    "details": alert_data.details,
                    "timestamp": datetime.now().isoformat()
                }
            },
            channel="alerts"
        )
    
    return db_status

async def get_module_statuses(db: AsyncSession, skip: Optional[int] = 0, limit: Optional[int] = 100) -> List[ModuleStatus]:
    """Récupère les statuts de tous les modules."""
    query = select(ModuleStatus).order_by(ModuleStatus.module_uid)
    if skip is not None:
        query = query.offset(skip)
    if limit is not None:
        query = query.limit(limit)
    result = await db.execute(query)
    return result.scalars().all()

async def get_module_status(db: AsyncSession, module_uid: int) -> Optional[ModuleStatus]:
    """Récupère le statut d'un module spécifique."""
    query = select(ModuleStatus).filter(ModuleStatus.module_uid == module_uid)
    result = await db.execute(query)
    return result.scalar_one_or_none()
