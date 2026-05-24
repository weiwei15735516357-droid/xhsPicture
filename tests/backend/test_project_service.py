from pathlib import Path

from fastapi.testclient import TestClient

from backend.services.asset_registry import AssetRegistry
from backend.server import create_app
from backend.services.project_service import ProjectService


def test_create_project_leaves_output_directory_empty(tmp_path: Path):
    service = ProjectService()
    project_dir = tmp_path / "MayCampaign"

    result = service.create_project(project_dir)

    assert result["project_dir"] == str(project_dir)
    assert list(project_dir.iterdir()) == []


def test_create_project_initializes_project_json(tmp_path: Path):
    service = ProjectService()
    project_dir = tmp_path / "MayCampaign"

    service.create_project(project_dir)
    data = AssetRegistry(project_dir)._load_project()

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
    assert list(project_dir.iterdir()) == []
