"""
Pydantic schemas for Salary API requests and responses.
"""

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------


class SalaryUpdate(BaseModel):
    """Schema for updating (creating a new record of) an employee's salary."""

    base_salary: Decimal = Field(..., gt=0, description="New base salary, must be positive")
    currency: str = Field(..., min_length=3, max_length=3)
    effective_date: date


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------


class SalaryRecordResponse(BaseModel):
    """Schema for a single salary history record."""

    id: uuid.UUID
    base_salary: Decimal
    currency: str
    effective_date: date
    salary_usd: Optional[Decimal] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class CurrentSalaryResponse(BaseModel):
    """Schema for the current salary with USD conversion."""

    base_salary: Decimal
    currency: str
    effective_date: date
    salary_usd: Optional[Decimal] = None


class SalaryHistoryResponse(BaseModel):
    """List of all salary records for an employee."""

    employee_id: str
    records: list[SalaryRecordResponse]
