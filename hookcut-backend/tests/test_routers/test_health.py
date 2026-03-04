"""Tests for health check and basic app endpoints."""


class TestHealth:
    def test_health_endpoint(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert "version" in data

    def test_nonexistent_route(self, client):
        resp = client.get("/api/nonexistent")
        assert resp.status_code in (404, 405)
