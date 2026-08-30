"""
Pydantic schemas for Analytics API responses.
"""

from decimal import Decimal
from typing import Optional

from pydantic import BaseModel


class DepartmentSalaryStat(BaseModel):
    """Salary statistics for a single department."""

    department: str
    employee_count: int
    avg_salary_usd: Decimal
    min_salary_usd: Decimal
    max_salary_usd: Decimal
    total_payroll_usd: Decimal


class CountrySalaryStat(BaseModel):
    """Salary statistics for a single country."""

    country: str
    currency: str
    employee_count: int
    avg_salary_local: Decimal
    avg_salary_usd: Decimal
    total_payroll_usd: Decimal


class SalarySummary(BaseModel):
    """Global salary summary across the entire organization."""

    total_employees: int
    avg_salary_usd: Decimal
    median_salary_usd: Optional[Decimal] = None
    min_salary_usd: Decimal
    max_salary_usd: Decimal
    total_payroll_usd: Decimal


class AnalyticsResponse(BaseModel):
    """Full analytics response combining all aggregations."""

    summary: SalarySummary
    by_department: list[DepartmentSalaryStat]
    by_country: list[CountrySalaryStat]
