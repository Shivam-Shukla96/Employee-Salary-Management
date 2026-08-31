"""
Salary API router — endpoints for salary management.

Nested under /api/employees/{employee_id}/salary.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.salary import (
    CurrentSalaryResponse,
    SalaryHistoryResponse,
    SalaryRecordResponse,
    SalaryUpdate,
)
from app.services.salary_service import SalaryService

router = APIRouter(prefix="/api/employees/{employee_id}/salary", tags=["Salaries"])


def _get_service(db: Session = Depends(get_db)) -> SalaryService:
    return SalaryService(db)


@router.get("", response_model=CurrentSalaryResponse)
def get_current_salary(
    employee_id: uuid.UUID,
    service: SalaryService = Depends(_get_service),
):
    """Get the current salary for an employee (with USD conversion)."""
    result = service.get_current_salary(employee_id)
    if not result:
        raise HTTPException(status_code=404, detail="Employee or salary not found")
    return CurrentSalaryResponse(**result)


@router.get("/history", response_model=SalaryHistoryResponse)
def get_salary_history(
    employee_id: uuid.UUID,
    service: SalaryService = Depends(_get_service),
):
    """Get the full salary history for an employee."""
    records = service.get_salary_history(employee_id)
    return SalaryHistoryResponse(
        employee_id=str(employee_id),
        records=[SalaryRecordResponse(**r) for r in records],
    )


@router.post("", response_model=SalaryRecordResponse, status_code=201)
def update_salary(
    employee_id: uuid.UUID,
    data: SalaryUpdate,
    service: SalaryService = Depends(_get_service),
    db: Session = Depends(get_db),
):
    """Update an employee's salary (creates a new salary record)."""
    try:
        result = service.update_salary(employee_id, data)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    if not result:
        raise HTTPException(status_code=404, detail="Employee not found")
    db.commit()
    return SalaryRecordResponse(**result)
