"""
Pydantic schemas for Employee API requests and responses.
"""

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------


class EmployeeCreate(BaseModel):
    """Schema for creating a new employee (with initial salary)."""

    full_name: str = Field(..., min_length=1, max_length=255)
    email: str = Field(..., min_length=1, max_length=255)
    department: str = Field(..., min_length=1, max_length=100)
    job_title: str = Field(..., min_length=1, max_length=100)
    country: str = Field(..., min_length=1, max_length=100)
    joining_date: date

    # Initial salary — required when creating an employee
    base_salary: Decimal = Field(..., gt=0)
    currency: str = Field(..., min_length=3, max_length=3)


class EmployeeUpdate(BaseModel):
    """Schema for updating employee details (not salary — that's a separate endpoint)."""

    full_name: Optional[str] = Field(None, min_length=1, max_length=255)
    email: Optional[str] = Field(None, min_length=1, max_length=255)
    department: Optional[str] = Field(None, min_length=1, max_length=100)
    job_title: Optional[str] = Field(None, min_length=1, max_length=100)
    country: Optional[str] = Field(None, min_length=1, max_length=100)
    joining_date: Optional[date] = None


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------


class SalaryInfo(BaseModel):
    """Current salary information included in employee responses."""

    base_salary: Decimal
    currency: str
    effective_date: date
    salary_usd: Optional[Decimal] = None

    model_config = {"from_attributes": True}


class EmployeeResponse(BaseModel):
    """Schema for a single employee in API responses."""

    id: uuid.UUID
    employee_id: str
    full_name: str
    email: str
    department: str
    job_title: str
    country: str
    status: str
    joining_date: date
    created_at: datetime
    updated_at: datetime
    current_salary: Optional[SalaryInfo] = None

    model_config = {"from_attributes": True}


class EmployeeListResponse(BaseModel):
    """Paginated list of employees."""

    items: list[EmployeeResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
