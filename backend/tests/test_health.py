"""Smoke test to verify the app scaffold and test infrastructure work."""


def test_health_check(client):
    """The health endpoint should return a 200 with status healthy."""
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}
