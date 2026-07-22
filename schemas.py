from typing import Optional
import datetime
from pydantic import BaseModel, ConfigDict

class EmployeeBase(BaseModel):
    full_name: str
    department_id: int
    position_id: int

class EmployeeResponse(EmployeeBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class RequestCreate(BaseModel):
    author_id: int
    executor_id: Optional[int] = None
    description: str
    deadline: datetime.datetime

class RequestResponse(BaseModel):
    id: int
    created_at: datetime.datetime
    author_id: int
    executor_id: Optional[int]
    description: str
    deadline: datetime.datetime
    status: str
    model_config = ConfigDict(from_attributes=True)

class StatusCount(BaseModel):
    status: str
    count: int

class ExecutorPerformance(BaseModel):
    executor_id: Optional[int]
    executor_name: Optional[str]
    completed_count: int

class AnalyticalReportResponse(BaseModel):
    by_status: list[StatusCount]
    total_overdue: int
    by_executor: list[ExecutorPerformance]

class NamedEntity(BaseModel):
    id: int
    name: str
    model_config = ConfigDict(from_attributes=True)

class EmployeeDetailedResponse(BaseModel):
    id: int
    full_name: str
    department: NamedEntity
    position: NamedEntity
    
    model_config = ConfigDict(from_attributes=True)