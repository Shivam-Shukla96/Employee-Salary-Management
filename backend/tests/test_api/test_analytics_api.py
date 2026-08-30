"""
API integration tests for the Analytics endpoints.
"""

import uuid
from decimal import Decimal

import pytest

from app.models.exchange_rate import ExchangeRate


def _seed_exchange_rates(db_session):
    """Seed exchange rates into the test DB."""
    rates = [
        ExchangeRate(currency="USD", rate_to_usd=Decimal("1.000000")),
        ExchangeRate(currency="GBP", rate_to_usd=Decimal("1.270000")),
        ExchangeRate(currency="INR", rate_to_usd=Decimal("0.012000")),
    ]
    for r in rates:
        db_session.add(r)
    db_session.flush()


def _create_employee(client, name, email, country, department, salary, currency):
    """Create an employee via the API."""
    return client.post(
        "/api/employees",
        json={
            "full_name": name,
            "email": email,
            "department": department,
            "job_title": "Engineer",
            "country": country,
            "joining_date": "2023-01-15",
            "base_salary": str(salary),
            "currency": currency,
        },
    )


@pytest.fixture()
def populated_db(client, db_session):
    """Create employees across departments and countries for analytics tests."""
    _seed_exchange_rates(db_session)
    _create_employee(client, "Alice", "alice@a.com", "US", "Engineering", 100000, "USD")
    _create_employee(client, "Bob", "bob@a.com", "US", "Engineering", 120000, "USD")
    _create_employee(client, "Charlie", "charlie@a.com", "US", "Sales", 80000, "USD")
    _create_employee(client, "Diana", "diana@a.com", "UK", "Engineering", 70000, "GBP")
    _create_employee(client, "Raj", "raj@a.com", "India", "Engineering", 2000000, "INR")


# ---------------------------------------------------------------------------
# GET /api/analytics — Full analytics
# ---------------------------------------------------------------------------


class TestFullAnalyticsAPI:
    """Tests for GET /api/analytics."""

    def test_full_analytics_response_shape(self, client, populated_db):
        """Should return summary, by_department, and by_country."""
        response = client.get("/api/analytics")
        assert response.status_code == 200

        data = response.json()
        assert "summary" in data
        assert "by_department" in data
        assert "by_country" in data

    def test_full_analytics_summary(self, client, populated_db):
        """Summary should contain correct totals."""
        data = client.get("/api/analytics").json()
        summary = data["summary"]

        assert summary["total_employees"] == 5
        assert Decimal(summary["total_payroll_usd"]) == Decimal("412900.00")

    def test_full_analytics_departments(self, client, populated_db):
        """Should have stats for each department."""
        data = client.get("/api/analytics").json()
        depts = {d["department"]: d for d in data["by_department"]}

        assert "Engineering" in depts
        assert "Sales" in depts
        assert depts["Engineering"]["employee_count"] == 4

    def test_full_analytics_countries(self, client, populated_db):
        """Should have stats for each country."""
        data = client.get("/api/analytics").json()
        countries = {c["country"]: c for c in data["by_country"]}

        assert "US" in countries
        assert "UK" in countries
        assert "India" in countries


# ---------------------------------------------------------------------------
# GET /api/analytics/summary
# ---------------------------------------------------------------------------


class TestSummaryAPI:
    """Tests for GET /api/analytics/summary."""

    def test_summary_endpoint(self, client, populated_db):
        """Should return global salary summary."""
        response = client.get("/api/analytics/summary")
        assert response.status_code == 200

        data = response.json()
        assert data["total_employees"] == 5
        assert "avg_salary_usd" in data
        assert "min_salary_usd" in data
        assert "max_salary_usd" in data

    def test_summary_empty_db(self, client, db_session):
        """Should handle empty database."""
        _seed_exchange_rates(db_session)
        response = client.get("/api/analytics/summary")
        assert response.status_code == 200
        assert response.json()["total_employees"] == 0


# ---------------------------------------------------------------------------
# GET /api/analytics/by-department
# ---------------------------------------------------------------------------


class TestDepartmentStatsAPI:
    """Tests for GET /api/analytics/by-department."""

    def test_department_stats(self, client, populated_db):
        """Should return stats for each department."""
        response = client.get("/api/analytics/by-department")
        assert response.status_code == 200

        data = response.json()
        assert len(data) == 2  # Engineering, Sales
        for dept in data:
            assert "department" in dept
            assert "avg_salary_usd" in dept
            assert "min_salary_usd" in dept
            assert "max_salary_usd" in dept
            assert "total_payroll_usd" in dept


# ---------------------------------------------------------------------------
# GET /api/analytics/by-country
# ---------------------------------------------------------------------------


class TestCountryStatsAPI:
    """Tests for GET /api/analytics/by-country."""

    def test_country_stats(self, client, populated_db):
        """Should return stats for each country."""
        response = client.get("/api/analytics/by-country")
        assert response.status_code == 200

        data = response.json()
        assert len(data) == 3  # US, UK, India
        for country in data:
            assert "country" in country
            assert "currency" in country
            assert "avg_salary_local" in country
            assert "avg_salary_usd" in country
            assert "total_payroll_usd" in country

    def test_country_stats_correct_conversion(self, client, populated_db):
        """USD conversion should be correct for each country."""
        data = client.get("/api/analytics/by-country").json()
        country_map = {c["country"]: c for c in data}

        india = country_map["India"]
        assert india["currency"] == "INR"
        assert Decimal(india["avg_salary_usd"]) == Decimal("24000.00")
