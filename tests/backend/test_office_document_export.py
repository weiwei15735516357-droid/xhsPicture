from pathlib import Path

import fitz
import pytest

from backend.services.document_exporter import DocumentExporter
from backend.services.project_service import ProjectService


class FakeOfficeConverter:
    def __init__(self, pdf_path: Path):
        self.pdf_path = pdf_path
        self.converted = []

    def convert_to_pdf(self, file_path: Path, output_dir: Path) -> Path:
        self.converted.append((file_path, output_dir))
        return self.pdf_path


def _create_pdf(path: Path) -> None:
    doc = fitz.open()
    page = doc.new_page(width=120, height=120)
    page.insert_text((20, 60), "Office")
    doc.save(path)
    doc.close()


def _create_project(project_dir: Path) -> None:
    ProjectService().create_project(project_dir)


def test_docx_export_uses_office_converter_then_renders_pdf(tmp_path: Path):
    project_dir = tmp_path / "ProjectA"
    _create_project(project_dir)
    source_docx = tmp_path / "note.docx"
    source_docx.write_bytes(b"docx placeholder")
    converted_pdf = tmp_path / "converted.pdf"
    _create_pdf(converted_pdf)
    converter = FakeOfficeConverter(converted_pdf)

    result = DocumentExporter(office_converter=converter).export(
        project_dir=project_dir,
        file_path=source_docx,
        scale=1,
        page_start=None,
        page_end=None,
        subfolder_output=True,
    )

    assert converter.converted[0][0] == source_docx
    assert converter.converted[0][1] != project_dir / "pages" / "_office_pdf"
    assert not (project_dir / "pages").exists()
    assert len(result["assets"]) == 1
    assert Path(result["assets"][0]["path"]).suffix == ".png"


def test_unsupported_document_extension_fails_clearly(tmp_path: Path):
    project_dir = tmp_path / "ProjectA"
    _create_project(project_dir)

    with pytest.raises(ValueError, match="不支持的文档格式"):
        DocumentExporter().export(
            project_dir=project_dir,
            file_path=tmp_path / "notes.txt",
            scale=1,
            page_start=None,
            page_end=None,
            subfolder_output=True,
        )
