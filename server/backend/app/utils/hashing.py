import secrets
from passlib.context import CryptContext
import hashlib

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def hash_token(raw: str) -> str:
    # utilise SHA‑256 sur le refresh token
    return hashlib.sha256(raw.encode()).hexdigest()

def create_refresh_token_raw():
    """Create a random refresh token."""
    return secrets.token_hex(64)

def generate_password(length : int = 8):
    """Generate a random password"""
    # Génération d’un mot de passe temporaire robuste
    import secrets
    import string

    alphabet = string.ascii_letters + string.digits + "!@#$%^&*()"
    raw_password = ''.join(secrets.choice(alphabet) for _ in range(length))

    return raw_password