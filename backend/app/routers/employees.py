"""
Employee API router — CRUD endpoints for employee management.

Thin layer: validates input, delegates to EmployeeService, formats output.
"""

import csv
import io
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.employee import (
    EmployeeCreate,
    EmployeeListResponse,
    EmployeeResponse,
    EmployeeUpdate,
    SalaryInfo,
)
from app.services.employee_service import EmployeeService

router = APIRouter(prefix="/api/employees", tags=["Employees"])


def _get_service(db: Session = Depends(get_db)) -> EmployeeService:
    return EmployeeService(db)


def _to_response(employee) -> EmployeeResponse:
    """Convert an Employee model to an EmployeeResponse schema."""
    current_salary = None
    if employee.salary_records:
        # Latest salary record by effective date
        latest = max(employee.salary_records, key=lambda r: r.effective_date)
        current_salary = SalaryInfo(
            base_salary=latest.base_salary,
            currency=latest.currency,
            effective_date=latest.effective_date,
        )

    return EmployeeResponse(
        id=employee.id,
        employee_id=employee.employee_id,
        full_name=employee.full_name,
        email=employee.email,
        department=employee.department,
        job_title=employee.job_title,
        country=employee.country,
        status=employee.status.value if hasattr(employee.status, "value") else employee.status,
        joining_date=employee.joining_date,
        created_at=employee.created_at,
        updated_at=employee.updated_at,
        current_salary=current_salary,
    )


@router.get("", response_model=EmployeeListResponse)
def list_employees(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    country: Optional[str] = Query(None),
    department: Optional[str] = Query(None),
    job_title: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    sort_by: Optional[str] = Query(None),
    sort_order: str = Query("asc"),
    service: EmployeeService = Depends(_get_service),
):
    """List employees with pagination, search, filtering, and sorting."""
    result = service.list_employees(
        page=page,
        page_size=page_size,
        search=search,
        country=country,
        department=department,
        job_title=job_title,
        status=status,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    return EmployeeListResponse(
        items=[_to_response(emp) for emp in result["items"]],
        total=result["total"],
        page=result["page"],
        page_size=result["page_size"],
        total_pages=result["total_pages"],
    )


@router.get("/export")
def export_employees_csv(
    search: Optional[str] = Query(None),
    country: Optional[str] = Query(None),
    department: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    service: EmployeeService = Depends(_get_service),
):
    """Export filtered employees as CSV."""
    result = service.list_employees(
        page=1,
        page_size=100_000,
        search=search,
        country=country,
        department=department,
        status=status,
    )

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Employee ID", "Full Name", "Email", "Department",
        "Job Title", "Country", "Status", "Joining Date",
        "Current Salary", "Currency",
    ])

    for emp in result["items"]:
        salary = ""
        currency = ""
        if emp.salary_records:
            latest = max(emp.salary_records, key=lambda r: r.effective_date)
            salary = str(latest.base_salary)
            currency = latest.currency

        writer.writerow([
            emp.employee_id,
            emp.full_name,
            emp.email,
            emp.department,
            emp.job_title,
            emp.country,
            emp.status.value if hasattr(emp.status, "value") else emp.status,
            str(emp.joining_date),
            salary,
            currency,
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=employees.csv"},
    )


@router.get("/{employee_id}", response_model=EmployeeResponse)
def get_employee(
    employee_id: uuid.UUID,
    service: EmployeeService = Depends(_get_service),
):
    """Get a single employee by ID."""
    employee = service.get_by_id(employee_id)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    return _to_response(employee)


@router.post("", response_model=EmployeeResponse, status_code=201)
def create_employee(
    data: EmployeeCreate,
    service: EmployeeService = Depends(_get_service),
    db: Session = Depends(get_db),
):
    """Create a new employee with an initial salary."""
    try:
        employee = service.create(data)
        db.commit()
        return _to_response(employee)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.put("/{employee_id}", response_model=EmployeeResponse)
def update_employee(
    employee_id: uuid.UUID,
    data: EmployeeUpdate,
    service: EmployeeService = Depends(_get_service),
    db: Session = Depends(get_db),
):
    """Update employee details (not salary)."""
    try:
        employee = service.update(employee_id, data)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    db.commit()
    return _to_response(employee)


@router.delete("/{employee_id}", response_model=EmployeeResponse)
def delete_employee(
    employee_id: uuid.UUID,
    service: EmployeeService = Depends(_get_service),
    db: Session = Depends(get_db),
):
    """Soft-delete an employee (set status to inactive)."""
    try:
        employee = service.soft_delete(employee_id)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    db.commit()
    return _to_response(employee)


@router.post("/{employee_id}/reactivate", response_model=EmployeeResponse)
def reactivate_employee(
    employee_id: uuid.UUID,
    service: EmployeeService = Depends(_get_service),
    db: Session = Depends(get_db),
):
    """Reactivate a previously deactivated employee."""
    try:
        employee = service.reactivate(employee_id)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    db.commit()
    return _to_response(employee)
