"""SalaryRecord model — append-only salary history for employees."""

import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.types import PortableUUID


class SalaryRecord(Base):
    """
    Represents a single salary entry for an employee.

    Each salary change creates a new record with an effective_date.
    The current salary is always the record with the latest effective_date.
    This design is append-only and audit-friendly.
    """

    __tablename__ = "salary_records"

    id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID(), primary_key=True, default=uuid.uuid4
    )
    employee_id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID(), ForeignKey("employees.id"), nullable=False, index=True
    )
    base_salary: Mapped[Decimal] = mapped_column(
        Numeric(precision=15, scale=2), nullable=False
    )
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    effective_date: Mapped[date] = mapped_column(Date, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=func.now()
    )

    # Relationships
    employee = relationship("Employee", back_populates="salary_records")

    def __repr__(self) -> str:
        return f"<SalaryRecord {self.currency} {self.base_salary} from {self.effective_date}>"
