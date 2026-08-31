"""
API integration tests for the Salary endpoints.

Tests the full HTTP layer for salary management.
"""

import uuid


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _create_employee(client, name="Alice", email="alice@acme.com"):
    """Helper to create an employee via the API."""
    resp = client.post(
        "/api/employees",
        json={
            "full_name": name,
            "email": email,
            "department": "Engineering",
            "job_title": "SE",
            "country": "US",
            "joining_date": "2023-01-15",
            "base_salary": "85000.00",
            "currency": "USD",
        },
    )
    return resp.json()["id"]


def _seed_exchange_rates(db_session):
    """Seed exchange rates into the test DB."""
    from decimal import Decimal
    from app.models.exchange_rate import ExchangeRate

    rates = [
        ExchangeRate(currency="USD", rate_to_usd=Decimal("1.000000")),
        ExchangeRate(currency="GBP", rate_to_usd=Decimal("1.270000")),
        ExchangeRate(currency="INR", rate_to_usd=Decimal("0.012000")),
    ]
    for r in rates:
        db_session.add(r)
    db_session.flush()


# ---------------------------------------------------------------------------
# GET /api/employees/{id}/salary — Current salary
# ---------------------------------------------------------------------------


class TestGetCurrentSalaryAPI:
    """Tests for GET /api/employees/{id}/salary."""

    def test_get_current_salary(self, client, db_session):
        """Should return the current salary with USD conversion."""
        _seed_exchange_rates(db_session)
        emp_id = _create_employee(client)

        response = client.get(f"/api/employees/{emp_id}/salary")
        assert response.status_code == 200

        data = response.json()
        assert data["base_salary"] == "85000.00"
        assert data["currency"] == "USD"
        assert data["effective_date"] == "2023-01-15"
        assert data["salary_usd"] == "85000.00"

    def test_get_current_salary_nonexistent_returns_404(self, client):
        """Should return 404 for a non-existent employee."""
        response = client.get(f"/api/employees/{uuid.uuid4()}/salary")
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# POST /api/employees/{id}/salary — Update salary
# ---------------------------------------------------------------------------


class TestUpdateSalaryAPI:
    """Tests for POST /api/employees/{id}/salary."""

    def test_update_salary_returns_201(self, client, db_session):
        """Updating salary should return 201 with the new record."""
        _seed_exchange_rates(db_session)
        emp_id = _create_employee(client)

        response = client.post(
            f"/api/employees/{emp_id}/salary",
            json={
                "base_salary": "95000.00",
                "currency": "USD",
                "effective_date": "2024-01-15",
            },
        )
        assert response.status_code == 201

        data = response.json()
        assert data["base_salary"] == "95000.00"
        assert data["currency"] == "USD"
        assert data["salary_usd"] == "95000.00"

    def test_update_salary_with_foreign_currency(self, client, db_session):
        """Should correctly convert foreign currency to USD."""
        _seed_exchange_rates(db_session)
        emp_id = _create_employee(client)

        response = client.post(
            f"/api/employees/{emp_id}/salary",
            json={
                "base_salary": "70000.00",
                "currency": "GBP",
                "effective_date": "2024-06-01",
            },
        )
        assert response.status_code == 201
        data = response.json()
        # 70000 * 1.27 = 88900
        assert data["salary_usd"] == "88900.00"

    def test_update_salary_nonexistent_employee_returns_404(self, client):
        """Should return 404 for a non-existent employee."""
        response = client.post(
            f"/api/employees/{uuid.uuid4()}/salary",
            json={
                "base_salary": "90000",
                "currency": "USD",
                "effective_date": "2024-01-01",
            },
        )
        assert response.status_code == 404

    def test_update_salary_preserves_history(self, client, db_session):
        """After updating, history should contain both old and new records."""
        _seed_exchange_rates(db_session)
        emp_id = _create_employee(client)

        # Update salary
        client.post(
            f"/api/employees/{emp_id}/salary",
            json={
                "base_salary": "95000.00",
                "currency": "USD",
                "effective_date": "2024-01-15",
            },
        )

        # Check history
        response = client.get(f"/api/employees/{emp_id}/salary/history")
        data = response.json()
        assert len(data["records"]) == 2

    def test_update_salary_with_negative_amount_returns_422(self, client, db_session):
        """Negative salary should be rejected."""
        _seed_exchange_rates(db_session)
        emp_id = _create_employee(client)

        response = client.post(
            f"/api/employees/{emp_id}/salary",
            json={
                "base_salary": "-5000",
                "currency": "USD",
                "effective_date": "2024-01-01",
            },
        )
        assert response.status_code == 422

    def test_update_salary_with_identical_values_returns_409(self, client, db_session):
        """Updating with identical salary values should return 409 Conflict."""
        _seed_exchange_rates(db_session)
        emp_id = _create_employee(client)

        response = client.post(
            f"/api/employees/{emp_id}/salary",
            json={
                "base_salary": "85000.00",
                "currency": "USD",
                "effective_date": "2024-01-01",
            },
        )
        assert response.status_code == 409
        assert "No changes detected" in response.json()["detail"]


# ---------------------------------------------------------------------------
# GET /api/employees/{id}/salary/history — Salary history
# ---------------------------------------------------------------------------


class TestSalaryHistoryAPI:
    """Tests for GET /api/employees/{id}/salary/history."""

    def test_get_salary_history(self, client, db_session):
        """Should return all salary records."""
        _seed_exchange_rates(db_session)
        emp_id = _create_employee(client)

        response = client.get(f"/api/employees/{emp_id}/salary/history")
        assert response.status_code == 200

        data = response.json()
        assert "records" in data
        assert len(data["records"]) == 1  # just the initial record

    def test_salary_history_after_multiple_updates(self, client, db_session):
        """Should contain all records after multiple salary updates."""
        _seed_exchange_rates(db_session)
        emp_id = _create_employee(client)

        # Add two more salary updates
        client.post(
            f"/api/employees/{emp_id}/salary",
            json={"base_salary": "90000", "currency": "USD", "effective_date": "2023-07-01"},
        )
        client.post(
            f"/api/employees/{emp_id}/salary",
            json={"base_salary": "95000", "currency": "USD", "effective_date": "2024-01-01"},
        )

        response = client.get(f"/api/employees/{emp_id}/salary/history")
        data = response.json()
        assert len(data["records"]) == 3

        # Should be ordered by effective_date
        dates = [r["effective_date"] for r in data["records"]]
        assert dates == sorted(dates)

    def test_salary_history_nonexistent_employee(self, client):
        """Should return empty records for a non-existent employee."""
        response = client.get(f"/api/employees/{uuid.uuid4()}/salary/history")
        assert response.status_code == 200
        assert response.json()["records"] == []
