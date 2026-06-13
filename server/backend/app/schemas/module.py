from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from datetime import datetime
from app.models.module import ModuleStatus as ModuleStatusEnum

class ModuleBase(BaseModel):
    uid: int

    name: Optional[str] = None
    description: Optional[str] = None
    
    emplacement: Optional[str] = None

    created_by: Optional[int] = None
    updated_by: Optional[int] = None
    
    faceChecked: Optional[bool] = True
    rfidChecked: Optional[bool] = True
    status: ModuleStatusEnum = ModuleStatusEnum.offline

    model_config = ConfigDict(from_attributes=True)  # Utiliser la nouvelle syntaxe

class ModuleCreate(ModuleBase):
    pass

class ModuleUpdate(BaseModel):
    # Seulement les champs qui peuvent être mis à jour
    name: Optional[str] = None
    description: Optional[str] = None
    emplacement: Optional[str] = None
    faceChecked: Optional[bool] = None
    rfidChecked: Optional[bool] = None
    updated_by: Optional[int] = None
    status: Optional[ModuleStatusEnum] = None
    
    model_config = ConfigDict(from_attributes=True)

class ModuleResponse(BaseModel):
    uid: int
    name: Optional[str] = None
    description: Optional[str] = None
    emplacement: Optional[str] = None
    faceChecked: bool
    rfidChecked: bool
    created_by: Optional[int] = None
    status: ModuleStatusEnum = ModuleStatusEnum.offline
    
    model_config = ConfigDict(from_attributes=True)

class ModuleOperationResponse(BaseModel):
    message: str
    success: bool