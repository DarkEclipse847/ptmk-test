from fastapi import FastAPI, Depends, Query
from sqlalchemy.orm import Session
from database import engine, Base, get_db
import models
import schemas
from services import RequestDomainService

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Система учета заявок сотрудников")

@app.post("/employees/", response_model=schemas.EmployeeResponse)
def create_employee(employee: schemas.EmployeeBase, db: Session = Depends(get_db)):
    db_employee = models.Employee(**employee.model_dump())
    db.add(db_employee)
    db.commit()
    db.refresh(db_employee)
    return db_employee

@app.post("/requests/", response_model=schemas.RequestResponse)
def create_request(request_data: schemas.RequestCreate, db: Session = Depends(get_db)):
    service = RequestDomainService(db)
    return service.create_request(request_data)

@app.patch("/requests/{request_id}/status", response_model=schemas.RequestResponse)
def update_request_status(request_id: int, new_status: str = Query(...), db: Session = Depends(get_db)):
    service = RequestDomainService(db)
    return service.update_status(request_id, new_status)

@app.patch("/requests/{request_id}/executor", response_model=schemas.RequestResponse)
def update_request_executor(request_id: int, executor_id: int | None = Query(None), db: Session = Depends(get_db)):
    service = RequestDomainService(db)
    return service.update_executor(request_id, executor_id)

@app.get("/requests/", response_model=list[schemas.RequestResponse])
def list_requests(
    status: str | None = None,
    executor_id: int | None = None,
    department_id: int | None = None,
    is_overdue: bool | None = None,
    limit: int = Query(50, ge=1, le=100), # По умолчанию 50 строк
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    service = RequestDomainService(db)
    return service.get_filtered_requests(
        status=status, 
        executor_id=executor_id, 
        department_id=department_id, 
        is_overdue=is_overdue,
        limit=limit,
        offset=offset
    )
