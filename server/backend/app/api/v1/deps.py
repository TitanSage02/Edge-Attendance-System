from fastapi import Header, Depends, HTTPException, status, WebSocket, HTTPException
from sqlalchemy.future import select
from fastapi.security import OAuth2PasswordBearer

from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

import logging
import os

from pathlib import Path

from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.services.log_service import db_logger

from app.models.user import User

from app.models.api_key import ApiKey


# # Configure logging - using a path relative to the application root
# current_file = Path(__file__)
# project_root = current_file.parent.parent.parent  # Navigate up to the project root
# log_dir = project_root / "logs"
# os.makedirs(log_dir, exist_ok=True)
# log_file = log_dir / "app.log"

# logger = logging.getLogger("api")
# logger.setLevel(logging.DEBUG)

# file_handler = logging.FileHandler(log_file)
# file_handler.setLevel(logging.DEBUG)

# formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# file_handler.setFormatter(formatter)

# logger.addHandler(file_handler)


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

async def get_db():
    """
    Dependency for database session.
    
    Yields:
        AsyncSession: Database session
    """
    session = AsyncSessionLocal()
    try:
        yield session
    except Exception as e:
        # Effectuer un rollback en cas d'erreur
        try:
            await session.rollback()
            # logger.error(f"Database session error: {str(e)}")
        except Exception as rollback_error:
            # logger.error(f"Error during rollback: {str(rollback_error)}")
            pass
        # IMPORTANT: Re-lancer l'exception originale pour que FastAPI puisse la traiter
        raise
    finally:
        try:
            await session.close()
        except Exception as close_error:
            # logger.error(f"Error closing session: {str(close_error)}")
            pass

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Verify and return the current authenticated user.
    
    Args:
        token: JWT token from authorization header
        db: Database session
    
    Returns:
        User: The authenticated user
        
    Raises:
        HTTPException: If authentication fails
    """

    from app.services.user_service import crud_user

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token, 
            settings.JWT_ACCESS_SECRET, 
            algorithms=[settings.ALGORITHM]
        )
        
        user_id: int = int(payload.get("sub"))
        
        if not user_id:
            # logger.warning(f"Missing user ID in JWT token. Payload: {payload}")
            raise credentials_exception
    
    except JWTError as e:
        # logger.warning(f"JWT token decode error: {str(e)}")
        raise credentials_exception
    
    user = await crud_user.get_by_id(db, user_id=user_id)
    if not user:
        # logger.warning(f"User not found in database during authentication. User ID: {user_id}")
        raise credentials_exception
    
    if not user.is_active:
        # logger.warning(f"Inactive user login attempt. User ID: {user_id}, Email: {user.email}")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")
    
    # logger.debug(f"User authenticated successfully. User ID: {user_id}, Email: {user.email}, Role: {user.role}")
    
    return user

async def get_current_user_ws(websocket: WebSocket):
    """
    Authenticate a user through WebSocket connection.
    
    Args:
        websocket: The WebSocket connection
    
    Returns:
        User or None: The authenticated user or None if no valid token
    """
    from app.services.user_service import crud_user
    
    token = websocket.query_params.get("token")
    client_info = f"{websocket.client.host}:{websocket.client.port}" if websocket.client else "unknown"
    
    if not token:
        db_logger.debug(f"WebSocket connection attempt without token. Client: {client_info}")
        return None
        
    try:
        payload = jwt.decode(
            token, 
            settings.JWT_ACCESS_SECRET, 
            algorithms=[settings.ALGORITHM]
        )
        user_id = int(payload.get("sub"))
        
        async with AsyncSessionLocal() as db:
            user = await crud_user.get_by_id(db, user_id=user_id)
            if not user or not user.is_active:
                db_logger.warning(f"WebSocket authentication failed - user not found or inactive. User ID: {user_id}, Client: {client_info}")
                return None
                
            db_logger.debug(f"WebSocket user authenticated successfully. User ID: {user_id}, Email: {user.email}, Client: {client_info}")
            return user
    except Exception as e:
        db_logger.error(f"WebSocket authentication error: {str(e)}. Client: {client_info}")
        return None


async def get_api_key(
    db: AsyncSession = Depends(get_db),
    x_api_key: str = Header(None)
):
    """Verify API key and return the corresponding ApiKey object.
    
    Args:
        db: Database session
        x_api_key: API key from X-API-Key header
        
    Returns:
        ApiKey: The API key object if valid
        
    Raises:
        HTTPException: If API key is missing or invalid
    """
    import hashlib
    from datetime import datetime
    
    if not x_api_key:
        raise HTTPException(status_code=401, detail="API key required")
    
    # Hash the provided API key
    hashed_key = hashlib.sha256(x_api_key.encode()).hexdigest()
    
    query = select(ApiKey).filter(
        ApiKey.key == hashed_key,
        ApiKey.is_active == True
    )
    result = await db.execute(query)
    api_key = result.scalar_one_or_none()
    
    if not api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    # Update last_used_at timestamp
    api_key.last_used_at = datetime.utcnow()
    await db.commit()
    
    return api_key