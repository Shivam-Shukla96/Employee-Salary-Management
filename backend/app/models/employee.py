"""Employee model — core entity representing an ACME org employee."""

import enum
import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Enum, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.types import PortableUUID


class EmployeeStatus(str, enum.Enum):
    """Employee status — Active or Inactive (soft delete)."""

    ACTIVE = "active"
    INACTIVE = "inactive"


class Employee(Base):
    """
    Represents an employee in the organization.

    Business key: employee_id (EMP-XXXX format)
    Primary key: id (UUID, internal)
    """

    __tablename__ = "employees"

    id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID(), primary_key=True, default=uuid.uuid4
    )
    employee_id: Mapped[str] = mapped_column(
        String(20), unique=True, nullable=False, index=True
    )
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    department: Mapped[str] = mapped_column(String(100), nullable=False)
    job_title: Mapped[str] = mapped_column(String(100), nullable=False)
    country: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[EmployeeStatus] = mapped_column(
        Enum(EmployeeStatus), nullable=False, default=EmployeeStatus.ACTIVE
    )
    joining_date: Mapped[date] = mapped_column(Date, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=func.now(), onupdate=func.now()
    )

    # Relationships
    salary_records = relationship(
        "SalaryRecord", back_populates="employee", order_by="SalaryRecord.effective_date"
    )

    def __repr__(self) -> str:
        return f"<Employee {self.employee_id}: {self.full_name}>"
