from app.db.base import Base
from sqlalchemy import ForeignKey, Column, Integer, String, DateTime, Text, Float, Enum, text
from app.models.module import ModuleStatus as ModuleStatusEnum


class ModuleStatus(Base):
    __tablename__ = "module_status"
    id = Column(Integer, primary_key=True)
    module_uid = Column(Integer, ForeignKey("modules.uid", ondelete="CASCADE"))
    status = Column(Enum(ModuleStatusEnum), nullable=False)  # Utilise l'Enum du modèle Module
    version = Column(String(50), nullable=True)
    last_seen = Column(DateTime(timezone=True), server_default=text('NOW()'))
    uptime = Column(Float, nullable=True)                # en secondes
    memory_usage = Column(Float, nullable=True)          # en MB
    cpu_usage = Column(Float, nullable=True)             # en pourcentage (maxi 100)
    details = Column(Text, nullable=True)                # Détails supplémentaires au format JSON