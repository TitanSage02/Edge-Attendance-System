from sqlalchemy import Column, String, Boolean, DateTime, text
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship
from app.db.base import Base
from app.models.embedding import Embedding
from app.utils.encryption import encryption_service


class Student(Base):
    __tablename__ = "students"
    
    id = Column(String(20), primary_key=True, index=True)
    firstName = Column(String(100), nullable=False)
    lastName = Column(String(100), nullable=False)
    
    # Données sensibles encryptées
    _rfidUid = Column("rfidUid", String(255), nullable=True)
    _embeddings = relationship("Embedding", back_populates="student", cascade="all, delete-orphan")
    presences = relationship("Presence", back_populates="student", cascade="all, delete-orphan")
    classGroup = Column(String(50), nullable=False)
    promotion = Column(String(50), nullable=False)

    faceEnrolled = Column(Boolean, default=False)
    rfidEnrolled = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=text('NOW()'))
    updated_at = Column(DateTime(timezone=True), onupdate=text('NOW()'))
    
    @hybrid_property
    def rfidUid(self):
        if not self._rfidUid:
            return None
        try:
            decrypted = encryption_service.decrypt(self._rfidUid)
            if decrypted is None:
                return None
            return decrypted.decode('utf-8')
        except Exception:
            return None

    @rfidUid.setter
    def rfidUid(self, value):
        if not value:
            self._rfidUid = None
        else:
            try:
                self._rfidUid = encryption_service.encrypt(value)
            except Exception:
                self._rfidUid = None
    
    @hybrid_property
    def embeddings(self):
        if not self._embeddings:
            return None
        return [embedding.vector for embedding in self._embeddings]
    
    @embeddings.setter
    def embeddings(self, value):
        if not value:
            self._embeddings = []
        else:
            embedding = Embedding(vector=value, student_id=self.id)
            self._embeddings = [embedding]