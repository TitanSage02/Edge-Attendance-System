from pydantic import BaseModel, EmailStr
from typing import Optional

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_at: str | None = None

class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    remember_me: Optional[bool] = False
    
class LoginResponse(BaseModel):
    user: dict
    token: str
    expires_at: str
    success: bool

class ResetPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordResponse(BaseModel):
    message: str
    success: bool

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str

class ChangePasswordResponse(BaseModel):
    success: bool
    message: str