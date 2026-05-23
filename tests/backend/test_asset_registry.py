import json
from pathlib import Path

from backend.services.asset_registry import AssetRegistry
from backend.services.project_service import ProjectService


def test_asset_registry_adds_image_asset_to_project_json(tmp_path: Path):
    project_dir = tmp_path / "ProjectA"
    ProjectService().create_project(project_dir)
    image_path = project_dir / "source" / "cover.png"
    image_path.write_bytes(b"fake")

    asset = AssetRegistry(project_dir).add_asset(image_path, "普通图片", "import")

    assert asset["id"]
    assert asset["path"] == str(image_path)
    assert asset["source_type"] == "普通图片"
    project = json.loads((project_dir / "project.json").read_text(encoding="utf-8"))
    assert project["assets"][0]["id"] == asset["id"]


def test_asset_registry_lists_assets(tmp_path: Path):
    project_dir = tmp_path / "ProjectA"
    ProjectService().create_project(project_dir)
    image_path = project_dir / "source" / "cover.png"
    image_path.write_bytes(b"fake")
    registry = AssetRegistry(project_dir)
    created = registry.add_asset(image_path, "普通图片", "import")

    assets = registry.list_assets()

    assert assets == [created]
