from fastapi.testclient import TestClient


def test_healthz(test_client: TestClient):
    """Test the health check endpoint."""
    response = test_client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"ok": True}
