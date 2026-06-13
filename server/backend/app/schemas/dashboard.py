from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class DashboardLogSchema(BaseModel):
    id: int
    timestamp: datetime
    level: str
    action: str
    details: Optional[str] = None
    userName: Optional[str] = None
    moduleName: Optional[str] = None

    class Config:
        from_attributes = True

class AttendanceByClassSchema(BaseModel):
    name: str  # Nom de la classe (ex: "L1", "L2")
    present: int
    absent: int

    class Config:
        from_attributes = True

class TodayAttendanceMetricsSchema(BaseModel):
    total: int # Total des étudiants (présents + absents) pour les classes listées pour la journée
    by_class: List[AttendanceByClassSchema] = Field(..., alias="byClass")


    class Config:
        from_attributes = True
        populate_by_name = True


class AlertMetricsSchema(BaseModel):
    total: int
    # critical: int

    class Config:
        from_attributes = True

class ModuleMetricsSchema(BaseModel):
    total: int
    online: int
    offline: int
    # warning: int
    standby: int
    # temperature: Optional[float] = None

    class Config:
        from_attributes = True

class DashboardMetricsSchema(BaseModel):
    today_attendance: TodayAttendanceMetricsSchema = Field(..., alias="todayAttendance")
    alerts: AlertMetricsSchema
    modules: ModuleMetricsSchema
    recent_logs: List[DashboardLogSchema] = Field(..., alias="recentLogs")

    class Config:
        from_attributes = True
        populate_by_name = True 