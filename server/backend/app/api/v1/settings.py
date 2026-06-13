"""
Endpoints pour la gestion des paramètres de l'application.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List

from app.api.v1.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.settings import AllSettings, SettingsUpdate, SettingsResponse
from app.services.settings_service import settings_service
from app.services.log_service import db_logger

router = APIRouter(tags=["settings"])


async def require_admin_or_manager(current_user: User = Depends(get_current_user)):
    """Vérifie que l'utilisateur est admin ou manager."""
    if current_user.role not in ["admin", "pedagogical"]:
        raise HTTPException(
            status_code=403,
            detail="Accès autorisé uniquement aux administrateurs et gestionnaires pédagogiques"
        )
    return current_user


@router.get("/", response_model=Dict[str, Any])
async def get_settings(
    current_user: User = Depends(require_admin_or_manager)
    # db: AsyncSession = Depends(get_db)
):
    """
    Récupère tous les paramètres de l'application.
    
    Accessible uniquement aux administrateurs et gestionnaires pédagogiques.
    """
    try:
        await db_logger.debug(
            f"⚙️ Récupération des paramètres par {current_user.email} ✅",
            source="settings_api"
        )
        
        settings_data = await settings_service.get_settings()
        
        return settings_data
    except Exception as e:
        await db_logger.error(
            f"❌ Erreur lors de la récupération des paramètres: {str(e)}",
            source="settings_api"
        )

        raise HTTPException(
            status_code=500,
            detail="Erreur lors de la récupération des paramètres"
        )


@router.put("/", response_model=Dict[str, Any])
async def update_settings(
    settings: AllSettings,
    current_user: User = Depends(require_admin_or_manager)
):
    """
    Met à jour tous les paramètres de l'application.
    
    Accessible uniquement aux administrateurs et gestionnaires pédagogiques.
    """
    try:
        await db_logger.info(
            f"⚙️ {current_user.firstName} {current_user.lastName} a mis à jour les paramètres du système.",
            source="settings_api"
        )
        
        updated_settings = await settings_service.save_settings(
            settings, 
            current_user.email
        )
        
        return updated_settings
    except Exception as e:
        await db_logger.error(
            f"❌ Erreur lors de la mise à jour des paramètres: {str(e)}",
            source="settings_api"
        )

        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la mise à jour des paramètres: {str(e)}"
        )


@router.patch("/", response_model=Dict[str, Any])
async def update_partial_settings(
    updates: Dict[str, Any],
    current_user: User = Depends(require_admin_or_manager),
    db: AsyncSession = Depends(get_db)
):
    """
    Met à jour partiellement les paramètres de l'application.
    
    Permet de modifier seulement certains paramètres sans affecter les autres.
    """
    try:
        await db_logger.info(
            f"Mise à jour partielle des paramètres par {current_user.email}: {list(updates.keys())} ✅",
            source="settings_api"
        )
        
        updated_settings = await settings_service.update_partial_settings(
            updates, 
            current_user.email
        )
        
        return updated_settings
    except Exception as e:
        # await db_logger.error(
        #     f"❌ Erreur lors de la mise à jour partielle: {str(e)} 🚨",
        #     source="settings_api"
        # )
        
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la mise à jour: {str(e)}"
        )


@router.post("/reset", response_model=Dict[str, Any])
async def reset_settings_to_defaults(
    current_user: User = Depends(require_admin_or_manager),
    db: AsyncSession = Depends(get_db)
):
    """
    Remet tous les paramètres aux valeurs par défaut.
    
    Action critique - accessible uniquement aux administrateurs.
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Seuls les administrateurs peuvent remettre les paramètres à zéro"
        )
    
    try:
        # await db_logger.warning(
        #     f"🔄 Remise à zéro des paramètres par {current_user.email} ⚠️",
        #     source="settings_api"
        # )
        
        reset_settings = await settings_service.reset_to_defaults(current_user.email)
        
        return reset_settings
    except Exception as e:
        await db_logger.error(
            f"❌ Erreur lors de la remise à zéro: {str(e)} 🚨",
            source="settings_api"
        )
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la remise à zéro: {str(e)}"
        )


@router.get("/system-info", response_model=Dict[str, Any])
async def get_system_info(
    current_user: User = Depends(require_admin_or_manager),
    db: AsyncSession = Depends(get_db)
):
    """
    Récupère les informations système et l'état de l'application.
    """
    try:
        system_info = await settings_service.get_system_info()
        return system_info
    except Exception as e:
        await db_logger.error(
            f"❌ Erreur lors de la récupération des infos système: {str(e)} 🚨",
            source="settings_api"
        )
        raise HTTPException(
            status_code=500,
            detail="Erreur lors de la récupération des informations système"
        )


@router.post("/backup", response_model=Dict[str, Any])
async def create_backup(
    current_user: User = Depends(require_admin_or_manager),
    db: AsyncSession = Depends(get_db)
):
    """
    Crée une sauvegarde système complète.
    """
    try:
        result = await settings_service.create_backup(created_by=current_user.email)
        
        await db_logger.info(
            f"💾 Sauvegarde système créée par {current_user.email}: {result['backup_name']} ✅",
            source="settings_api"
        )
        
        return result
    
    except Exception as e:
        await db_logger.error(
            f"❌ Erreur lors de la création de sauvegarde système: {str(e)} 🚨",
            source="settings_api"
        )
    
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la création de sauvegarde système: {str(e)}"
        )


@router.get("/backup", response_model=List[Dict[str, Any]])
async def list_backups(
    current_user: User = Depends(require_admin_or_manager),
    db: AsyncSession = Depends(get_db)
):
    """
    Liste toutes les sauvegardes système disponibles.
    """
    try:
        backups = await settings_service.list_backups()
        return backups
    except Exception as e:
        await db_logger.error(
            f"❌ Erreur lors de la liste des sauvegardes système: {str(e)} 🚨",
            source="settings_api"
        )
        raise HTTPException(
            status_code=500,
            detail="Erreur lors de la récupération des sauvegardes système"
        )


@router.post("/backup/{backup_name}/restore", response_model=Dict[str, Any])
async def restore_backup(
    backup_name: str,
    current_user: User = Depends(require_admin_or_manager),
    db: AsyncSession = Depends(get_db)
):
    """
    Restaure une sauvegarde système spécifiée.
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Seuls les administrateurs peuvent restaurer des sauvegardes système"
        )
    
    try:
        result = await settings_service.restore_backup(backup_name, current_user.email)
        await db_logger.warning(
            f"🔄 Sauvegarde système restaurée depuis {backup_name} par {current_user.email} ⚠️",
            source="settings_api"
        )
        return result
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )
    except Exception as e:
        await db_logger.error(
            f"❌ Erreur lors de la restauration système depuis {backup_name}: {str(e)} 🚨",
            source="settings_api"
        )
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la restauration système: {str(e)}"
        )
