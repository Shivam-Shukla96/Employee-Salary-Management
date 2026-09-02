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

    def test_create_employee_with_empty_country_returns_422(self, client):
        """Empty or whitespace-only country name should be rejected with 422."""
        response = client.post(
            "/api/employees",
            json={
                "full_name": "Alice",
                "email": "alice_empty_country@acme.com",
                "department": "Engineering",
                "job_title": "SE",
                "country": "   ",
                "joining_date": "2023-01-15",
                "base_salary": "80000",
                "currency": "USD",
            },
        )
        assert response.status_code == 422

    def test_create_employee_with_empty_department_returns_422(self, client):
        """Empty or whitespace-only department name should be rejected with 422."""
        response = client.post(
            "/api/employees",
            json={
                "full_name": "Alice",
                "email": "alice_empty_dept@acme.com",
                "department": "   ",
                "job_title": "SE",
                "country": "US",
                "joining_date": "2023-01-15",
                "base_salary": "80000",
                "currency": "USD",
            },
        )
        assert response.status_code == 422

    def test_create_employee_with_new_custom_country_and_department(self, client):
        """A new employee from a new country and new department should be accepted."""
        response = client.post(
            "/api/employees",
            json={
                "full_name": "Claire Dupont",
                "email": "claire@acme.com",
                "department": "AI Research",
                "job_title": "Research Scientist",
                "country": "France",
                "joining_date": "2024-01-15",
                "base_salary": "75000",
                "currency": "EUR",
            },
        )
        assert response.status_code == 201
        assert response.json()["country"] == "France"
        assert response.json()["department"] == "AI Research"

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

    def test_update_employee_with_empty_country_returns_422(self, client):
        """Updating an employee with an empty country should return 422."""
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
            json={"country": "  "},
        )
        assert response.status_code == 422

    def test_update_employee_with_new_country_and_department(self, client):
        """Updating an employee with a new country and department should succeed."""
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
            json={"department": "Robotics", "country": "Japan"},
        )
        assert response.status_code == 200
        assert response.json()["department"] == "Robotics"
        assert response.json()["country"] == "Japan"

    def test_update_employee_with_no_changes_returns_409(self, client):
        """Submitting an update with identical values should return 409 Conflict."""
        create_resp = client.post(
            "/api/employees",
            json={
                "full_name": "Bob",
                "email": "bob_noop@acme.com",
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
            json={"full_name": "Bob", "department": "Engineering"},
        )
        assert response.status_code == 409
        assert "No changes detected" in response.json()["detail"]

    def test_update_employee_duplicate_email_returns_409(self, client):
        """Updating to an email already in use should return 409 Conflict."""
        client.post(
            "/api/employees",
            json={
                "full_name": "User One",
                "email": "user1_dup@acme.com",
                "department": "Engineering",
                "job_title": "SE",
                "country": "US",
                "joining_date": "2023-01-15",
                "base_salary": "80000",
                "currency": "USD",
            },
        )
        resp2 = client.post(
            "/api/employees",
            json={
                "full_name": "User Two",
                "email": "user2_dup@acme.com",
                "department": "Sales",
                "job_title": "SR",
                "country": "UK",
                "joining_date": "2023-01-15",
                "base_salary": "60000",
                "currency": "GBP",
            },
        )
        emp2_id = resp2.json()["id"]

        response = client.put(
            f"/api/employees/{emp2_id}",
            json={"email": "user1_dup@acme.com"},
        )
        assert response.status_code == 409
        assert "already exists" in response.json()["detail"].lower()

    def test_update_inactive_employee_returns_409(self, client):
        """Updating details of a deactivated employee should return 409 Conflict."""
        create_resp = client.post(
            "/api/employees",
            json={
                "full_name": "Bob Inactive",
                "email": "bob_inactive_upd@acme.com",
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

        response = client.put(
            f"/api/employees/{emp_id}",
            json={"department": "Sales"},
        )
        assert response.status_code == 409
        assert "inactive" in response.json()["detail"].lower()


# ---------------------------------------------------------------------------
# DELETE /api/employees/{id} — Soft Delete & Reactivate
# ---------------------------------------------------------------------------


class TestDeleteEmployeeAPI:
    """Tests for DELETE /api/employees/{id} and POST /api/employees/{id}/reactivate."""

    def test_soft_delete_returns_inactive_employee(self, client):
        """Soft delete should return the employee with inactive status."""
        create_resp = client.post(
            "/api/employees",
            json={
                "full_name": "Alice",
                "email": "alice_del@acme.com",
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

    def test_deactivate_already_inactive_employee_returns_409(self, client):
        """Deactivating an already inactive employee should return 409 Conflict."""
        create_resp = client.post(
            "/api/employees",
            json={
                "full_name": "Alice",
                "email": "alice_double_del@acme.com",
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

        response = client.delete(f"/api/employees/{emp_id}")
        assert response.status_code == 409
        assert "already inactive" in response.json()["detail"].lower()

    def test_reactivate_already_active_employee_returns_409(self, client):
        """Reactivating an already active employee should return 409 Conflict."""
        create_resp = client.post(
            "/api/employees",
            json={
                "full_name": "Alice",
                "email": "alice_already_act@acme.com",
                "department": "Engineering",
                "job_title": "SE",
                "country": "US",
                "joining_date": "2023-01-15",
                "base_salary": "80000",
                "currency": "USD",
            },
        )
        emp_id = create_resp.json()["id"]

        response = client.post(f"/api/employees/{emp_id}/reactivate")
        assert response.status_code == 409
        assert "already active" in response.json()["detail"].lower()

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
                "email": "alice_get_del@acme.com",
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
