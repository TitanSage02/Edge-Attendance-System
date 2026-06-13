from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, EmailStr, ConfigDict

class UserBase(BaseModel):
    firstName:  Optional[str]
    lastName:   Optional[str]
    email:       Optional[EmailStr]
    role:        Optional[str]   # "admin" | "pedagogical" | "technician"
    is_active:   bool = True

    # Passer en datetime pour lever le 422
    created_at:  Optional[datetime]
    last_login:  Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class UserCreate(BaseModel):
    firstName: str
    lastName: str
    email: EmailStr    
    role: str   # "admin" | "pedagogical" | "technician"
    password: Optional[str] = None
    is_active: bool = True

    model_config = ConfigDict(from_attributes=True)


class UserRead(UserBase):
    id: int

    # on garde from_attributes pour pouvoir faire from_orm()
    model_config = ConfigDict(from_attributes=True)


class UserUpdate(BaseModel):
    firstName: Optional[str] = None
    lastName:  Optional[str] = None    
    email:     Optional[EmailStr] = None
    role:      Optional[str] = None   # "admin" | "pedagogical" | "technician"

    model_config = ConfigDict(from_attributes=True)

class UserOperationResponse(BaseModel):
    message : str
    success : bool