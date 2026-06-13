from sqlalchemy import Column, Integer, String, DateTime, Boolean, text
from datetime import datetime
from app.db.base import Base

class ApiKey(Base):
    __tablename__ = "api_keys"
    
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(255), unique=True, index=True, nullable=False)  # Hash de la clé
    plain_key = Column(String(255), nullable=True)  # Clé en clair pour affichage
    
    module_uid = Column(Integer, nullable=True)  # ID du module ou None pour l'app
    created_at = Column(DateTime(timezone=True), server_default=text('NOW()'))
    
    updated_at = Column(DateTime(timezone=True), server_default=text('NOW()'), onupdate=text('NOW()'))
    
    last_used_at = Column(DateTime(timezone=True), nullable=True)  # Date de la dernière utilisation de la clé
    is_active = Column(Boolean, default=True)  # Boolean au lieu d'Integer