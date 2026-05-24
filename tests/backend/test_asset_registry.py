from pathlib import Path

from backend.services.asset_registry import AssetRegistry
from backend.services.project_service import ProjectService


def test_asset_registry_adds_image_asset_to_project_json(tmp_path: Path):
    project_dir = tmp_path / "ProjectA"
    ProjectService().create_project(project_dir)
    image_path = project_dir / "source" / "cover.png"
    image_path.parent.mkdir()
    image_path.write_bytes(b"fake")

    asset = AssetRegistry(project_dir).add_asset(image_path, "普通图片", "import")

    assert asset["id"]
    assert asset["path"] == str(image_path)
    assert asset["source_type"] == "普通图片"
    project = AssetRegistry(project_dir)._load_project()
    assert project["assets"][0]["id"] == asset["id"]


def test_asset_registry_lists_assets(tmp_path: Path):
    project_dir = tmp_path / "ProjectA"
    ProjectService().create_project(project_dir)
    image_path = project_dir / "source" / "cover.png"
    image_path.parent.mkdir()
    image_path.write_bytes(b"fake")
    registry = AssetRegistry(project_dir)
    created = registry.add_asset(image_path, "普通图片", "import")

    assets = registry.list_assets()

    assert assets == [created]


def test_asset_registry_recreates_missing_internal_project_file(tmp_path: Path):
    project_dir = tmp_path / "ProjectA"
    project_dir.mkdir()
    image_path = project_dir / "cover.png"
    image_path.write_bytes(b"fake")

    asset = AssetRegistry(project_dir).add_asset(image_path, "普通图片", "import")

    assert asset["id"]
    assert AssetRegistry(project_dir).list_assets()[0]["id"] == asset["id"]
