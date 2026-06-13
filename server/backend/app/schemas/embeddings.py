from pydantic import BaseModel, ConfigDict, field_validator
from typing import List, Optional
from datetime import datetime

class EmbeddingBase(BaseModel):
    student_id: str
    vector: List[float]

class EmbeddingCreate(EmbeddingBase):
    @field_validator("vector")
    def validate_vector(cls, v):
        if len(v) != 512:
            raise ValueError("Le vecteur doit contenir exactement 512 valeurs")
        if not all(isinstance(x, (int, float)) for x in v):
            raise ValueError("Tous les éléments du vecteur doivent être des nombres")
        return v

class EmbeddingRead(EmbeddingBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)

class EmbeddingOperationResponse(BaseModel):
    message : str
    success : bool