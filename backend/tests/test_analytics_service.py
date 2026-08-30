"""
Tests for the AnalyticsService — salary aggregations by department, country, and overall.

Written BEFORE the service exists (TDD).
"""

from datetime import date
from decimal import Decimal

import pytest

from app.models.employee import Employee, EmployeeStatus
from app.models.exchange_rate import ExchangeRate
from app.models.salary_record import SalaryRecord
from app.services.analytics_service import AnalyticsService


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
def analytics_service(db_session):
    """Provide an AnalyticsService wired to the test DB session."""
    return AnalyticsService(db_session)


def _create_employee_with_salary(
    db_session, emp_id, name, email, department, country, salary, currency
):
    """Helper to create an employee with a salary record."""
    employee = Employee(
        employee_id=emp_id,
        full_name=name,
        email=email,
        department=department,
        job_title="Engineer",
        country=country,
        status=EmployeeStatus.ACTIVE,
        joining_date=date(2023, 1, 15),
    )
    db_session.add(employee)
    db_session.flush()

    record = SalaryRecord(
        employee_id=employee.id,
        base_salary=Decimal(str(salary)),
        currency=currency,
        effective_date=date(2023, 1, 15),
    )
    db_session.add(record)
    db_session.flush()
    return employee


@pytest.fixture()
def seeded_employees(db_session):
    """Create a set of employees for analytics tests."""
    employees = [
        # US Engineering
        ("EMP-00001", "Alice", "alice@acme.com", "Engineering", "US", 100000, "USD"),
        ("EMP-00002", "Bob", "bob@acme.com", "Engineering", "US", 120000, "USD"),
        # US Sales
        ("EMP-00003", "Charlie", "charlie@acme.com", "Sales", "US", 80000, "USD"),
        # UK Engineering
        ("EMP-00004", "Diana", "diana@acme.com", "Engineering", "UK", 70000, "GBP"),
        # India Engineering
        ("EMP-00005", "Raj", "raj@acme.com", "Engineering", "India", 2000000, "INR"),
    ]
    created = []
    for emp_id, name, email, dept, country, salary, currency in employees:
        emp = _create_employee_with_salary(
            db_session, emp_id, name, email, dept, country, salary, currency
        )
        created.append(emp)
    return created


# ---------------------------------------------------------------------------
# Department aggregation tests
# ---------------------------------------------------------------------------


class TestDepartmentStats:
    """Tests for salary aggregations by department."""

    def test_avg_salary_by_department(
        self, analytics_service, seeded_employees, exchange_rates
    ):
        """Should calculate average USD salary per department."""
        result = analytics_service.get_department_stats()

        dept_map = {d["department"]: d for d in result}
        assert "Engineering" in dept_map
        assert "Sales" in dept_map

        eng = dept_map["Engineering"]
        assert eng["employee_count"] == 4  # 2 US + 1 UK + 1 India

    def test_department_stats_include_min_max(
        self, analytics_service, seeded_employees, exchange_rates
    ):
        """Should include min and max salary per department."""
        result = analytics_service.get_department_stats()
        dept_map = {d["department"]: d for d in result}

        eng = dept_map["Engineering"]
        # Min should be India: 2000000 * 0.012 = 24000
        assert eng["min_salary_usd"] == Decimal("24000.00")
        # Max should be Bob: 120000 * 1.0 = 120000
        assert eng["max_salary_usd"] == Decimal("120000.00")

    def test_department_stats_total_payroll(
        self, analytics_service, seeded_employees, exchange_rates
    ):
        """Should calculate total payroll per department in USD."""
        result = analytics_service.get_department_stats()
        dept_map = {d["department"]: d for d in result}

        # Sales: only Charlie at 80000 USD
        sales = dept_map["Sales"]
        assert sales["total_payroll_usd"] == Decimal("80000.00")
        assert sales["employee_count"] == 1


# ---------------------------------------------------------------------------
# Country aggregation tests
# ---------------------------------------------------------------------------


class TestCountryStats:
    """Tests for salary aggregations by country."""

    def test_avg_salary_by_country(
        self, analytics_service, seeded_employees, exchange_rates
    ):
        """Should calculate average salary per country in both local and USD."""
        result = analytics_service.get_country_stats()

        country_map = {c["country"]: c for c in result}
        assert "US" in country_map
        assert "UK" in country_map
        assert "India" in country_map

        us = country_map["US"]
        assert us["employee_count"] == 3  # Alice, Bob, Charlie
        # Average: (100000 + 120000 + 80000) / 3 = 100000
        assert us["avg_salary_usd"] == Decimal("100000.00")

    def test_country_stats_foreign_currency(
        self, analytics_service, seeded_employees, exchange_rates
    ):
        """Should correctly convert foreign currencies to USD for country stats."""
        result = analytics_service.get_country_stats()
        country_map = {c["country"]: c for c in result}

        india = country_map["India"]
        assert india["currency"] == "INR"
        assert india["avg_salary_local"] == Decimal("2000000.00")
        # 2000000 * 0.012 = 24000
        assert india["avg_salary_usd"] == Decimal("24000.00")

    def test_country_stats_total_payroll(
        self, analytics_service, seeded_employees, exchange_rates
    ):
        """Should calculate total payroll per country in USD."""
        result = analytics_service.get_country_stats()
        country_map = {c["country"]: c for c in result}

        uk = country_map["UK"]
        # Diana: 70000 GBP * 1.27 = 88900
        assert uk["total_payroll_usd"] == Decimal("88900.00")


# ---------------------------------------------------------------------------
# Summary stats tests
# ---------------------------------------------------------------------------


class TestSummaryStats:
    """Tests for global salary summary."""

    def test_summary_total_employees(
        self, analytics_service, seeded_employees, exchange_rates
    ):
        """Should count all active employees."""
        result = analytics_service.get_summary()
        assert result["total_employees"] == 5

    def test_summary_min_max(
        self, analytics_service, seeded_employees, exchange_rates
    ):
        """Should find the global min and max salary in USD."""
        result = analytics_service.get_summary()
        # Min: India 24000, Max: Bob 120000
        assert result["min_salary_usd"] == Decimal("24000.00")
        assert result["max_salary_usd"] == Decimal("120000.00")

    def test_summary_total_payroll(
        self, analytics_service, seeded_employees, exchange_rates
    ):
        """Total payroll should be sum of all salaries in USD."""
        result = analytics_service.get_summary()
        # Alice:100000 + Bob:120000 + Charlie:80000 + Diana:88900 + Raj:24000 = 412900
        assert result["total_payroll_usd"] == Decimal("412900.00")

    def test_summary_avg_salary(
        self, analytics_service, seeded_employees, exchange_rates
    ):
        """Average salary should be total payroll / employee count."""
        result = analytics_service.get_summary()
        # 412900 / 5 = 82580
        assert result["avg_salary_usd"] == Decimal("82580.00")

    def test_summary_excludes_inactive_employees(
        self, analytics_service, seeded_employees, exchange_rates, db_session
    ):
        """Inactive employees should be excluded from analytics."""
        # Deactivate Alice
        alice = seeded_employees[0]
        alice.status = EmployeeStatus.INACTIVE
        db_session.flush()

        result = analytics_service.get_summary()
        assert result["total_employees"] == 4

    def test_empty_database(self, analytics_service, exchange_rates):
        """Should handle empty database gracefully."""
        result = analytics_service.get_summary()
        assert result["total_employees"] == 0
        assert result["total_payroll_usd"] == Decimal("0")
