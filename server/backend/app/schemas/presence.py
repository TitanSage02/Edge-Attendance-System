from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime, date
from typing import Optional, Dict, List

class PresenceBase(BaseModel):
    student_id: str
    status: bool = Field(default=True, description="True pour présent, False pour absent")
    module_uid: int = Field(default=0, description="ID du module (0 pour présence manuelle)")
    timestamp: Optional[datetime] = None

class PresenceCreate(PresenceBase):
    pass

class PresenceResponse(PresenceBase):
    id: int
    entry_time: Optional[datetime] = Field(
        default=None,
        description="Heure d'entrée pour cette session de présence"
    )
    exit_time: Optional[datetime] = Field(
        default=None,
        description="Heure de sortie pour cette session de présence"
    )
    student: Optional[dict] = Field(
        default=None,
        description="Informations de l'étudiant",
        example={
            "id": "12345",
            "firstName": "John",
            "lastName": "Doe",
            "classGroup": "L1"
        }
    )
    
    model_config = ConfigDict(from_attributes=True)

class PresenceSummary(BaseModel):
    date: date
    total_students: int
    present_count: int
    absent_count: int
    presence_percentage: float

    by_class: Dict[str, float] = Field(
        default_factory=dict,
        description="Pourcentage de présence par classe"
    )

class StudentPresenceStat(BaseModel):
    student_id: str
    total_days: int
    present_days: int
    absent_days: int
    presence_percentage: float
    
    by_module: Dict[str, float] = Field(
        default_factory=dict,
        description="Pourcentage de présence par module"
    )
    
    by_date: Dict[date, bool] = Field(
        default_factory=dict,
        description="Statut de présence par date"
    )
