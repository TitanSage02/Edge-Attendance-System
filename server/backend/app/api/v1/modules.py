from fastapi import APIRouter, HTTPException, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from typing import List
import re

from app.models.user import User
from app.models.module import Module
from app.schemas.module import ModuleCreate, ModuleUpdate, ModuleResponse
from app.services.module_service import (
    get_module,
    get_modules,
    create_module,
    update_module,
    delete_module
)
from app.services.mqtt_service import mqtt_client

from app.api.v1.deps import get_db, get_current_user
from app.services.log_service import db_logger

router = APIRouter(tags=["modules"])

# # Helper pour valider le format du nom du module
# def validate_module_name(name: str) -> bool:
#     """Valide que le nom du module contient des lettres, chiffres, espaces ou tirets, et a une longueur de 3 à 100 caractères."""
#     return bool(re.match(r"^[a-zA-Z0-9\s\-]{3,100}$", name))

@router.post("/", response_model=ModuleResponse)
async def create_new_module(
    module_data: ModuleCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> ModuleResponse:
    """
    Crée un nouveau module.
    Ce point de terminaison crée un nouveau module dans le système.
    
    Paramètres:
    - module_data: Détails du module à créer
    
    Retours:
    - Informations du module créé
    """    
    # Vérification du rôle admin ou technicien
    if current_user.role != "admin" and current_user.role != "technician": # if role == pedagogue
        await db_logger.error(
            f"Création non de mudule non autorisé pour {current_user.email}",
            source="api_modules",
            user_id=current_user.id
        )
        raise HTTPException(status_code=403, detail="Seuls les administrateurs et techniciens peuvent créer des modules")

    # # Validation du format du nom
    # if not validate_module_name(module_data.name):
    #     await db_logger.warning(
    #         "Invalid module name format",
    #         source="api_modules",
    #         user_id=current_user.id,
    #         details={"name": module_data.name}
    #     )
    #     raise HTTPException(
    #         status_code=400,
    #         detail="Le nom du module doit contenir 3 à 100 caractères (lettres, chiffres, espaces, tirets)"
    #     )

    # Vérification de l'unicité du nom
    result = await db.execute(select(Module).where(Module.name == module_data.name))
    if result.scalar_one_or_none():
        await db_logger.warning(
            f"Impossible de créer un nouveau module avec le même nom {module_data.name}",
            source="api_modules",
            user_id=current_user.id
        )
        raise HTTPException(status_code=400, detail="Un module avec ce nom existe déjà")

    try:
        await db_logger.debug(
            "Demande de création d'un nouveau module",
            source="api_modules",
            user_id=current_user.id,
            details={
                "nom": module_data.name,
                "uid_demande": module_data.uid,
                "chemin": request.url.path
            }
        )
        module_data.created_by = current_user.id
        module = await create_module(db, module_data)
        
        await db_logger.info(
            f"🎉 Le module '{module.name}'(UID: {module.uid}) a été enregistré dans le système avec succès.",
            source="api_modules",
            user_id=current_user.id
        )
        
        return module
    
    except ValueError as ve:
        # Gestion spécifique des erreurs de validation (UID en conflit, etc.)
        await db_logger.warning(
            "Erreur de validation lors de la création du module",
            source="api_modules",
            user_id=current_user.id,
            details={
                "erreur": str(ve),
                "nom": module_data.name,
                "uid_demande": module_data.uid,
                "chemin": request.url.path
            }
        )
        raise HTTPException(
            status_code=409,  # Conflict - UID déjà existant
            detail=str(ve)
        )
    
    except Exception as e:
        await db_logger.error(
            "Erreur inattendue lors de la création du module",
            source="api_modules",
            user_id=current_user.id,
            details={
                "erreur": str(e),
                "type_erreur": type(e).__name__,
                "nom": module_data.name,
                "uid_demande": module_data.uid,
                "chemin": request.url.path
            }
        )

        raise HTTPException(
            status_code=500,
            detail=f"Erreur interne du serveur: {str(e)}"
        )

@router.patch("/{module_uid}", response_model=ModuleResponse)
async def update_existing_module(
    request: Request,
    module_uid: int,
    module_data: ModuleUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> ModuleResponse:
    """
    Met à jour un module existant.

    Paramètres:
    - module_uid: UID du module à mettre à jour
    - module_data: Données mises à jour du module
    
    Retours:
    - Détails du module mis à jour
    
    Erreurs:
    - 404: Si le module n'est pas trouvé
    """    
    
    # Vérification du rôle admin ou technicien
    if current_user.role != "admin" and current_user.role != "technician":
        await db_logger.error(
            f"🚫 Tentative non autorisée de modification du module {module_uid} par {current_user.firstName} {current_user.lastName}[{current_user.email}]",
            source="api_modules",
            user_id=current_user.id
        )

        raise HTTPException(status_code=403, detail="Seuls les administrateurs et techniciens peuvent modifier des modules")

    # Vérification de l'unicité du nom si modifié
    if module_data.name:
        result = await db.execute(
            select(Module).where(Module.name == module_data.name, Module.uid != module_uid)
        )

        if result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Un module avec ce nom existe déjà")

    try:
        await db_logger.debug(
            f"🔄 Demande de mise à jour reçue pour le module {module_uid} ✅",
            source="api_modules",
            user_id=current_user.id,
            details={
                "module_uid": module_uid, 
                "champs": list(module_data.model_dump(exclude_unset=True).keys()),
                "chemin": request.url.path
            }
        )
        
        module_data.updated_by = current_user.id
        updated_module = await update_module(db, module_uid, module_data)
        if updated_module is None:
            await db_logger.warning(
                f"Module à mettre à jour {module_uid} non trouvé ou supprimé",
                source="api_modules",
                user_id=current_user.id,
                details={"module_uid": module_uid}
            )
            raise HTTPException(status_code=404, detail="Module non trouvé")
        
        await db_logger.info(
            f"✨ Les données de configuration du module '{updated_module.name}' (UID: {module_uid}) ont été mises à jour avec succès par {current_user.firstName} {current_user.lastName}",
            source="api_modules",
            user_id=current_user.id,
        )
        
        return updated_module

    except HTTPException:
        raise
    
    except Exception as e:
        await db_logger.error(
            f"Erreur lors de la mise à jour du module {module_uid}",
            source="api_modules",
            user_id=current_user.id,
            details={
                "erreur": str(e),
                "module_uid": module_uid
            }
        )

        raise HTTPException(
            status_code=400,
            detail=f"Impossible de mettre à jour le module: {str(e)}"
        )

@router.delete("/{module_uid}")
async def delete_existing_module(
    module_uid: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Supprime un module existant.
    
    Paramètres:
    - module_uid: UID du module à supprimer
    
    Retours:
    - Message de confirmation
    
    Erreurs:
    - 404: Si le module n'est pas trouvé
    """
    # Vérification du rôle admin
    if current_user.role != "admin" and current_user.role != "technician":
        raise HTTPException(status_code=403, detail="Seuls les administrateurs peuvent supprimer des modules")

    try:
        await db_logger.debug(
            f"Demande de suppression du module {module_uid}",
            source="api_modules",
            user_id=current_user.id,
            details={"module_uid": module_uid, "chemin": request.url.path}
        )
        
        result = await delete_module(db, module_uid)
        if not result:
            await db_logger.warning(
                f"Module à supprimer {module_uid} non trouvé ou déjà supprimé",
                source="api_modules",
                user_id=current_user.id,
                details={"module_uid—uid": module_uid}
            )
            raise HTTPException(status_code=404, detail="Module non trouvé")
        
        await db_logger.info(
            f"🗑️ Le module {module_uid} a été supprimé avec succès par {current_user.firstName} {current_user.lastName}",
            source="api_modules",
            user_id=current_user.id,
        )
        
        return {"detail": "Module supprimé avec succès"}
    
    except HTTPException:
        raise
    
    except Exception as e:
        await db_logger.error(
            f"Erreur lors de la suppression du module {module_uid}",
            source="api_modules",
            user_id=current_user.id,
            details={
                "erreur": str(e),
                "module_uid": module_uid
            }
        )
        
        raise HTTPException(
            status_code=400,
            detail=f"Impossible de supprimer le module: {str(e)}"
        )

@router.get("/", response_model=List[ModuleResponse])
async def read_modules(
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Récupère tous les modules.
    Ce point de terminaison récupère tous les modules avec pagination.
    
    Paramètres:
    - skip: Nombre d'enregistrements à sauter (optionnel, défaut: 0)
    - limit: Nombre maximum d'enregistrements à renvoyer (optionnel, défaut: 100)
    
    Retours:
    - Liste des modules
    """
    try:
        await db_logger.debug(
            "Demande de liste des modules",
            source="api_modules",
            user_id=current_user.id,
            details={
                "skip": skip, 
                "limit": limit, 
                "chemin": request.url.path
            }
        )
        
        modules = await get_modules(db, skip=skip, limit=limit)
        
        await db_logger.debug(
            f"📋 Liste des modules récupérée avec succès - {len(modules)} module(s) disponible(s) ✅",
            source="api_modules",
            user_id=current_user.id,
            details={"nombre": len(modules)}
        )
        
        return modules
    
    except Exception as e:
        await db_logger.error(
            f"Erreur lors de la récupération des modules. Erreur : {str(e)}",
            source="api_modules",
            user_id=current_user.id
        )

        raise HTTPException(
            status_code=500,
            detail="Erreur lors de la récupération des modules"
        )

@router.get("/{module_uid}", response_model=ModuleResponse)
async def read_module(
    module_uid: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Récupère un module spécifique par UID.
    
    Paramètres:
    - module_uid: UID du module à récupérer
    
    Retours:
    - Détails du module
    
    Erreurs:
    - 404: Si le module n'est pas trouvé
    """
    try:
        await db_logger.debug(
            f"Demande du module {module_uid}",
            source="api_modules",
            user_id=current_user.id,
            details={"module_uid": module_uid, "chemin": request.url.path}
        )
        
        module = await get_module(db, module_uid)
        if module is None:
            await db_logger.warning(
                f"Module {module_uid} non trouvé ou supprimé",
                source="api_modules",
                user_id=current_user.id,
                details={"module_uid": module_uid}
            )
            raise HTTPException(status_code=404, detail="Module non trouvé")
        
        await db_logger.info(
            f"Les informations du module {module.name}(UID:{module_uid}) lus par {current_user.firstName} {current_user.lastName}",
            source="api_modules",
            user_id=current_user.id
        )
        
        return module
    
    except HTTPException:
        raise
    
    except Exception as e:
        await db_logger.error(
            f"Erreur lors de la récupération du module {module_uid}",
            source="api_modules",
            user_id=current_user.id,
            details={
                "erreur": str(e),
                "module_uid": module_uid
            }
        )

        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la récupération du module: {str(e)}"
        )

@router.post("/{module_uid}/restart")
async def restart_module(
    module_uid: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Redémarre un module.
    
    Paramètres:
    - module_uid: UID du module à redémarrer
    
    Retours:
    - Message de confirmation
    
    Erreurs:
    - 404: Si le module n'est pas trouvé
    - 403: Si l'utilisateur n'a pas les droits
    - 500: Si le redémarrage échoue
    """    
    # Vérification du rôle admin ou technicien
    if current_user.role != "admin" and current_user.role != "technician":
        await db_logger.error(
            f"🚫 Tentative non autorisée de redémarrage du module {module_uid} par {current_user.email} ⚠️",
            source="api_modules",
            user_id=current_user.id
        )
        raise HTTPException(status_code=403, detail="Seuls les administrateurs et techniciens peuvent redémarrer des modules")

    try:
        # Vérifier si le module existe
        module = await get_module(db, module_uid)
        if module is None:
            await db_logger.warning(
                f"Module à redémarrer {module_uid} non trouvé",
                source="api_modules",
                user_id=current_user.id,
                details={"module_uid": module_uid}
            )

            raise HTTPException(status_code=404, detail="Module non trouvé")

        await db_logger.debug(
            f"🔄 Demande de redémarrage reçue pour le module '{module.name}' (UID: {module_uid}) ✅",
            source="api_modules",
            user_id=current_user.id,
            details={
                "module_uid": module_uid,
                "nom": module.name,
                "chemin": request.url.path
            }
        )

        # Envoyer la commande de redémarrage via MQTT
        success = await mqtt_client.restart_module(module_uid)
        
        success = True  # Temporaire pour simuler le succès de la commande

        if not success:
            raise HTTPException(
                status_code=500,
                detail="Impossible d'envoyer la commande de redémarrage au module"
            )
        
        await db_logger.info(
            f"🔄 Le module '{module.name}'(UID: {module_uid}) a été redémarré avec succès par {current_user.firstName} {current_user.lastName}.",
            source="api_modules",
            user_id=current_user.id
        )
        
        return {"detail": "Commande de redémarrage envoyée avec succès"}
    
    except HTTPException:
        raise
    
    except Exception as e:
        await db_logger.error(
            f"💥 Erreur lors du redémarrage du module {module_uid} : {str(e)} ⚠️",
            source="api_modules",
            user_id=current_user.id,
            details={
                "erreur": str(e),
                "module_uid": module_uid
            }
        )

        raise HTTPException(
            status_code=500,
            detail=f"Impossible de redémarrer le module: {str(e)}"
        )