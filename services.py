from typing import Optional
import datetime
from sqlalchemy.orm import Session
from sqlalchemy import select
from models import Request, Employee

class RequestDomainService:
    def __init__(self, db: Session):
        self.db = db

    def create_request(self, data) -> Request:
        db_request = Request(
            author_id=data.author_id,
            executor_id=data.executor_id,
            description=data.description,
            deadline=data.deadline,
            status="Новая"
        )
        if db_request.executor_id:
            db_request.assign_executor(db_request.executor_id)
            
        self.db.add(db_request)
        self.db.commit()
        self.db.refresh(db_request)
        return db_request

    def update_status(self, request_id: int, new_status: str) -> Request:
        request = self.db.get(Request, request_id)
        if not request:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Заявка не найдена")
        request.change_status(new_status)
        
        self.db.commit()
        self.db.refresh(request)
        return request

    def update_executor(self, request_id: int, executor_id: Optional[int]) -> Request:
        request = self.db.get(Request, request_id)
        if not request:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Заявка не найдена")
        request.assign_executor(executor_id)
        
        self.db.commit()
        self.db.refresh(request)
        return request

    def get_filtered_requests(
        self, 
        status: str | None = None, 
        executor_id: Optional[int] = None, 
        department_id: Optional[int] = None, 
        is_overdue: bool | None = None,
        limit: int = 100,
        offset: int = 0
    ):
        query = select(Request)
        
        if status:
            query = query.where(Request.status == status)
        if executor_id:
            query = query.where(Request.executor_id == executor_id)
        if department_id:
            query = query.join(Request.author).where(Employee.department_id == department_id)
        if is_overdue:
            query = query.where(Request.deadline < datetime.datetime.utcnow()).where(Request.status != "Выполнена")
        query = query.offset(offset).limit(limit)
        return self.db.scalars(query).all()
