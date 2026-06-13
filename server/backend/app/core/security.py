import datetime as dt
from jose import jwt, JWTError

from app.core.config import settings

def _now():
    return dt.datetime.now(dt.timezone.utc)

def create_access_token(user_id: int):
    """
    Crée un nouveau token JWT d'accès.
    
    Args:
        user_id: L'ID de l'utilisateur à inclure dans le token
        
    Returns:
        str: Le token JWT encodé
    """
    try:
        expire = _now() + dt.timedelta(minutes=settings.ACCESS_TTL_MINUTES)
        to_encode = {"sub": str(user_id), "exp": expire}
        token = jwt.encode(to_encode, settings.JWT_ACCESS_SECRET, algorithm=settings.ALGORITHM)
        
        return token
    except Exception as e:
        raise

def decode_jwt(token: str):
    """
    Décode et valide un token JWT.
    
    Args:
        token: Le token JWT à décoder
        
    Returns:
        dict: Le contenu décodé du token
        
    Raises:
        JWTError: Si le token est invalide ou expiré
    """
    try:
        payload = jwt.decode(
            token, 
            settings.JWT_ACCESS_SECRET, 
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError as e:
        raise
