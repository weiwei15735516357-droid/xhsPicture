from pathlib import Path

from fastapi.testclient import TestClient
from PIL import Image

from backend.server import create_app
from backend.services.project_service import ProjectService


def test_import_single_image_copies_to_project_source_and_registers_asset(tmp_path: Path):
    project_dir = tmp_path / "ProjectA"
    ProjectService().create_project(project_dir)
    source_image = tmp_path / "cover.png"
    source_image.write_bytes(b"image")
    client = TestClient(create_app())

    response = client.post(
        "/api/assets/import",
        json={"project_dir": str(project_dir), "paths": [str(source_image)]},
    )

    assert response.status_code == 200
    assets = response.json()["assets"]
    assert len(assets) == 1
    assert Path(assets[0]["path"]).parent == project_dir / "source"
    assert (project_dir / "source" / "cover.png").read_bytes() == b"image"


def test_import_folder_imports_supported_images_only(tmp_path: Path):
    project_dir = tmp_path / "ProjectA"
    ProjectService().create_project(project_dir)
    folder = tmp_path / "images"
    folder.mkdir()
    (folder / "a.jpg").write_bytes(b"a")
    (folder / "b.webp").write_bytes(b"b")
    (folder / "notes.txt").write_text("skip", encoding="utf-8")
    client = TestClient(create_app())

    response = client.post(
        "/api/assets/import",
        json={"project_dir": str(project_dir), "paths": [str(folder)]},
    )
    list_response = client.get("/api/assets", params={"project_dir": str(project_dir)})

    assert response.status_code == 200
    assert [asset["filename"] for asset in response.json()["assets"]] == ["a.jpg", "b.webp"]
    assert list_response.status_code == 200
    assert len(list_response.json()["assets"]) == 2


def test_import_folder_accepts_additional_common_image_extensions(tmp_path: Path):
    project_dir = tmp_path / "ProjectA"
    ProjectService().create_project(project_dir)
    folder = tmp_path / "images"
    folder.mkdir()
    (folder / "a.jfif").write_bytes(b"a")
    (folder / "b.tiff").write_bytes(b"b")
    client = TestClient(create_app())

    response = client.post(
        "/api/assets/import",
        json={"project_dir": str(project_dir), "paths": [str(folder)]},
    )

    assert response.status_code == 200
    assert [asset["filename"] for asset in response.json()["assets"]] == ["a.jfif", "b.tiff"]


def test_assets_api_filters_and_deletes_assets(tmp_path: Path):
    project_dir = tmp_path / "ProjectA"
    ProjectService().create_project(project_dir)
    source_image = tmp_path / "cover.png"
    Image.new("RGB", (80, 120), (180, 20, 20)).save(source_image)
    client = TestClient(create_app())
    imported = client.post(
        "/api/assets/import",
        json={"project_dir": str(project_dir), "paths": [str(source_image)]},
    ).json()["assets"][0]

    list_response = client.get(
        "/api/assets",
        params={"project_dir": str(project_dir), "source_type": "普通图片", "q": "cov", "sort": "filename_asc"},
    )
    delete_response = client.delete(
        f"/api/assets/{imported['id']}",
        params={"project_dir": str(project_dir), "delete_file": "true"},
    )
    after_delete = client.get("/api/assets", params={"project_dir": str(project_dir)})

    assert list_response.status_code == 200
    assert list_response.json()["assets"][0]["width"] == 80
    assert delete_response.status_code == 200
    assert after_delete.json()["assets"] == []
    assert not Path(imported["path"]).exists()
