from fastapi.testclient import TestClient

from backend.server import create_app


def test_health_endpoint_reports_service_ready():
    client = TestClient(create_app())

    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"ok": True, "service": "xhs-picture-backend"}


def test_settings_api_round_trips_values(tmp_path, monkeypatch):
    from backend.storage import paths

    monkeypatch.setattr(paths, "CONFIG_PATH", tmp_path / "config.json")
    client = TestClient(create_app())

    save_response = client.post("/api/settings", json={"default_canvas_ratio": "9:16"})
    load_response = client.get("/api/settings")

    assert save_response.status_code == 200
    assert save_response.json()["default_canvas_ratio"] == "9:16"
    assert load_response.status_code == 200
    assert load_response.json()["default_canvas_ratio"] == "9:16"
