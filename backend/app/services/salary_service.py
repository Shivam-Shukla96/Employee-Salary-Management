"""
SalaryService — business logic for salary management.

Handles salary updates (append-only history), current salary retrieval,
salary history, and currency normalization to USD.
"""

import uuid
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.models.employee import Employee, EmployeeStatus
from app.models.exchange_rate import ExchangeRate
from app.models.salary_record import SalaryRecord
from app.schemas.salary import SalaryUpdate


class SalaryService:
    """Service layer for salary management operations."""

    def __init__(self, db: Session):
        self.db = db

    # ------------------------------------------------------------------
    # Get current salary
    # ------------------------------------------------------------------

    def get_current_salary(self, employee_uuid: uuid.UUID) -> Optional[dict]:
        """
        Get the current (latest) salary for an employee, with USD conversion.

        Returns None if the employee doesn't exist or has no salary records.
        """
        record = (
            self.db.query(SalaryRecord)
            .filter(SalaryRecord.employee_id == employee_uuid)
            .order_by(desc(SalaryRecord.effective_date))
            .first()
        )
        if not record:
            return None

        salary_usd = self._convert_to_usd(record.base_salary, record.currency)

        return {
            "base_salary": record.base_salary,
            "currency": record.currency,
            "effective_date": record.effective_date,
            "salary_usd": salary_usd,
        }

    # ------------------------------------------------------------------
    # Update salary
    # ------------------------------------------------------------------

    def update_salary(
        self, employee_uuid: uuid.UUID, data: SalaryUpdate
    ) -> Optional[dict]:
        """
        Update an employee's salary by creating a new salary record.

        This is append-only — the old record is preserved for history.
        Returns None if the employee doesn't exist.
        """
        employee = (
            self.db.query(Employee).filter(Employee.id == employee_uuid).first()
        )
        if not employee:
            return None

        if employee.status == EmployeeStatus.INACTIVE:
            raise ValueError(
                f"Cannot update salary for inactive employee {employee.employee_id}. Please reactivate the employee first."
            )

        # Guard: reject if salary data is identical to current salary
        current = (
            self.db.query(SalaryRecord)
            .filter(SalaryRecord.employee_id == employee_uuid)
            .order_by(desc(SalaryRecord.effective_date))
            .first()
        )
        if current and current.base_salary == data.base_salary and current.currency == data.currency:
            raise ValueError("No changes detected — salary and currency are identical to current values")

        new_record = SalaryRecord(
            employee_id=employee_uuid,
            base_salary=data.base_salary,
            currency=data.currency,
            effective_date=data.effective_date,
        )
        self.db.add(new_record)
        self.db.flush()

        salary_usd = self._convert_to_usd(data.base_salary, data.currency)

        return {
            "id": new_record.id,
            "base_salary": new_record.base_salary,
            "currency": new_record.currency,
            "effective_date": new_record.effective_date,
            "salary_usd": salary_usd,
            "created_at": new_record.created_at,
        }

    # ------------------------------------------------------------------
    # Salary history
    # ------------------------------------------------------------------

    def get_salary_history(self, employee_uuid: uuid.UUID) -> list[dict]:
        """
        Get all salary records for an employee, ordered by effective_date.

        Each record includes the USD-converted value.
        Returns empty list if no records found.
        """
        records = (
            self.db.query(SalaryRecord)
            .filter(SalaryRecord.employee_id == employee_uuid)
            .order_by(SalaryRecord.effective_date)
            .all()
        )

        return [
            {
                "id": r.id,
                "base_salary": r.base_salary,
                "currency": r.currency,
                "effective_date": r.effective_date,
                "salary_usd": self._convert_to_usd(r.base_salary, r.currency),
                "created_at": r.created_at,
            }
            for r in records
        ]

    # ------------------------------------------------------------------
    # Currency conversion
    # ------------------------------------------------------------------

    def _convert_to_usd(self, amount: Decimal, currency: str) -> Optional[Decimal]:
        """
        Convert an amount to USD using the exchange rate table.

        Formula: salary_usd = amount * rate_to_usd
        Returns None if the exchange rate is not found.
        """
        rate = (
            self.db.query(ExchangeRate)
            .filter(ExchangeRate.currency == currency)
            .first()
        )
        if not rate:
            return None

        result = amount * rate.rate_to_usd
        return result.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
