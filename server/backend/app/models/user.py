
"""
Définitions des modèles pour User et RefreshToken.
"""
import datetime as dt
from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    ForeignKey,
    text,
)
from sqlalchemy.orm import relationship
from app.db.base import Base


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    firstName = Column(String(50), nullable=True)
    lastName = Column(String(50), nullable=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    role = Column(String(20), nullable=True)  # "admin" | "pedagogical" | "technician"
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=text('NOW()'))
    updated_at = Column(DateTime(timezone=True), server_default=text('NOW()'), onupdate=text('NOW()'))
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    hashed_password = Column(String(255), nullable=False)
    token_version = Column(Integer, default=0)

    # Relation vers les refresh tokens
    refresh_tokens = relationship("RefreshToken", back_populates="user", lazy="selectin")

class RefreshToken(Base):
    __tablename__ = "refresh_tokens"
    
    id = Column(Integer, primary_key=True, index=True)
    token_hash = Column(String(128), unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    user = relationship("User", back_populates="refresh_tokens")
    created_at = Column(DateTime(timezone=True), server_default=text('NOW()'))
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    ip = Column(String(64), nullable=True)
    user_agent = Column(String(256), nullable=True)
    user_token_version = Column(Integer, nullable=False)
