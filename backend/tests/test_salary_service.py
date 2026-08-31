"""
Tests for the SalaryService — salary updates, history, and currency conversion.

Written BEFORE the service exists (TDD).
"""

from datetime import date
from decimal import Decimal

import pytest

from app.models.employee import Employee, EmployeeStatus
from app.models.exchange_rate import ExchangeRate
from app.models.salary_record import SalaryRecord
from app.schemas.salary import SalaryUpdate
from app.services.salary_service import SalaryService


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def exchange_rates(db_session):
    """Seed exchange rates for testing."""
    rates = [
        ExchangeRate(currency="USD", rate_to_usd=Decimal("1.000000")),
        ExchangeRate(currency="GBP", rate_to_usd=Decimal("1.270000")),
        ExchangeRate(currency="INR", rate_to_usd=Decimal("0.012000")),
    ]
    for r in rates:
        db_session.add(r)
    db_session.flush()
    return rates


@pytest.fixture()
def sample_employee(db_session):
    """Create a test employee with an initial salary record."""
    employee = Employee(
        employee_id="EMP-00001",
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

    initial_salary = SalaryRecord(
        employee_id=employee.id,
        base_salary=Decimal("85000.00"),
        currency="USD",
        effective_date=date(2023, 1, 15),
    )
    db_session.add(initial_salary)
    db_session.flush()
    return employee


@pytest.fixture()
def salary_service(db_session):
    """Provide a SalaryService wired to the test DB session."""
    return SalaryService(db_session)


# ---------------------------------------------------------------------------
# Get current salary tests
# ---------------------------------------------------------------------------


class TestGetCurrentSalary:
    """Tests for retrieving the current (latest) salary."""

    def test_get_current_salary(self, salary_service, sample_employee, exchange_rates):
        """Should return the latest salary record with USD conversion."""
        result = salary_service.get_current_salary(sample_employee.id)

        assert result is not None
        assert result["base_salary"] == Decimal("85000.00")
        assert result["currency"] == "USD"
        assert result["salary_usd"] == Decimal("85000.00")  # USD * 1.0

    def test_get_current_salary_with_foreign_currency(
        self, salary_service, db_session, exchange_rates
    ):
        """Should convert foreign currency to USD using exchange rate."""
        employee = Employee(
            employee_id="EMP-00002",
            full_name="Raj Kumar",
            email="raj@acme.com",
            department="Engineering",
            job_title="Software Engineer",
            country="India",
            status=EmployeeStatus.ACTIVE,
            joining_date=date(2023, 1, 15),
        )
        db_session.add(employee)
        db_session.flush()

        salary = SalaryRecord(
            employee_id=employee.id,
            base_salary=Decimal("2000000.00"),
            currency="INR",
            effective_date=date(2023, 1, 15),
        )
        db_session.add(salary)
        db_session.flush()

        result = salary_service.get_current_salary(employee.id)
        assert result is not None
        assert result["base_salary"] == Decimal("2000000.00")
        assert result["currency"] == "INR"
        # 2000000 * 0.012 = 24000
        assert result["salary_usd"] == Decimal("24000.00")

    def test_get_current_salary_returns_latest(
        self, salary_service, sample_employee, db_session, exchange_rates
    ):
        """When multiple records exist, should return the one with the latest effective_date."""
        # Add a newer salary record
        newer_salary = SalaryRecord(
            employee_id=sample_employee.id,
            base_salary=Decimal("95000.00"),
            currency="USD",
            effective_date=date(2024, 1, 15),
        )
        db_session.add(newer_salary)
        db_session.flush()

        result = salary_service.get_current_salary(sample_employee.id)
        assert result["base_salary"] == Decimal("95000.00")
        assert result["effective_date"] == date(2024, 1, 15)

    def test_get_current_salary_nonexistent_employee(self, salary_service):
        """Should return None for a non-existent employee."""
        import uuid

        result = salary_service.get_current_salary(uuid.uuid4())
        assert result is None


# ---------------------------------------------------------------------------
# Update salary tests
# ---------------------------------------------------------------------------


class TestUpdateSalary:
    """Tests for updating salary (creating a new salary record)."""

    def test_update_salary_creates_new_record(
        self, salary_service, sample_employee, exchange_rates
    ):
        """Updating salary should create a NEW record, not overwrite the old one."""
        update_data = SalaryUpdate(
            base_salary=Decimal("95000.00"),
            currency="USD",
            effective_date=date(2024, 1, 15),
        )
        result = salary_service.update_salary(sample_employee.id, update_data)

        assert result is not None
        assert result["base_salary"] == Decimal("95000.00")

        # Original record should still exist
        history = salary_service.get_salary_history(sample_employee.id)
        assert len(history) == 2

    def test_update_salary_returns_usd_conversion(
        self, salary_service, sample_employee, exchange_rates
    ):
        """Updated salary should include the USD-converted value."""
        update_data = SalaryUpdate(
            base_salary=Decimal("70000.00"),
            currency="GBP",
            effective_date=date(2024, 6, 1),
        )
        result = salary_service.update_salary(sample_employee.id, update_data)

        # 70000 * 1.27 = 88900
        assert result["salary_usd"] == Decimal("88900.00")

    def test_update_salary_with_identical_values_raises_value_error(
        self, salary_service, sample_employee, exchange_rates
    ):
        """Updating salary with exact same amount and currency should be rejected."""
        update_data = SalaryUpdate(
            base_salary=Decimal("85000.00"),
            currency="USD",
            effective_date=date(2024, 1, 15),
        )
        with pytest.raises(ValueError, match="No changes detected"):
            salary_service.update_salary(sample_employee.id, update_data)

    def test_update_salary_nonexistent_employee(self, salary_service):
        """Updating salary for a non-existent employee should return None."""
        import uuid

        update_data = SalaryUpdate(
            base_salary=Decimal("90000.00"),
            currency="USD",
            effective_date=date(2024, 1, 1),
        )
        result = salary_service.update_salary(uuid.uuid4(), update_data)
        assert result is None


# ---------------------------------------------------------------------------
# Salary history tests
# ---------------------------------------------------------------------------


class TestGetSalaryHistory:
    """Tests for retrieving salary history."""

    def test_get_history_returns_all_records(
        self, salary_service, sample_employee, db_session, exchange_rates
    ):
        """Should return all salary records ordered by effective_date."""
        # Add more records
        records = [
            SalaryRecord(
                employee_id=sample_employee.id,
                base_salary=Decimal("90000.00"),
                currency="USD",
                effective_date=date(2023, 7, 1),
            ),
            SalaryRecord(
                employee_id=sample_employee.id,
                base_salary=Decimal("95000.00"),
                currency="USD",
                effective_date=date(2024, 1, 1),
            ),
        ]
        for r in records:
            db_session.add(r)
        db_session.flush()

        history = salary_service.get_salary_history(sample_employee.id)

        assert len(history) == 3  # initial + 2 new
        # Should be ordered by effective_date
        dates = [r["effective_date"] for r in history]
        assert dates == sorted(dates)

    def test_get_history_includes_usd_conversion(
        self, salary_service, sample_employee, exchange_rates
    ):
        """Each history record should include the USD-converted value."""
        history = salary_service.get_salary_history(sample_employee.id)

        for record in history:
            assert "salary_usd" in record
            assert record["salary_usd"] is not None

    def test_get_history_nonexistent_employee(self, salary_service):
        """Should return empty list for a non-existent employee."""
        import uuid

        history = salary_service.get_salary_history(uuid.uuid4())
        assert history == []
