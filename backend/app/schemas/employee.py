"""
Pydantic schemas for Employee API requests and responses.
"""

import re
import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from app.config import settings


# ---------------------------------------------------------------------------
# Reusable validation helpers
# ---------------------------------------------------------------------------


def _validate_full_name(v: Optional[str]) -> Optional[str]:
    if v is None:
        return v
    v = v.strip()
    if not v:
        raise ValueError("Full name cannot be empty")
    return v


def _validate_email(v: Optional[str]) -> Optional[str]:
    if v is None:
        return v
    v = v.strip()
    if not v:
        raise ValueError("Email cannot be empty")
    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", v):
        raise ValueError(f"Invalid email format: '{v}'")
    return v.lower()


def _validate_department(v: Optional[str]) -> Optional[str]:
    if v is None:
        return v
    v = v.strip()
    if not v:
        raise ValueError("Department cannot be empty")
    valid_map = {d.lower(): d for d in settings.departments_list}
    if v.lower() not in valid_map:
        raise ValueError(
            f"Invalid department '{v}'. Allowed departments: {', '.join(settings.departments_list)}"
        )
    return valid_map[v.lower()]


def _validate_job_title(v: Optional[str]) -> Optional[str]:
    if v is None:
        return v
    v = v.strip()
    if not v:
        raise ValueError("Job title cannot be empty")
    return v


def _validate_country(v: Optional[str]) -> Optional[str]:
    if v is None:
        return v
    v = v.strip()
    if not v:
        raise ValueError("Country cannot be empty")
    valid_map = {c.lower(): c for c in settings.countries_list}
    if v.lower() not in valid_map:
        raise ValueError(
            f"Invalid country '{v}'. Allowed countries: {', '.join(settings.countries_list)}"
        )
    return valid_map[v.lower()]


def _validate_currency(v: Optional[str]) -> Optional[str]:
    if v is None:
        return v
    v = v.strip().upper()
    valid_currencies = set(settings.exchange_rates_dict.keys())
    if v not in valid_currencies:
        raise ValueError(
            f"Invalid currency '{v}'. Allowed currencies: {', '.join(sorted(valid_currencies))}"
        )
    return v


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

    @field_validator("full_name")
    @classmethod
    def val_full_name(cls, v: str) -> str:
        return _validate_full_name(v)  # type: ignore

    @field_validator("email")
    @classmethod
    def val_email(cls, v: str) -> str:
        return _validate_email(v)  # type: ignore

    @field_validator("department")
    @classmethod
    def val_department(cls, v: str) -> str:
        return _validate_department(v)  # type: ignore

    @field_validator("job_title")
    @classmethod
    def val_job_title(cls, v: str) -> str:
        return _validate_job_title(v)  # type: ignore

    @field_validator("country")
    @classmethod
    def val_country(cls, v: str) -> str:
        return _validate_country(v)  # type: ignore

    @field_validator("currency")
    @classmethod
    def val_currency(cls, v: str) -> str:
        return _validate_currency(v)  # type: ignore


class EmployeeUpdate(BaseModel):
    """Schema for updating employee details (not salary — that's a separate endpoint)."""

    full_name: Optional[str] = Field(None, min_length=1, max_length=255)
    email: Optional[str] = Field(None, min_length=1, max_length=255)
    department: Optional[str] = Field(None, min_length=1, max_length=100)
    job_title: Optional[str] = Field(None, min_length=1, max_length=100)
    country: Optional[str] = Field(None, min_length=1, max_length=100)
    joining_date: Optional[date] = None

    @field_validator("full_name")
    @classmethod
    def val_full_name(cls, v: Optional[str]) -> Optional[str]:
        return _validate_full_name(v)

    @field_validator("email")
    @classmethod
    def val_email(cls, v: Optional[str]) -> Optional[str]:
        return _validate_email(v)

    @field_validator("department")
    @classmethod
    def val_department(cls, v: Optional[str]) -> Optional[str]:
        return _validate_department(v)

    @field_validator("job_title")
    @classmethod
    def val_job_title(cls, v: Optional[str]) -> Optional[str]:
        return _validate_job_title(v)

    @field_validator("country")
    @classmethod
    def val_country(cls, v: Optional[str]) -> Optional[str]:
        return _validate_country(v)


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
