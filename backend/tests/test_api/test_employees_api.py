"""
API integration tests for the Employee endpoints.

Tests the full HTTP layer: status codes, response shapes, pagination, error handling.
"""

from datetime import date
from decimal import Decimal


# ---------------------------------------------------------------------------
# POST /api/employees — Create
# ---------------------------------------------------------------------------


class TestCreateEmployeeAPI:
    """Tests for POST /api/employees."""

    def test_create_employee_returns_201(self, client):
        """Creating a valid employee should return 201 with the employee data."""
        response = client.post(
            "/api/employees",
            json={
                "full_name": "Alice Johnson",
                "email": "alice@acme.com",
                "department": "Engineering",
                "job_title": "Software Engineer",
                "country": "US",
                "joining_date": "2023-01-15",
                "base_salary": "85000.00",
                "currency": "USD",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["full_name"] == "Alice Johnson"
        assert data["employee_id"].startswith("EMP-")
        assert data["status"] == "active"
        assert data["current_salary"]["base_salary"] == "85000.00"

    def test_create_employee_with_missing_fields_returns_422(self, client):
        """Missing required fields should return 422."""
        response = client.post(
            "/api/employees",
            json={"full_name": "Incomplete"},
        )
        assert response.status_code == 422

    def test_create_employee_with_duplicate_email_returns_409(self, client):
        """Duplicate email should return 409 Conflict."""
        payload = {
            "full_name": "Alice",
            "email": "duplicate@acme.com",
            "department": "Engineering",
            "job_title": "SE",
            "country": "US",
            "joining_date": "2023-01-15",
            "base_salary": "80000",
            "currency": "USD",
        }
        client.post("/api/employees", json=payload)
        response = client.post("/api/employees", json=payload)
        assert response.status_code == 409

    def test_create_employee_with_negative_salary_returns_422(self, client):
        """Negative salary should be rejected by validation."""
        response = client.post(
            "/api/employees",
            json={
                "full_name": "Alice",
                "email": "alice@acme.com",
                "department": "Engineering",
                "job_title": "SE",
                "country": "US",
                "joining_date": "2023-01-15",
                "base_salary": "-1000",
                "currency": "USD",
            },
        )
        assert response.status_code == 422

    def test_create_employee_with_invalid_country_returns_422(self, client):
        """Invalid country name should be rejected with 422."""
        response = client.post(
            "/api/employees",
            json={
                "full_name": "Alice",
                "email": "alice_invalid_country@acme.com",
                "department": "Engineering",
                "job_title": "SE",
                "country": "Atlantis",
                "joining_date": "2023-01-15",
                "base_salary": "80000",
                "currency": "USD",
            },
        )
        assert response.status_code == 422

    def test_create_employee_with_invalid_department_returns_422(self, client):
        """Invalid department name should be rejected with 422."""
        response = client.post(
            "/api/employees",
            json={
                "full_name": "Alice",
                "email": "alice_invalid_dept@acme.com",
                "department": "SecretAgents",
                "job_title": "SE",
                "country": "US",
                "joining_date": "2023-01-15",
                "base_salary": "80000",
                "currency": "USD",
            },
        )
        assert response.status_code == 422

    def test_create_employee_with_invalid_email_returns_422(self, client):
        """Malformed email should be rejected with 422."""
        response = client.post(
            "/api/employees",
            json={
                "full_name": "Alice",
                "email": "not-an-email",
                "department": "Engineering",
                "job_title": "SE",
                "country": "US",
                "joining_date": "2023-01-15",
                "base_salary": "80000",
                "currency": "USD",
            },
        )
        assert response.status_code == 422


# ---------------------------------------------------------------------------
# GET /api/employees — List
# ---------------------------------------------------------------------------


class TestListEmployeesAPI:
    """Tests for GET /api/employees."""

    def _create_employee(self, client, name, email, country="US", department="Engineering"):
        """Helper to create an employee via the API."""
        return client.post(
            "/api/employees",
            json={
                "full_name": name,
                "email": email,
                "department": department,
                "job_title": "SE",
                "country": country,
                "joining_date": "2023-01-15",
                "base_salary": "80000",
                "currency": "USD",
            },
        )

    def test_list_returns_paginated_response(self, client):
        """List endpoint should return the paginated response shape."""
        self._create_employee(client, "Alice", "a@acme.com")
        self._create_employee(client, "Bob", "b@acme.com")

        response = client.get("/api/employees")
        assert response.status_code == 200

        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert "total_pages" in data
        assert data["total"] == 2

    def test_list_with_pagination_params(self, client):
        """Pagination params should limit results."""
        for i in range(5):
            self._create_employee(client, f"Emp{i}", f"emp{i}@acme.com")

        response = client.get("/api/employees?page=1&page_size=2")
        data = response.json()
        assert len(data["items"]) == 2
        assert data["total"] == 5
        assert data["total_pages"] == 3

    def test_list_filter_by_country(self, client):
        """Country filter should work."""
        self._create_employee(client, "US Emp", "us@acme.com", country="US")
        self._create_employee(client, "UK Emp", "uk@acme.com", country="UK")

        response = client.get("/api/employees?country=UK")
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["country"] == "UK"

    def test_list_search_by_name(self, client):
        """Search should match on name (case-insensitive)."""
        self._create_employee(client, "Alice Johnson", "alice@acme.com")
        self._create_employee(client, "Bob Smith", "bob@acme.com")

        response = client.get("/api/employees?search=alice")
        data = response.json()
        assert data["total"] == 1
        assert "Alice" in data["items"][0]["full_name"]


# ---------------------------------------------------------------------------
# GET /api/employees/{id} — Get
# ---------------------------------------------------------------------------


class TestGetEmployeeAPI:
    """Tests for GET /api/employees/{id}."""

    def test_get_existing_employee(self, client):
        """Should return the employee with current salary info."""
        create_resp = client.post(
            "/api/employees",
            json={
                "full_name": "Alice",
                "email": "alice@acme.com",
                "department": "Engineering",
                "job_title": "SE",
                "country": "US",
                "joining_date": "2023-01-15",
                "base_salary": "85000",
                "currency": "USD",
            },
        )
        emp_id = create_resp.json()["id"]

        response = client.get(f"/api/employees/{emp_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["full_name"] == "Alice"
        assert data["current_salary"] is not None

    def test_get_nonexistent_employee_returns_404(self, client):
        """Non-existent UUID should return 404."""
        import uuid

        response = client.get(f"/api/employees/{uuid.uuid4()}")
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# PUT /api/employees/{id} — Update
# ---------------------------------------------------------------------------


class TestUpdateEmployeeAPI:
    """Tests for PUT /api/employees/{id}."""

    def test_update_employee_fields(self, client):
        """Should update only provided fields."""
        create_resp = client.post(
            "/api/employees",
            json={
                "full_name": "Alice",
                "email": "alice@acme.com",
                "department": "Engineering",
                "job_title": "SE",
                "country": "US",
                "joining_date": "2023-01-15",
                "base_salary": "80000",
                "currency": "USD",
            },
        )
        emp_id = create_resp.json()["id"]

        response = client.put(
            f"/api/employees/{emp_id}",
            json={"department": "Product", "job_title": "PM"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["department"] == "Product"
        assert data["job_title"] == "PM"
        assert data["full_name"] == "Alice"  # unchanged

    def test_update_nonexistent_returns_404(self, client):
        """Updating a non-existent employee should return 404."""
        import uuid

        response = client.put(
            f"/api/employees/{uuid.uuid4()}",
            json={"full_name": "Ghost"},
        )
        assert response.status_code == 404

    def test_update_employee_with_invalid_country_returns_422(self, client):
        """Updating an employee with an invalid country should return 422."""
        create_resp = client.post(
            "/api/employees",
            json={
                "full_name": "Bob",
                "email": "bob_test_val@acme.com",
                "department": "Engineering",
                "job_title": "SE",
                "country": "US",
                "joining_date": "2023-01-15",
                "base_salary": "80000",
                "currency": "USD",
            },
        )
        emp_id = create_resp.json()["id"]

        response = client.put(
            f"/api/employees/{emp_id}",
            json={"country": "InvalidCountryName"},
        )
        assert response.status_code == 422

    def test_update_employee_with_invalid_department_returns_422(self, client):
        """Updating an employee with an invalid department should return 422."""
        create_resp = client.post(
            "/api/employees",
            json={
                "full_name": "Bob",
                "email": "bob_dept_test@acme.com",
                "department": "Engineering",
                "job_title": "SE",
                "country": "US",
                "joining_date": "2023-01-15",
                "base_salary": "80000",
                "currency": "USD",
            },
        )
        emp_id = create_resp.json()["id"]

        response = client.put(
            f"/api/employees/{emp_id}",
            json={"department": "InvalidDepartmentName"},
        )
        assert response.status_code == 422


# ---------------------------------------------------------------------------
# DELETE /api/employees/{id} — Soft Delete
# ---------------------------------------------------------------------------


class TestDeleteEmployeeAPI:
    """Tests for DELETE /api/employees/{id}."""

    def test_soft_delete_returns_inactive_employee(self, client):
        """Soft delete should return the employee with inactive status."""
        create_resp = client.post(
            "/api/employees",
            json={
                "full_name": "Alice",
                "email": "alice@acme.com",
                "department": "Engineering",
                "job_title": "SE",
                "country": "US",
                "joining_date": "2023-01-15",
                "base_salary": "80000",
                "currency": "USD",
            },
        )
        emp_id = create_resp.json()["id"]

        response = client.delete(f"/api/employees/{emp_id}")
        assert response.status_code == 200
        assert response.json()["status"] == "inactive"

    def test_soft_delete_nonexistent_returns_404(self, client):
        """Deleting a non-existent employee should return 404."""
        import uuid

        response = client.delete(f"/api/employees/{uuid.uuid4()}")
        assert response.status_code == 404

    def test_soft_deleted_employee_still_retrievable(self, client):
        """A soft-deleted employee should still be accessible via GET."""
        create_resp = client.post(
            "/api/employees",
            json={
                "full_name": "Alice",
                "email": "alice@acme.com",
                "department": "Engineering",
                "job_title": "SE",
                "country": "US",
                "joining_date": "2023-01-15",
                "base_salary": "80000",
                "currency": "USD",
            },
        )
        emp_id = create_resp.json()["id"]
        client.delete(f"/api/employees/{emp_id}")

        response = client.get(f"/api/employees/{emp_id}")
        assert response.status_code == 200
        assert response.json()["status"] == "inactive"
