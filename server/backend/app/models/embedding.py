from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, text
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship
import json

from app.db.base import Base
from app.utils.encryption import encryption_service

class Embedding(Base):
    __tablename__ = "embeddings"
    
    id = Column(Integer, primary_key=True)
    student_id = Column(String(20), ForeignKey("students.id"), nullable=False)

    _vector = Column("vector", Text, nullable=True)
    student = relationship("Student", back_populates="_embeddings")
    created_at = Column(DateTime(timezone=True), server_default=text('NOW()'))
    updated_at = Column(DateTime(timezone=True), server_default=text('NOW()'), onupdate=text('NOW()'))
    
    @hybrid_property
    def vector(self):
        if not self._vector:
            return None
        
        # Ensure we have a string value, not an InstrumentedAttribute
        vector_value = self._vector
        if hasattr(vector_value, '__name__') and vector_value.__name__ == 'InstrumentedAttribute':
            # This means the column hasn't been loaded yet, return None for now
            return None
        
        if not isinstance(vector_value, str):
            return None
            
        try:
            decrypted = encryption_service.decrypt(vector_value)
            return json.loads(decrypted)
        except (json.JSONDecodeError, Exception):
            return None
    
    @vector.setter
    def vector(self, value):
        if not value:
            self._vector = None
        else:
            if isinstance(value, list):
                value = json.dumps(value)
            self._vector = encryption_service.encrypt(value)