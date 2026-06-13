# app/api/v1/users.py
"""User management endpoints for admin operations.

This module provides CRUD operations for user management,
restricted to admin users only.
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.models.user import User
from app.schemas import user as user_schema
from app.services.user_service import crud_user
from app.services.log_service import db_logger
from app.services.email_service import send_account_deletion_notification
from app.api.v1.deps import get_db, get_current_user
from app.utils.sanitization import sanitize_string

router = APIRouter(tags=["users"])


async def require_admin(current_user: User = Depends(get_current_user)):
    """Vérifie que l'utilisateur actuel est un admin."""
    if current_user.role != "admin":
        await db_logger.error(
            f"🚫 Tentative d'accès administrateur non autorisée par {current_user.email} 🔒", 
            "users.require_admin",
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Accès non autorisé"
        )
    return current_user


@router.get("/", response_model=List[user_schema.UserRead])
async def get_users(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Récupérer la liste de tous les utilisateurs."""
    try:
        result = await db.execute(select(User))
        users = result.scalars().all()
        
        await db_logger.debug(
            f"📋 Liste des utilisateurs récupérée par {current_user.email} ✅", 
            "users.get_users",
            user_id=current_user.id,
            details={"users_count": len(users)}
        )
        
        return users
    except Exception as e:        
        await db_logger.error(
            f"❌ Erreur lors de la récupération des utilisateurs: {str(e)}.", 
            "users.get_users",
            user_id=current_user.id
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la récupération des utilisateurs"
        )


@router.get("/{user_id}", response_model=user_schema.UserRead)
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Récupérer un utilisateur par son ID."""
    user = await crud_user.get_by_id(db, user_id=user_id)
    
    if not user:
        await db_logger.warning(
            f"🔍 Tentative d'accès à un utilisateur inexistant ID: {user_id} ⚠️", 
            "users.get_user",
            user_id=current_user.id
        )

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilisateur non trouvé"
        )
    
    await db_logger.info(
        f"👤 Utilisateur {user.email} récupéré par {current_user.email} ✅", 
        "users.get_user",
        user_id=current_user.id
    )
    
    return user


@router.patch("/{user_id}", response_model=user_schema.UserRead)
async def update_user(
    user_id: int,
    user_update: user_schema.UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Mettre à jour un utilisateur."""
   
    # Vérifier que l'utilisateur existe
    user = await crud_user.get_by_id(db, user_id=user_id)
    if not user:
        await db_logger.warning(
            f"🔍 Tentative de mise à jour d'un utilisateur inexistant ID: {user_id} ⚠️", 
            "users.update_user",
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilisateur non trouvé"
        )
    
    # Préparer les données à mettre à jour
    update_data = user_update.model_dump(exclude_unset=True)
    
    if "firstName" in update_data:
        update_data["firstName"] = sanitize_string(update_data["firstName"])
    
    if "lastName" in update_data:
        update_data["lastName"] = sanitize_string(update_data["lastName"])
    
    
    try:
        updated_user = await crud_user.update(db, user_id=user_id, **update_data)
        await db_logger.debug(
            f"✏️ Utilisateur {user.email} mis à jour par {current_user.email} ✅", 
            "users.update_user",
            user_id=current_user.id,
            details={"target_user_id": user_id, "updated_fields": list(update_data.keys())}
        )
        
        return updated_user
    
    except Exception as e:
        await db_logger.error(
            f"❌ Une erreur lors de la mise à jour des informations de l'utilisateur: {str(e)}.", 
            "users.update_user",
            user_id=current_user.id
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la mise à jour de l'utilisateur"
        )


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Supprimer un utilisateur."""
    # Vérifier que l'utilisateur existe
    user = await crud_user.get_by_id(db, user_id=user_id)

    if not user:
        await db_logger.warning(
            f"🔍 Tentative de suppression d'un utilisateur inexistant ID: {user_id} ⚠️", 
            "users.delete_user",
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilisateur non trouvé"
        )
    
    # Empêcher la suppression de son propre compte
    if user_id == current_user.id:
        await db_logger.warning(
            f"⚠️ Tentative de suppression de son propre compte par {current_user.email} 🚫", 
            "users.delete_user",
            user_id=current_user.id
        )

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Vous ne pouvez pas supprimer votre propre compte"
        )
    
    # Stocker les informations de l'utilisateur avant suppression pour l'email
    user_email = user.email
    user_name = user.lastName + " " + user.firstName if hasattr(user, 'lastName') and user.lastName else user.email
    admin_email = current_user.firstName + " " + current_user.lastName + "[" + current_user.email + "]"
    
    try:
        await crud_user.delete(db, user=user)
        
        # Envoi de l'email de notification en arrière-plan
        background_tasks.add_task(
            send_account_deletion_notification,
            to=user_email,
            username=user_name,
            deleted_by=admin_email
        )

        await db_logger.info(
            f"🗑️ L'administrateur {current_user.firstName} {current_user.lastName} [{current_user.email}] a supprimé le compte de {user_name} {user_email}.", 
            "users.delete_user",
            user_id=current_user.id
        )
        
    except Exception as e:        
        await db_logger.error(
            f"❌ Erreur lors de la suppression de l'utilisateur: {str(e)}", 
            "users.delete_user",
            user_id=current_user.id
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la suppression de l'utilisateur"
        )
