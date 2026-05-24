from pathlib import Path

import fitz
from PIL import Image
from fastapi.testclient import TestClient

from backend.server import create_app
from backend.services.asset_registry import AssetRegistry
from backend.services.document_exporter import DocumentExporter
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


def test_pdf_export_groups_all_pages_not_only_first_summary(tmp_path: Path):
    project_dir = tmp_path / "ProjectA"
    ProjectService().create_project(project_dir)
    pdf_path = tmp_path / "long-deck.pdf"
    _create_pdf(pdf_path, pages=22)
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
        "long-deck_汇总_001_001-005.png",
        "long-deck_汇总_002_006-010.png",
        "long-deck_汇总_003_011-015.png",
        "long-deck_汇总_004_016-020.png",
        "long-deck_汇总_005_021-022.png",
    ]


def test_summary_uses_custom_layout_slots():
    exporter = DocumentExporter()
    red = Image.new("RGB", (1600, 900), (180, 20, 20))
    blue = Image.new("RGB", (1600, 900), (20, 40, 180))
    layout = [
        {"x": 0.0, "y": 0.0, "width": 1.0, "height": 0.5},
        {"x": 0.0, "y": 0.5, "width": 0.5, "height": 0.5},
    ]

    image = exporter._compose_summary([(1, red), (2, blue)], custom_layout=layout).convert("RGB")

    assert image.getpixel((540, 120)) == (180, 20, 20)
    assert image.getpixel((120, 1000)) == (20, 40, 180)


def test_followup_summary_groups_use_followup_layout(tmp_path: Path):
    project_dir = tmp_path / "ProjectA"
    ProjectService().create_project(project_dir)
    rendered_pages = [
        (index, Image.new("RGB", (1600, 900), (180 if index <= 5 else 20, 20, 180)))
        for index in range(1, 11)
    ]

    output_dir = project_dir / "deck"
    output_dir.mkdir()
    assets = DocumentExporter()._save_summary_groups(
        registry=AssetRegistry(project_dir),
        output_dir=output_dir,
        document_name="deck",
        rendered_pages=rendered_pages,
        group_size=5,
        origin="test",
        background_path=None,
        custom_layout=[{"x": 0, "y": 0, "width": 1, "height": 0.5}] * 5,
        followup_layout=[{"x": 0, "y": 0.5, "width": 1, "height": 0.5}] * 5,
    )

    first = Image.open(assets[0]["path"]).convert("RGB")
    second = Image.open(assets[1]["path"]).convert("RGB")
    assert first.getpixel((540, 120)) == (180, 20, 180)
    assert first.getpixel((540, 1200)) == (248, 250, 252)
    assert second.getpixel((540, 120)) == (248, 250, 252)
    assert second.getpixel((540, 1200)) == (20, 20, 180)


def test_custom_first_and_followup_layouts_can_use_different_group_sizes(tmp_path: Path):
    project_dir = tmp_path / "ProjectA"
    ProjectService().create_project(project_dir)
    rendered_pages = [(index, Image.new("RGB", (1600, 900), (20, 40, 180))) for index in range(1, 9)]

    output_dir = project_dir / "deck"
    output_dir.mkdir()
    assets = DocumentExporter()._save_summary_groups(
        registry=AssetRegistry(project_dir),
        output_dir=output_dir,
        document_name="deck",
        rendered_pages=rendered_pages,
        group_size=5,
        origin="test",
        background_path=None,
        custom_layout=[
            {"x": 0, "y": 0, "width": 1, "height": 0.3},
            {"x": 0, "y": 0.3, "width": 1, "height": 0.3},
            {"x": 0, "y": 0.6, "width": 1, "height": 0.3},
        ],
        followup_layout=[
            {"x": 0, "y": 0, "width": 1, "height": 0.5},
            {"x": 0, "y": 0.5, "width": 1, "height": 0.5},
        ],
    )

    assert [Path(asset["path"]).name for asset in assets] == [
        "deck_汇总_001_001-003.png",
        "deck_汇总_002_004-005.png",
        "deck_汇总_003_006-007.png",
        "deck_汇总_004_008-008.png",
    ]


def test_document_export_root_contains_only_document_output_folder(tmp_path: Path):
    project_dir = tmp_path / "ProjectA"
    ProjectService().create_project(project_dir)
    pdf_path = tmp_path / "deck.pdf"
    _create_pdf(pdf_path, pages=3)
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

    assert response.status_code == 200
    assert sorted(child.name for child in project_dir.iterdir()) == ["deck"]


def test_summary_uses_uploaded_background_image(tmp_path: Path):
    project_dir = tmp_path / "ProjectA"
    ProjectService().create_project(project_dir)
    pdf_path = tmp_path / "deck.pdf"
    background_path = tmp_path / "background.png"
    _create_pdf(pdf_path, pages=5)
    Image.new("RGB", (80, 80), (20, 80, 160)).save(background_path)
    client = TestClient(create_app())

    response = client.post(
        "/api/documents/export",
        json={
            "project_dir": str(project_dir),
            "file_path": str(pdf_path),
            "scale": 1,
            "summary_group_size": 5,
            "background_path": str(background_path),
        },
    )

    output = Path(response.json()["assets"][0]["path"])
    image = Image.open(output).convert("RGB")
    assert image.getpixel((8, 8)) == (20, 80, 160)


def test_later_summary_groups_use_hero_layout_and_fill_canvas(tmp_path: Path):
    project_dir = tmp_path / "ProjectA"
    ProjectService().create_project(project_dir)
    pdf_path = tmp_path / "deck.pdf"
    _create_pdf(pdf_path, pages=8)
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

    second_output = Path(response.json()["assets"][1]["path"])
    image = Image.open(second_output).convert("RGB")
    assert image.size == (1080, 1440)
    assert image.getpixel((540, 80)) != (248, 250, 252)


def test_summary_slots_crop_to_fill_without_white_card_padding():
    exporter = DocumentExporter()
    red = Image.new("RGB", (1600, 900), (180, 20, 20))
    blue = Image.new("RGB", (1600, 900), (20, 40, 180))
    green = Image.new("RGB", (1600, 900), (20, 140, 70))

    image = exporter._compose_summary([(1, red), (2, blue), (3, green)]).convert("RGB")

    assert image.getpixel((540, 36)) == (180, 20, 20)
    assert image.getpixel((36, 1130)) == (20, 40, 180)
    assert image.getpixel((560, 1130)) == (20, 140, 70)


def test_summary_thumbnails_preserve_edges_and_reach_bottom():
    exporter = DocumentExporter()
    hero = Image.new("RGB", (1600, 900), (180, 20, 20))
    thumbnail = Image.new("RGB", (1600, 900), (20, 40, 180))
    for x in range(0, 120):
        for y in range(900):
            thumbnail.putpixel((x, y), (250, 210, 40))

    image = exporter._compose_summary([(1, hero), (2, thumbnail), (3, thumbnail), (4, thumbnail), (5, thumbnail)]).convert("RGB")

    assert image.getpixel((32, 840)) == (250, 210, 40)
    assert image.getpixel((700, 1410)) == (20, 40, 180)


def test_summary_hero_is_larger_and_lower_grid_reaches_bottom():
    exporter = DocumentExporter()
    slides = [(index, Image.new("RGB", (1600, 900), (20 * index, 30, 40))) for index in range(1, 6)]

    image = exporter._compose_summary(slides).convert("RGB")

    assert image.getpixel((540, 610)) == (20, 30, 40)
    assert image.getpixel((550, 1410)) != (248, 250, 252)
