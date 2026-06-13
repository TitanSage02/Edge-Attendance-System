"""API Key schemas for request/response validation."""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ApiKeyBase(BaseModel):
    """Base API key schema."""
    module_uid: int = Field(..., description="Module UID this API key belongs to")


class ApiKeyCreate(ApiKeyBase):
    """Schema for creating a new API key."""
    pass


class ApiKeyRead(ApiKeyBase):
    """Schema for reading API key data (without the actual key)."""
    id: int
    created_at: datetime
    last_used_at: Optional[datetime] = None
    is_active: bool
    key_preview: str = Field(..., description="Preview of the hashed key (first 8 characters + ...)")
    
    class Config:
        from_attributes = True


class ApiKeyReadWithKey(ApiKeyBase):
    """Schema for reading API key data WITH the actual key (for display purposes)."""
    id: int
    created_at: datetime
    last_used_at: Optional[datetime] = None
    is_active: bool
    key: str = Field(..., description="Full API key for display")
    
    class Config:
        from_attributes = True


class ApiKeyResponse(ApiKeyBase):
    """Schema for API key creation response (includes plain key - only shown once)."""
    id: int
    key: str = Field(..., description="Plain API key - only shown at creation time")
    created_at: datetime
    last_used_at: Optional[datetime] = None
    is_active: bool
    message: str = Field(..., description="Message about the API key creation")
    
    class Config:
        from_attributes = True


class ApiKeyUpdate(BaseModel):
    """Schema for updating API key status."""
    is_active: Optional[bool] = None
