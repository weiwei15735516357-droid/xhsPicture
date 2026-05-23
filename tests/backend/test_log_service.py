import json
from pathlib import Path

from fastapi.testclient import TestClient

from backend.server import create_app
from backend.services.log_service import LogService


def test_log_service_appends_json_lines(tmp_path: Path):
    log_path = tmp_path / "app.log"
    service = LogService(log_path)

    first = service.append("info", "created project", {"project": "A"})
    second = service.append("error", "failed task", {"task_id": "t1"})

    lines = log_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    assert json.loads(lines[0])["message"] == "created project"
    assert json.loads(lines[1])["level"] == "error"
    assert first["id"] != second["id"]


def test_log_service_reads_latest_entries_first(tmp_path: Path):
    log_path = tmp_path / "app.log"
    service = LogService(log_path)
    service.append("info", "one", {})
    service.append("info", "two", {})

    entries = service.list_entries(limit=1)

    assert len(entries) == 1
    assert entries[0]["message"] == "two"


def test_logs_api_returns_entries(tmp_path: Path, monkeypatch):
    from backend.storage import paths

    monkeypatch.setattr(paths, "LOG_DIR", tmp_path)
    client = TestClient(create_app())

    post_response = client.post("/api/logs", json={"level": "info", "message": "hello", "context": {"a": 1}})
    get_response = client.get("/api/logs")

    assert post_response.status_code == 200
    assert get_response.status_code == 200
    assert get_response.json()[0]["message"] == "hello"
