from app.db.base import Base
from sqlalchemy import Boolean, ForeignKey, Column, Integer, String, DateTime, Enum, text
from sqlalchemy.orm import relationship
import enum

class ModuleStatus(enum.Enum):
    online = "online"
    idle = "idle"
    offline = "offline"
    warning = "warning"

class Module(Base):
    __tablename__ = "modules"
    
    # Identité du module dans le système
    uid = Column(Integer, primary_key=True, unique=True, index=True, nullable=False) 
    
    name = Column(String(100), unique=True, nullable=True)
    description = Column(String(500), nullable=True)    
    emplacement = Column(String(200), nullable=True)

    # Pour les logings
    created_at = Column(DateTime(timezone=True), server_default=text('NOW()'))
    created_by = Column(Integer, ForeignKey("users.id"))

    updated_at = Column(DateTime(timezone=True), server_default=text('NOW()'), onupdate=text('NOW()'))
    updated_by = Column(Integer, ForeignKey("users.id"))

    # Module système
    faceChecked = Column(Boolean, default=True)
    rfidChecked = Column(Boolean, default=True)
    status = Column(Enum(ModuleStatus), default=ModuleStatus.offline, nullable=False)
    
    # Relations
    presences = relationship("Presence", back_populates="module", cascade="all, delete-orphan")