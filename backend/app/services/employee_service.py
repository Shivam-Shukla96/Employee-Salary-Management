"""
EmployeeService — business logic for employee CRUD operations.

Encapsulates all database operations for employees, keeping the router
thin and the logic independently testable.
"""

import math
import uuid
from datetime import date
from decimal import Decimal
from typing import Optional

from sqlalchemy import asc, desc, func, or_
from sqlalchemy.orm import Session, selectinload

from app.models.employee import Employee, EmployeeStatus
from app.models.salary_record import SalaryRecord
from app.schemas.employee import EmployeeCreate, EmployeeUpdate


class EmployeeService:
    """Service layer for Employee CRUD operations."""

    def __init__(self, db: Session):
        self.db = db

    # ------------------------------------------------------------------
    # Create
    # ------------------------------------------------------------------

    def create(self, data: EmployeeCreate) -> Employee:
        """
        Create a new employee with an initial salary record.

        Generates a sequential employee_id (EMP-XXXXX).
        Raises ValueError if email is already taken.
        """
        # Check for duplicate email
        existing = (
            self.db.query(Employee).filter(Employee.email == data.email).first()
        )
        if existing:
            raise ValueError(f"An employee with this email already exists: {data.email}")

        # Generate next employee_id
        employee_id = self._next_employee_id()

        employee = Employee(
            employee_id=employee_id,
            full_name=data.full_name,
            email=data.email,
            department=data.department,
            job_title=data.job_title,
            country=data.country,
            status=EmployeeStatus.ACTIVE,
            joining_date=data.joining_date,
        )
        self.db.add(employee)
        self.db.flush()

        # Create initial salary record
        salary_record = SalaryRecord(
            employee_id=employee.id,
            base_salary=data.base_salary,
            currency=data.currency,
            effective_date=data.joining_date,
        )
        self.db.add(salary_record)
        self.db.flush()

        return employee

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def get_by_id(self, employee_uuid: uuid.UUID) -> Optional[Employee]:
        """Get a single employee by their internal UUID with salary records eager-loaded."""
        return (
            self.db.query(Employee)
            .options(selectinload(Employee.salary_records))
            .filter(Employee.id == employee_uuid)
            .first()
        )

    def list_employees(
        self,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        country: Optional[str] = None,
        department: Optional[str] = None,
        job_title: Optional[str] = None,
        status: Optional[str] = None,
        sort_by: Optional[str] = None,
        sort_order: str = "asc",
    ) -> dict:
        """
        List employees with pagination, search, and filtering.

        Uses selectinload to eager-load salary records in 1 batch query (preventing N+1).
        Returns a dict with: items, total, page, page_size, total_pages.
        """
        query = self.db.query(Employee).options(selectinload(Employee.salary_records))

        # Apply filters
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    Employee.full_name.ilike(search_term),
                    Employee.employee_id.ilike(search_term),
                    Employee.email.ilike(search_term),
                )
            )
        if country:
            query = query.filter(Employee.country == country)
        if department:
            query = query.filter(Employee.department == department)
        if job_title:
            query = query.filter(Employee.job_title == job_title)
        if status:
            query = query.filter(Employee.status == status)

        # Get total count before pagination
        total = query.count()

        # Apply sorting
        sortable_columns = {
            "employee_id": Employee.employee_id,
            "full_name": Employee.full_name,
            "department": Employee.department,
            "country": Employee.country,
            "job_title": Employee.job_title,
            "joining_date": Employee.joining_date,
            "status": Employee.status,
        }
        sort_column = sortable_columns.get(sort_by, Employee.employee_id)
        order_fn = desc if sort_order == "desc" else asc

        # Apply pagination
        offset = (page - 1) * page_size
        items = (
            query.order_by(order_fn(sort_column))
            .offset(offset)
            .limit(page_size)
            .all()
        )

        total_pages = math.ceil(total / page_size) if page_size > 0 else 0

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        }

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update(
        self, employee_uuid: uuid.UUID, data: EmployeeUpdate
    ) -> Optional[Employee]:
        """
        Update employee details (not salary — that's handled by SalaryService).

        Only updates fields that are explicitly provided (not None).
        Guards against:
        - Inactive employee modification
        - No-op updates (identical values)
        - Duplicate email collisions
        Returns None if employee not found.
        """
        employee = self.get_by_id(employee_uuid)
        if not employee:
            return None

        if employee.status == EmployeeStatus.INACTIVE:
            raise ValueError(
                f"Cannot update details for inactive employee {employee.employee_id}. Please reactivate first."
            )

        update_data = data.model_dump(exclude_unset=True)
        changes = {}
        for field, value in update_data.items():
            if value is not None and getattr(employee, field) != value:
                changes[field] = value

        if not changes:
            raise ValueError("No changes detected — employee details are identical to current values")

        if "email" in changes:
            existing = (
                self.db.query(Employee)
                .filter(Employee.email == changes["email"], Employee.id != employee_uuid)
                .first()
            )
            if existing:
                raise ValueError(f"An employee with email '{changes['email']}' already exists")

        for field, value in changes.items():
            setattr(employee, field, value)

        self.db.flush()
        return employee

    # ------------------------------------------------------------------
    # Soft delete
    # ------------------------------------------------------------------

    def soft_delete(self, employee_uuid: uuid.UUID) -> Optional[Employee]:
        """
        Soft-delete an employee by setting status to INACTIVE.

        The employee remains in the database for historical analytics.
        Guards against deactivating already inactive employees.
        Returns None if employee not found.
        """
        employee = self.get_by_id(employee_uuid)
        if not employee:
            return None

        if employee.status == EmployeeStatus.INACTIVE:
            raise ValueError(f"Employee {employee.employee_id} is already inactive")

        employee.status = EmployeeStatus.INACTIVE
        self.db.flush()
        return employee

    def reactivate(self, employee_uuid: uuid.UUID) -> Optional[Employee]:
        """
        Reactivate a previously deactivated employee.

        Guards against reactivating already active employees.
        Returns None if employee not found.
        """
        employee = self.get_by_id(employee_uuid)
        if not employee:
            return None

        if employee.status == EmployeeStatus.ACTIVE:
            raise ValueError(f"Employee {employee.employee_id} is already active")

        employee.status = EmployeeStatus.ACTIVE
        self.db.flush()
        return employee

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _next_employee_id(self) -> str:
        """Generate the next sequential employee ID (EMP-XXXXX)."""
        max_id = self.db.query(func.max(Employee.employee_id)).scalar()
        if max_id:
            current_num = int(max_id.split("-")[1])
            return f"EMP-{current_num + 1:05d}"
        return "EMP-00001"
