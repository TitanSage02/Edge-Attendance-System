from pydantic import BaseModel, field_validator
from typing import Optional, Dict

class PresenceMessage(BaseModel):
    student_id: str
    module_uid: str
    status: str
    timestamp: str
    details: Optional[Dict] = None

    @field_validator("status")
    def validate_status(cls, v):
        if v.lower() not in ["present", "absent", "late"]:
            raise ValueError("Invalid status")
        return v.lower()

class ModuleStatusMessage(BaseModel):
    status: str
    version: Optional[str] = None
    uptime: Optional[float] = None
    memory_usage: Optional[float] = None
    cpu_usage: Optional[float] = None
    details: Optional[Dict] = None

