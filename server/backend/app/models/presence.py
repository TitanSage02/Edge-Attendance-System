from sqlalchemy import ForeignKey, DateTime, Boolean, Column, Integer, String, text
from sqlalchemy.orm import relationship
from app.db.base import Base


class Presence(Base):
    __tablename__ = "presences"
    
    id = Column(Integer, primary_key=True)
    student_id = Column(String(20), ForeignKey("students.id", ondelete="CASCADE"))
    status = Column(Boolean, default=True)  # True pour présent, False pour absent
    module_uid = Column(Integer, ForeignKey("modules.uid", ondelete="CASCADE"))
    timestamp = Column(DateTime(timezone=True), server_default=text('NOW()'))
    
    # Relations
    student = relationship("Student", back_populates="presences")
    module = relationship("Module", back_populates="presences")
