from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, text
import json

from app.db.base import Base

class Log(Base):
    __tablename__ = "logs"
    
    id = Column(Integer, primary_key=True)
    level = Column(String(10))  # INFO, WARNING, ERROR, DEBUG
    message = Column(Text)
    source = Column(String(50))  # Le composant qui a généré le log
    
    module_uid = Column(Integer, ForeignKey("modules.uid", ondelete="SET NULL"), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=text('NOW()'))
    details = Column(Text, nullable=True)  # Détails supplémentaires au format JSON
    
    # channel optionnel pour les messages WebSocket
    channel = Column(String(50), nullable=True)  # Canal WebSocket associé

    @property
    def details_dict(self):
        """Convertit les détails JSON en dictionnaire Python"""
        if self.details:
            try:
                return json.loads(self.details)
            except json.JSONDecodeError:
                return {}
        return {}
    
    def set_details(self, details_dict):
        """Définit les détails à partir d'un dictionnaire"""
        if details_dict:
            self.details = json.dumps(details_dict)
        else:
            self.details = None