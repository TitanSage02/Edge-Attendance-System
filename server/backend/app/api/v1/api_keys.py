"""API Keys management endpoints.

This module provides endpoints for managing API keys for presence units.
Includes creation, listing, revocation, and status management of API keys.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status # type: ignore
from sqlalchemy.ext.asyncio import AsyncSession # type: ignore
from sqlalchemy.future import select # type: ignore
from datetime import datetime
import secrets
import hashlib

from app.db.session import AsyncSessionLocal
from app.api.v1.deps import get_db, get_current_user
from app.models.api_key import ApiKey
from app.models.user import User
from app.schemas.api_key import ApiKeyCreate, ApiKeyRead, ApiKeyReadWithKey, ApiKeyResponse

router = APIRouter(tags=["api-keys"])


def generate_api_key() -> str:
    """Generate a secure API key."""
    return secrets.token_urlsafe(32)


def hash_api_key(api_key: str) -> str:
    """Hash an API key for secure storage."""
    return hashlib.sha256(api_key.encode()).hexdigest()


@router.post("/", response_model=ApiKeyResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    api_key_data: ApiKeyCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new API key for a module.
    
    Args:
        api_key_data: API key creation data
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        ApiKeyResponse: Created API key with plain key value (only shown once)
    """
    # Generate plain API key
    plain_key = generate_api_key()
    hashed_key = hash_api_key(plain_key)
    
    # Check if module_uid already has an active API key
    query = select(ApiKey).filter(
        ApiKey.module_uid == api_key_data.module_uid,
        ApiKey.is_active == True
    )
    result = await db.execute(query)
    existing_key = result.scalar_one_or_none()
    
    if existing_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Module {api_key_data.module_uid} already has an active API key"
        )
    
    # Create new API key
    db_api_key = ApiKey(
        key=hashed_key,
        plain_key=plain_key,  # Stocker aussi la clé en clair
        module_uid=api_key_data.module_uid,
        created_at=datetime.utcnow(),
        is_active=True
    )
    
    db.add(db_api_key)
    await db.commit()
    await db.refresh(db_api_key)
    
    # # Log the action
    # log_user_action(
    #     user_id=current_user.id,
    #     action="create_api_key",
    #     details=f"Created API key for module {api_key_data.module_uid}",
    #     ip_address=None  # Will be filled by middleware if available
    # )
    
    # Return the API key with plain key (only time it's shown)
    return ApiKeyResponse(
        id=db_api_key.id,
        key=plain_key,  # Plain key only shown at creation
        module_uid=db_api_key.module_uid,
        created_at=db_api_key.created_at,
        last_used_at=db_api_key.last_used_at,
        is_active=db_api_key.is_active,
        message="Clé API créée avec succès. Sauvegardez cette clé en sécurité - elle ne sera plus affichée."
    )


@router.get("/", response_model=List[ApiKeyReadWithKey])
async def list_api_keys(
    include_inactive: bool = False,
    module_uid: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all API keys.
    
    Args:
        include_inactive: Whether to include inactive keys
        module_uid: Filter by specific module UID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        List[ApiKeyReadWithKey]: List of API keys with plain key values
    """
    query = select(ApiKey)
    
    if not include_inactive:
        query = query.filter(ApiKey.is_active == True)
    
    if module_uid is not None:
        query = query.filter(ApiKey.module_uid == module_uid)
    
    query = query.order_by(ApiKey.created_at.desc())
    result = await db.execute(query)
    api_keys = result.scalars().all()
    
    return [
        ApiKeyReadWithKey(
            id=key.id,
            module_uid=key.module_uid,
            created_at=key.created_at,
            last_used_at=key.last_used_at,
            is_active=key.is_active,
            key=key.plain_key if key.plain_key else f"Clé #{key.id} (clé en clair non disponible)"  # Affichage de la clé en clair ou message
        )
        for key in api_keys
    ]


@router.get("/{api_key_id}", response_model=ApiKeyRead)
async def get_api_key(
    api_key_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific API key by ID.
    
    Args:
        api_key_id: ID of the API key
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        ApiKeyRead: API key details (without plain key value)
    """
    query = select(ApiKey).filter(ApiKey.id == api_key_id)
    result = await db.execute(query)
    api_key = result.scalar_one_or_none()
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    
    return ApiKeyRead(
        id=api_key.id,
        module_uid=api_key.module_uid,
        created_at=api_key.created_at,
        last_used_at=api_key.last_used_at,
        is_active=api_key.is_active,
        key_preview=f"{api_key.key[:8]}..." if api_key.key else "..."
    )


@router.patch("/{api_key_id}/revoke", response_model=ApiKeyRead)
async def revoke_api_key(
    api_key_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Revoke (deactivate) an API key.
    
    Args:
        api_key_id: ID of the API key to revoke
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        ApiKeyRead: Updated API key
    """
    query = select(ApiKey).filter(ApiKey.id == api_key_id)
    result = await db.execute(query)
    api_key = result.scalar_one_or_none()
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    
    if not api_key.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="API key is already revoked"
        )
    
    # Revoke the key
    api_key.is_active = False
    api_key.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(api_key)
    
    # # Log the action
    # log_user_action(
    #     user_id=current_user.id,
    #     action="revoke_api_key",
    #     details=f"Revoked API key for module {api_key.module_uid}",
    #     ip_address=None
    # )
    
    return ApiKeyRead(
        id=api_key.id,
        module_uid=api_key.module_uid,
        created_at=api_key.created_at,
        last_used_at=api_key.last_used_at,
        is_active=api_key.is_active,
        key_preview=f"{api_key.key[:8]}..." if api_key.key else "..."
    )


@router.patch("/{api_key_id}/activate", response_model=ApiKeyRead)
async def activate_api_key(
    api_key_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Activate (re-enable) an API key.
    
    Args:
        api_key_id: ID of the API key to activate
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        ApiKeyRead: Updated API key
    """
    query = select(ApiKey).filter(ApiKey.id == api_key_id)
    result = await db.execute(query)
    api_key = result.scalar_one_or_none()
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    
    if api_key.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="API key is already active"
        )
    
    # Check if module already has another active key
    existing_query = select(ApiKey).filter(
        ApiKey.module_uid == api_key.module_uid,
        ApiKey.is_active == True,
        ApiKey.id != api_key_id
    )
    existing_result = await db.execute(existing_query)
    existing_active_key = existing_result.scalar_one_or_none()
    
    if existing_active_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Module {api_key.module_uid} already has another active API key"
        )
    
    # Activate the key
    api_key.is_active = True
    api_key.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(api_key)
    
    # # Log the action
    # log_user_action(
    #     user_id=current_user.id,
    #     action="activate_api_key",
    #     details=f"Activated API key for module {api_key.module_uid}",
    #     ip_address=None
    # )
    
    return ApiKeyRead(
        id=api_key.id,
        module_uid=api_key.module_uid,
        created_at=api_key.created_at,
        last_used_at=api_key.last_used_at,
        is_active=api_key.is_active,
        key_preview=f"{api_key.key[:8]}..." if api_key.key else "..."
    )


@router.delete("/{api_key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_api_key(
    api_key_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Permanently delete an API key.
    
    Args:
        api_key_id: ID of the API key to delete
        db: Database session
        current_user: Current authenticated user
    """
    query = select(ApiKey).filter(ApiKey.id == api_key_id)
    result = await db.execute(query)
    api_key = result.scalar_one_or_none()
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    
    # # Log the action before deletion
    # log_user_action(
    #     user_id=current_user.id,
    #     action="delete_api_key",
    #     details=f"Deleted API key for module {api_key.module_uid}",
    #     ip_address=None
    # )
    
    await db.delete(api_key)
    await db.commit()
    
    return None
