from pathlib import Path

from PIL import Image

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


def test_asset_registry_records_image_metadata_and_filters_assets(tmp_path: Path):
    project_dir = tmp_path / "ProjectA"
    ProjectService().create_project(project_dir)
    source_dir = project_dir / "source"
    source_dir.mkdir()
    cover = source_dir / "cover.png"
    detail = source_dir / "detail.png"
    Image.new("RGB", (80, 120), (180, 20, 20)).save(cover)
    Image.new("RGB", (160, 90), (20, 40, 180)).save(detail)
    registry = AssetRegistry(project_dir)

    registry.add_asset(cover, "普通图片", "import")
    registry.add_asset(detail, "汇总图", "export")

    assets = registry.list_assets(source_type="普通图片", query="cov", sort="filename_asc")

    assert len(assets) == 1
    assert assets[0]["filename"] == "cover.png"
    assert assets[0]["width"] == 80
    assert assets[0]["height"] == 120
    assert assets[0]["file_size"] > 0


def test_asset_registry_deletes_record_and_optionally_file(tmp_path: Path):
    project_dir = tmp_path / "ProjectA"
    ProjectService().create_project(project_dir)
    source_dir = project_dir / "source"
    source_dir.mkdir()
    image_path = source_dir / "cover.png"
    Image.new("RGB", (80, 120), (180, 20, 20)).save(image_path)
    registry = AssetRegistry(project_dir)
    asset = registry.add_asset(image_path, "普通图片", "import")

    removed = registry.delete_asset(asset["id"], delete_file=True)

    assert removed["id"] == asset["id"]
    assert registry.list_assets() == []
    assert not image_path.exists()
