"""
Tests for SQLAlchemy models — Employee, SalaryRecord, ExchangeRate.

Written BEFORE the models exist (TDD). These tests define the expected
behavior and constraints for the data model.
"""

import uuid
from datetime import date, datetime
from decimal import Decimal

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.employee import Employee, EmployeeStatus
from app.models.salary_record import SalaryRecord
from app.models.exchange_rate import ExchangeRate


# ---------------------------------------------------------------------------
# Employee model tests
# ---------------------------------------------------------------------------


class TestEmployeeModel:
    """Tests for the Employee model validation and constraints."""

    def test_create_employee_with_valid_data(self, db_session):
        """An employee with all required fields should be persisted."""
        employee = Employee(
            employee_id="EMP-0001",
            full_name="Alice Johnson",
            email="alice@acme.com",
            department="Engineering",
            job_title="Software Engineer",
            country="US",
            status=EmployeeStatus.ACTIVE,
            joining_date=date(2023, 1, 15),
        )
        db_session.add(employee)
        db_session.flush()

        assert employee.id is not None
        assert employee.employee_id == "EMP-0001"
        assert employee.full_name == "Alice Johnson"
        assert employee.email == "alice@acme.com"
        assert employee.status == EmployeeStatus.ACTIVE
        assert employee.created_at is not None
        assert employee.updated_at is not None

    def test_employee_id_must_be_unique(self, db_session):
        """Two employees cannot share the same employee_id."""
        emp1 = Employee(
            employee_id="EMP-0001",
            full_name="Alice",
            email="alice@acme.com",
            department="Engineering",
            job_title="Software Engineer",
            country="US",
            status=EmployeeStatus.ACTIVE,
            joining_date=date(2023, 1, 15),
        )
        emp2 = Employee(
            employee_id="EMP-0001",
            full_name="Bob",
            email="bob@acme.com",
            department="Sales",
            job_title="Sales Rep",
            country="US",
            status=EmployeeStatus.ACTIVE,
            joining_date=date(2023, 2, 1),
        )
        db_session.add(emp1)
        db_session.flush()
        db_session.add(emp2)

        with pytest.raises(IntegrityError):
            db_session.flush()

    def test_email_must_be_unique(self, db_session):
        """Two employees cannot share the same email."""
        emp1 = Employee(
            employee_id="EMP-0001",
            full_name="Alice",
            email="same@acme.com",
            department="Engineering",
            job_title="Software Engineer",
            country="US",
            status=EmployeeStatus.ACTIVE,
            joining_date=date(2023, 1, 15),
        )
        emp2 = Employee(
            employee_id="EMP-0002",
            full_name="Bob",
            email="same@acme.com",
            department="Sales",
            job_title="Sales Rep",
            country="UK",
            status=EmployeeStatus.ACTIVE,
            joining_date=date(2023, 2, 1),
        )
        db_session.add(emp1)
        db_session.flush()
        db_session.add(emp2)

        with pytest.raises(IntegrityError):
            db_session.flush()

    def test_default_status_is_active(self, db_session):
        """A new employee should default to ACTIVE status."""
        employee = Employee(
            employee_id="EMP-0001",
            full_name="Alice",
            email="alice@acme.com",
            department="Engineering",
            job_title="Software Engineer",
            country="US",
            joining_date=date(2023, 1, 15),
        )
        db_session.add(employee)
        db_session.flush()

        assert employee.status == EmployeeStatus.ACTIVE

    def test_employee_can_be_deactivated(self, db_session):
        """An employee's status can be set to INACTIVE (soft delete)."""
        employee = Employee(
            employee_id="EMP-0001",
            full_name="Alice",
            email="alice@acme.com",
            department="Engineering",
            job_title="Software Engineer",
            country="US",
            status=EmployeeStatus.ACTIVE,
            joining_date=date(2023, 1, 15),
        )
        db_session.add(employee)
        db_session.flush()

        employee.status = EmployeeStatus.INACTIVE
        db_session.flush()

        assert employee.status == EmployeeStatus.INACTIVE

    def test_timestamps_are_auto_set(self, db_session):
        """created_at and updated_at should be automatically populated."""
        employee = Employee(
            employee_id="EMP-0001",
            full_name="Alice",
            email="alice@acme.com",
            department="Engineering",
            job_title="Software Engineer",
            country="US",
            joining_date=date(2023, 1, 15),
        )
        db_session.add(employee)
        db_session.flush()

        assert isinstance(employee.created_at, datetime)
        assert isinstance(employee.updated_at, datetime)


# ---------------------------------------------------------------------------
# SalaryRecord model tests
# ---------------------------------------------------------------------------


class TestSalaryRecordModel:
    """Tests for the SalaryRecord model — append-only salary history."""

    def _create_employee(self, db_session):
        """Helper to create a test employee."""
        employee = Employee(
            employee_id="EMP-0001",
            full_name="Alice",
            email="alice@acme.com",
            department="Engineering",
            job_title="Software Engineer",
            country="US",
            joining_date=date(2023, 1, 15),
        )
        db_session.add(employee)
        db_session.flush()
        return employee

    def test_create_salary_record(self, db_session):
        """A salary record should store amount, currency, and effective date."""
        employee = self._create_employee(db_session)

        record = SalaryRecord(
            employee_id=employee.id,
            base_salary=Decimal("85000.00"),
            currency="USD",
            effective_date=date(2023, 1, 15),
        )
        db_session.add(record)
        db_session.flush()

        assert record.id is not None
        assert record.base_salary == Decimal("85000.00")
        assert record.currency == "USD"
        assert record.effective_date == date(2023, 1, 15)

    def test_employee_can_have_multiple_salary_records(self, db_session):
        """Multiple salary records per employee — this is the salary history."""
        employee = self._create_employee(db_session)

        record1 = SalaryRecord(
            employee_id=employee.id,
            base_salary=Decimal("85000.00"),
            currency="USD",
            effective_date=date(2023, 1, 15),
        )
        record2 = SalaryRecord(
            employee_id=employee.id,
            base_salary=Decimal("95000.00"),
            currency="USD",
            effective_date=date(2024, 1, 15),
        )
        db_session.add_all([record1, record2])
        db_session.flush()

        assert len(employee.salary_records) == 2

    def test_salary_record_belongs_to_employee(self, db_session):
        """A salary record should reference its parent employee."""
        employee = self._create_employee(db_session)

        record = SalaryRecord(
            employee_id=employee.id,
            base_salary=Decimal("85000.00"),
            currency="USD",
            effective_date=date(2023, 1, 15),
        )
        db_session.add(record)
        db_session.flush()

        assert record.employee.id == employee.id

    def test_salary_record_requires_employee(self, db_session):
        """A salary record without an employee_id should fail."""
        record = SalaryRecord(
            base_salary=Decimal("85000.00"),
            currency="USD",
            effective_date=date(2023, 1, 15),
        )
        db_session.add(record)

        with pytest.raises(IntegrityError):
            db_session.flush()


# ---------------------------------------------------------------------------
# ExchangeRate model tests
# ---------------------------------------------------------------------------


class TestExchangeRateModel:
    """Tests for the ExchangeRate model — static currency conversion table."""

    def test_create_exchange_rate(self, db_session):
        """An exchange rate should store currency code and rate to USD."""
        rate = ExchangeRate(
            currency="INR",
            rate_to_usd=Decimal("0.012"),
        )
        db_session.add(rate)
        db_session.flush()

        assert rate.id is not None
        assert rate.currency == "INR"
        assert rate.rate_to_usd == Decimal("0.012")

    def test_currency_must_be_unique(self, db_session):
        """Only one exchange rate per currency is allowed."""
        rate1 = ExchangeRate(currency="INR", rate_to_usd=Decimal("0.012"))
        rate2 = ExchangeRate(currency="INR", rate_to_usd=Decimal("0.013"))
        db_session.add(rate1)
        db_session.flush()
        db_session.add(rate2)

        with pytest.raises(IntegrityError):
            db_session.flush()

    def test_usd_rate_is_one(self, db_session):
        """USD to USD should be 1.0 — the base currency."""
        rate = ExchangeRate(currency="USD", rate_to_usd=Decimal("1.0"))
        db_session.add(rate)
        db_session.flush()

        assert rate.rate_to_usd == Decimal("1.0")
