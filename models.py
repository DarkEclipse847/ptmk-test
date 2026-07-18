import datetime
from typing import Optional
from sqlalchemy import ForeignKey, String, Text, DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from fastapi import HTTPException, status
from database import Base

class DomainException(HTTPException):
    def __init__(self, detail: str):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)

class Department(Base):
    __tablename__ = "departments"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    employees: Mapped[list["Employee"]] = relationship(back_populates="department")

class Position(Base):
    __tablename__ = "positions"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    employees: Mapped[list["Employee"]] = relationship(back_populates="position")

class Employee(Base):
    __tablename__ = "employees"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    full_name: Mapped[str] = mapped_column(String(150), nullable=False)
    department_id: Mapped[int] = mapped_column(ForeignKey("departments.id"), nullable=False)
    position_id: Mapped[int] = mapped_column(ForeignKey("positions.id"), nullable=False)
    
    department: Mapped["Department"] = relationship(back_populates="employees")
    position: Mapped["Position"] = relationship(back_populates="employees")

class Request(Base):
    __tablename__ = "requests"
    
    _TRANSITIONS = {
        "Новая": ["В работе"],
        "В работе": ["Выполнена", "Новая"],
        "Выполнена": []
    }

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)
    deadline: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="Новая", index=True)
    
    author_id: Mapped[int] = mapped_column(ForeignKey("employees.id"), nullable=False, index=True)
    executor_id: Mapped[Optional[int]] = mapped_column(ForeignKey("employees.id"), nullable=True, index=True)
    
    author: Mapped["Employee"] = relationship(foreign_keys=[author_id])
    executor: Mapped[Optional["Employee"]] = relationship(foreign_keys=[executor_id])

    def change_status(self, new_status: str) -> None:
        if new_status == self.status:
            return
        allowed = self._TRANSITIONS.get(self.status, [])
        if new_status not in allowed:
            raise DomainException(
                f"Бизнес-правило нарушено: нельзя перевести заявку из '{self.status}' в '{new_status}'"
            )
        if new_status == "В работе" and not self.executor_id:
            raise DomainException("Невозможно перевести заявку 'В работе' без назначения исполнителя.")
        self.status = new_status

    def assign_executor(self, executor_id: Optional[int]) -> None:
        if self.status == "Выполнена":
            raise DomainException("Нельзя менять исполнителя у уже выполненной заявки.")
        self.executor_id = executor_id
        if not executor_id and self.status == "В работе":
            self.status = "Новая"

    def is_overdue(self) -> bool:
        if self.status == "Выполнена":
            return False
        return self.deadline < datetime.datetime.utcnow()
