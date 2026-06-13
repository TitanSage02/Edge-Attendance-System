from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, Dict, Any

class LogBase(BaseModel):
    level: str
    message: str
    source: str
    module_uid: Optional[int] = None
    user_id: Optional[int] = None
    details: Optional[Dict[str, Any]] = None

class LogCreate(LogBase):
    pass

class LogRead(LogBase):
    id: int
    timestamp: datetime
    
    model_config = ConfigDict(from_attributes=True)
    