from pathlib import Path

import fitz
from fastapi.testclient import TestClient

from backend.server import create_app
from backend.services.project_service import ProjectService


def _create_pdf(path: Path, pages: int = 2) -> None:
    doc = fitz.open()
    for index in range(pages):
        page = doc.new_page(width=200, height=120)
        page.insert_text((36, 60), f"Page {index + 1}")
    doc.save(path)
    doc.close()


def test_pdf_export_renders_selected_pages_to_png_assets(tmp_path: Path):
    project_dir = tmp_path / "ProjectA"
    ProjectService().create_project(project_dir)
    pdf_path = tmp_path / "sample.pdf"
    _create_pdf(pdf_path)
    client = TestClient(create_app())

    response = client.post(
        "/api/documents/export",
        json={
            "project_dir": str(project_dir),
            "file_path": str(pdf_path),
            "scale": 2,
            "page_start": 1,
            "page_end": 1,
            "subfolder_output": True,
            "summary_group_size": None,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["task"]["status"] == "completed"
    assert len(body["assets"]) == 1
    output = Path(body["assets"][0]["path"])
    assert output.suffix == ".png"
    assert output.parent == project_dir / "sample"
    assert output.is_file()


def test_pdf_export_outputs_portrait_xiaohongshu_canvas(tmp_path: Path):
    project_dir = tmp_path / "ProjectA"
    ProjectService().create_project(project_dir)
    pdf_path = tmp_path / "wide.pdf"
    _create_pdf(pdf_path, pages=1)
    client = TestClient(create_app())

    response = client.post(
        "/api/documents/export",
        json={
            "project_dir": str(project_dir),
            "file_path": str(pdf_path),
            "scale": 1,
            "summary_group_size": None,
        },
    )

    output = Path(response.json()["assets"][0]["path"])
    image = fitz.open(output)
    try:
        page = image.load_page(0)
        assert round(page.rect.width / page.rect.height, 2) == 0.75
    finally:
        image.close()


def test_pdf_export_groups_pages_into_summary_images(tmp_path: Path):
    project_dir = tmp_path / "ProjectA"
    ProjectService().create_project(project_dir)
    pdf_path = tmp_path / "deck.pdf"
    _create_pdf(pdf_path, pages=12)
    client = TestClient(create_app())

    response = client.post(
        "/api/documents/export",
        json={
            "project_dir": str(project_dir),
            "file_path": str(pdf_path),
            "scale": 1,
            "summary_group_size": 5,
        },
    )

    assets = response.json()["assets"]
    assert [Path(asset["path"]).name for asset in assets] == [
        "deck_汇总_001_001-005.png",
        "deck_汇总_002_006-010.png",
        "deck_汇总_003_011-012.png",
    ]
    assert all(asset["source_type"] == "汇总图" for asset in assets)
