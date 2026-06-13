from datetime import datetime
from pydantic import BaseModel, ConfigDict
from typing import Optional, Dict, Any

class ModuleStatusBase(BaseModel):
    module_uid: int
    status: str
    version: Optional[str] = None
    uptime: Optional[float] = None
    memory_usage: Optional[float] = None
    cpu_usage: Optional[float] = None
    details: Optional[Dict[str, Any]] = None

class ModuleStatusCreate(ModuleStatusBase):
    pass

class ModuleStatusUpdate(BaseModel):
    status: Optional[str] = None
    version: Optional[str] = None
    uptime: Optional[float] = None
    memory_usage: Optional[float] = None
    cpu_usage: Optional[float] = None
    details: Optional[Dict[str, Any]] = None

class ModuleStatusRead(ModuleStatusBase):
    id: int
    last_seen: datetime
    
    model_config = ConfigDict(from_attributes=True)
