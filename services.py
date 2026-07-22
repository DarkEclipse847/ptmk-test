from typing import Optional
import datetime
from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload
from sqlalchemy import select, func
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
    def generate_analytical_report(self) -> dict:
        status_query = (
            select(Request.status, func.count(Request.id).label("count"))
            .group_by(Request.status)
        )
        status_results = self.db.execute(status_query).all()
        by_status = [{"status": r.status, "count": r.count} for r in status_results]
        overdue_query = (
            select(func.count(Request.id))
            .where(Request.deadline < func.now())
            .where(Request.status != "Выполнена")
        )
        total_overdue = self.db.scalar(overdue_query) or 0
        executor_query = (
            select(
                Request.executor_id,
                Employee.full_name.label("executor_name"),
                func.count(Request.id).label("completed_count")
            )
            .join(Employee, Request.executor_id == Employee.id, isouter=True)
            .where(Request.status == "Выполнена")
            .group_by(Request.executor_id, Employee.full_name)
            .order_by(func.count(Request.id).desc())
            .limit(100)
        )
        executor_results = self.db.execute(executor_query).all()
        by_executor = [
            {
                "executor_id": r.executor_id,
                "executor_name": r.executor_name if r.executor_id else "Не назначен",
                "completed_count": r.completed_count
            }
            for r in executor_results
        ]
        return {
            "by_status": by_status,
            "total_overdue": total_overdue,
            "by_executor": by_executor
        }
    def get_employees(self, limit: int = 100, offset: int = 0):
        query = (
            select(Employee)
            .options(
                joinedload(Employee.department),
                joinedload(Employee.position)
            )
            .order_by(Employee.id)
            .offset(offset)
            .limit(limit)
        )
        return self.db.scalars(query).all()
