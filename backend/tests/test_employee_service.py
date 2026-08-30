"""
Tests for the EmployeeService — business logic for employee CRUD.

Written BEFORE the service exists (TDD).
"""

from datetime import date
from decimal import Decimal

import pytest

from app.models.employee import Employee, EmployeeStatus
from app.models.salary_record import SalaryRecord
from app.models.exchange_rate import ExchangeRate
from app.schemas.employee import EmployeeCreate, EmployeeUpdate
from app.services.employee_service import EmployeeService


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def employee_service(db_session):
    """Provide an EmployeeService instance wired to the test DB session."""
    return EmployeeService(db_session)


@pytest.fixture()
def sample_employee_data():
    """Valid employee creation data."""
    return EmployeeCreate(
        full_name="Alice Johnson",
        email="alice@acme.com",
        department="Engineering",
        job_title="Software Engineer",
        country="US",
        joining_date=date(2023, 1, 15),
        base_salary=Decimal("85000.00"),
        currency="USD",
    )


@pytest.fixture()
def seeded_exchange_rates(db_session):
    """Seed exchange rates needed for USD conversion."""
    rates = [
        ExchangeRate(currency="USD", rate_to_usd=Decimal("1.000000")),
        ExchangeRate(currency="INR", rate_to_usd=Decimal("0.012000")),
        ExchangeRate(currency="GBP", rate_to_usd=Decimal("1.270000")),
    ]
    for r in rates:
        db_session.add(r)
    db_session.flush()
    return rates


# ---------------------------------------------------------------------------
# Create tests
# ---------------------------------------------------------------------------


class TestCreateEmployee:
    """Tests for creating a new employee."""

    def test_create_employee_returns_employee_with_id(
        self, employee_service, sample_employee_data
    ):
        """Creating an employee should return an employee with a generated employee_id."""
        employee = employee_service.create(sample_employee_data)

        assert employee.id is not None
        assert employee.employee_id is not None
        assert employee.employee_id.startswith("EMP-")
        assert employee.full_name == "Alice Johnson"
        assert employee.email == "alice@acme.com"
        assert employee.department == "Engineering"
        assert employee.status == EmployeeStatus.ACTIVE

    def test_create_employee_creates_initial_salary_record(
        self, employee_service, sample_employee_data
    ):
        """Creating an employee should also create an initial salary record."""
        employee = employee_service.create(sample_employee_data)

        assert len(employee.salary_records) == 1
        record = employee.salary_records[0]
        assert record.base_salary == Decimal("85000.00")
        assert record.currency == "USD"
        assert record.effective_date == date(2023, 1, 15)

    def test_create_employee_with_duplicate_email_raises(
        self, employee_service, sample_employee_data
    ):
        """Creating two employees with the same email should raise an error."""
        employee_service.create(sample_employee_data)

        with pytest.raises(ValueError, match="email"):
            employee_service.create(sample_employee_data)

    def test_employee_ids_are_sequential(self, employee_service):
        """Employee IDs should be generated sequentially (EMP-00001, EMP-00002, ...)."""
        emp1 = employee_service.create(
            EmployeeCreate(
                full_name="A",
                email="a@acme.com",
                department="Engineering",
                job_title="SE",
                country="US",
                joining_date=date(2023, 1, 1),
                base_salary=Decimal("80000"),
                currency="USD",
            )
        )
        emp2 = employee_service.create(
            EmployeeCreate(
                full_name="B",
                email="b@acme.com",
                department="Sales",
                job_title="SR",
                country="UK",
                joining_date=date(2023, 2, 1),
                base_salary=Decimal("60000"),
                currency="GBP",
            )
        )
        # IDs should be sequential
        id1 = int(emp1.employee_id.split("-")[1])
        id2 = int(emp2.employee_id.split("-")[1])
        assert id2 == id1 + 1


# ---------------------------------------------------------------------------
# Read / List tests
# ---------------------------------------------------------------------------


class TestGetEmployee:
    """Tests for retrieving employees."""

    def test_get_by_id(self, employee_service, sample_employee_data):
        """Should retrieve an employee by their UUID."""
        created = employee_service.create(sample_employee_data)
        found = employee_service.get_by_id(created.id)

        assert found is not None
        assert found.id == created.id
        assert found.full_name == "Alice Johnson"

    def test_get_by_id_not_found_returns_none(self, employee_service):
        """Should return None for a non-existent UUID."""
        import uuid

        result = employee_service.get_by_id(uuid.uuid4())
        assert result is None


class TestListEmployees:
    """Tests for listing employees with filtering and pagination."""

    def _seed_employees(self, employee_service):
        """Create a few test employees for list/filter tests."""
        employees_data = [
            EmployeeCreate(
                full_name="Alice US",
                email="alice@acme.com",
                department="Engineering",
                job_title="Software Engineer",
                country="US",
                joining_date=date(2023, 1, 15),
                base_salary=Decimal("85000"),
                currency="USD",
            ),
            EmployeeCreate(
                full_name="Bob UK",
                email="bob@acme.com",
                department="Sales",
                job_title="Sales Rep",
                country="UK",
                joining_date=date(2023, 2, 1),
                base_salary=Decimal("45000"),
                currency="GBP",
            ),
            EmployeeCreate(
                full_name="Charlie India",
                email="charlie@acme.com",
                department="Engineering",
                job_title="Senior Software Engineer",
                country="India",
                joining_date=date(2023, 3, 10),
                base_salary=Decimal("2000000"),
                currency="INR",
            ),
        ]
        created = []
        for data in employees_data:
            created.append(employee_service.create(data))
        return created

    def test_list_all_returns_paginated_result(self, employee_service):
        """List should return all employees with pagination info."""
        self._seed_employees(employee_service)
        result = employee_service.list_employees(page=1, page_size=10)

        assert result["total"] == 3
        assert len(result["items"]) == 3
        assert result["page"] == 1

    def test_list_with_pagination(self, employee_service):
        """Should respect page and page_size parameters."""
        self._seed_employees(employee_service)
        result = employee_service.list_employees(page=1, page_size=2)

        assert result["total"] == 3
        assert len(result["items"]) == 2
        assert result["total_pages"] == 2

    def test_filter_by_country(self, employee_service):
        """Should filter employees by country."""
        self._seed_employees(employee_service)
        result = employee_service.list_employees(page=1, page_size=10, country="US")

        assert result["total"] == 1
        assert result["items"][0].country == "US"

    def test_filter_by_department(self, employee_service):
        """Should filter employees by department."""
        self._seed_employees(employee_service)
        result = employee_service.list_employees(
            page=1, page_size=10, department="Engineering"
        )

        assert result["total"] == 2
        for emp in result["items"]:
            assert emp.department == "Engineering"

    def test_search_by_name(self, employee_service):
        """Should search employees by name (case-insensitive partial match)."""
        self._seed_employees(employee_service)
        result = employee_service.list_employees(page=1, page_size=10, search="alice")

        assert result["total"] == 1
        assert "Alice" in result["items"][0].full_name

    def test_search_by_employee_id(self, employee_service):
        """Should search employees by employee_id."""
        created = self._seed_employees(employee_service)
        emp_id = created[0].employee_id

        result = employee_service.list_employees(page=1, page_size=10, search=emp_id)
        assert result["total"] == 1

    def test_filter_by_status(self, employee_service):
        """Should filter by active/inactive status."""
        self._seed_employees(employee_service)
        # Deactivate one
        employee_service.soft_delete(
            employee_service.list_employees(page=1, page_size=10)["items"][0].id
        )

        active = employee_service.list_employees(page=1, page_size=10, status="active")
        assert active["total"] == 2

        inactive = employee_service.list_employees(
            page=1, page_size=10, status="inactive"
        )
        assert inactive["total"] == 1


# ---------------------------------------------------------------------------
# Update tests
# ---------------------------------------------------------------------------


class TestUpdateEmployee:
    """Tests for updating employee details."""

    def test_update_employee_fields(self, employee_service, sample_employee_data):
        """Should update only the provided fields."""
        created = employee_service.create(sample_employee_data)
        updated = employee_service.update(
            created.id,
            EmployeeUpdate(department="Product", job_title="Product Manager"),
        )

        assert updated.department == "Product"
        assert updated.job_title == "Product Manager"
        # Unchanged fields should remain
        assert updated.full_name == "Alice Johnson"
        assert updated.email == "alice@acme.com"

    def test_update_nonexistent_employee_returns_none(self, employee_service):
        """Updating a non-existent employee should return None."""
        import uuid

        result = employee_service.update(
            uuid.uuid4(), EmployeeUpdate(full_name="Ghost")
        )
        assert result is None


# ---------------------------------------------------------------------------
# Soft delete tests
# ---------------------------------------------------------------------------


class TestSoftDelete:
    """Tests for soft-deleting (deactivating) employees."""

    def test_soft_delete_sets_inactive(self, employee_service, sample_employee_data):
        """Soft delete should set the employee's status to INACTIVE."""
        created = employee_service.create(sample_employee_data)
        result = employee_service.soft_delete(created.id)

        assert result is not None
        assert result.status == EmployeeStatus.INACTIVE

    def test_soft_delete_nonexistent_returns_none(self, employee_service):
        """Soft deleting a non-existent employee should return None."""
        import uuid

        result = employee_service.soft_delete(uuid.uuid4())
        assert result is None

    def test_soft_deleted_employee_still_in_database(
        self, employee_service, sample_employee_data
    ):
        """A soft-deleted employee should still be retrievable by ID."""
        created = employee_service.create(sample_employee_data)
        employee_service.soft_delete(created.id)

        found = employee_service.get_by_id(created.id)
        assert found is not None
        assert found.status == EmployeeStatus.INACTIVE
