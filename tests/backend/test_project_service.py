import json
from pathlib import Path

from fastapi.testclient import TestClient

from backend.server import create_app
from backend.services.project_service import ProjectService


def test_create_project_builds_required_directory_tree(tmp_path: Path):
    service = ProjectService()
    project_dir = tmp_path / "MayCampaign"

    result = service.create_project(project_dir)

    assert result["project_dir"] == str(project_dir)
    for name in ["source", "pages", "compositions", "collages", "exports", "logs", "templates"]:
        assert (project_dir / name).is_dir()
    assert (project_dir / "project.json").is_file()


def test_create_project_initializes_project_json(tmp_path: Path):
    service = ProjectService()
    project_dir = tmp_path / "MayCampaign"

    service.create_project(project_dir)
    data = json.loads((project_dir / "project.json").read_text(encoding="utf-8"))

    assert data["name"] == "MayCampaign"
    assert data["assets"] == []
    assert data["tasks"] == []
    assert data["templates"] == []


def test_create_project_api_returns_created_project(tmp_path: Path):
    client = TestClient(create_app())
    project_dir = tmp_path / "ApiProject"

    response = client.post("/api/project/create", json={"project_dir": str(project_dir)})

    assert response.status_code == 200
    assert response.json()["project_dir"] == str(project_dir)
    assert (project_dir / "project.json").is_file()
