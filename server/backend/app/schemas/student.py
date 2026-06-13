from pydantic import BaseModel, ConfigDict
from typing import List
from typing import Optional

class StudentBase(BaseModel):
    id: Optional[str]
    firstName: str
    lastName: str
    rfidUid: Optional[str] = None
    classGroup: str
    promotion: str
    
    faceEnrolled: Optional[bool] = False
    rfidEnrolled: Optional[bool] = False

class StudentCreate(StudentBase):
    pass
    
class StudentUpdate(BaseModel):
    firstName: Optional[str] = None
    lastName: Optional[str] = None
    rfidUid: Optional[str] = None
    classGroup: Optional[str] = None
    promotion: Optional[str] = None
    faceEnrolled: Optional[bool] = None
    rfidEnrolled: Optional[bool] = None

class StudentRead(StudentBase):
    model_config = ConfigDict(from_attributes=True)

    faceEnrolled: bool = False
    rfidEnrolled: Optional[bool] = False
    rfidScanned: bool = False

class StudentModuleRead(BaseModel):
    studentId: str
    rfidUid: str
    faceEmbedding : List[float]

class StudentOperationResponse(BaseModel):
    message: str
    success : bool

class StudentsPage(BaseModel):
    items: List[StudentRead]
    total_items: int
    page: int
    limit: int