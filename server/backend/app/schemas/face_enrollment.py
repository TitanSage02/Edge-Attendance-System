from pydantic import BaseModel, Field

class FaceEnrollmentUpload(BaseModel):
    """Schéma pour l'upload de photos d'enrôlement facial"""
    student_id: str = Field(..., description="ID de l'étudiant")

class FaceEnrollmentResponse(BaseModel):
    """Réponse après traitement de l'enrôlement facial"""
    student_id: str
    message: str

class FaceEnrollmentBatchResponse(BaseModel):
    """Réponse pour un batch de photos d'enrôlement"""
    student_id: str
    message: str
    
    class Config:
        from_attributes = True