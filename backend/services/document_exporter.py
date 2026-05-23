from pathlib import Path
from typing import Any

import fitz

from backend.services.asset_registry import AssetRegistry
from backend.services.office_converter import POWERPOINT_EXTENSIONS, WORD_EXTENSIONS, OfficeConverter


class DocumentExporter:
    def __init__(self, office_converter: OfficeConverter | None = None):
        self.office_converter = office_converter or OfficeConverter()

    def export(
        self,
        project_dir: Path,
        file_path: Path,
        scale: int,
        page_start: int | None,
        page_end: int | None,
        subfolder_output: bool,
    ) -> dict[str, Any]:
        suffix = file_path.suffix.lower()
        if suffix == ".pdf":
            return self.export_pdf(project_dir, file_path, scale, page_start, page_end, subfolder_output)
        if suffix in WORD_EXTENSIONS or suffix in POWERPOINT_EXTENSIONS:
            converted_pdf = self.office_converter.convert_to_pdf(file_path, project_dir / "pages" / "_office_pdf")
            return self.export_pdf(project_dir, converted_pdf, scale, page_start, page_end, subfolder_output)
        raise ValueError(f"不支持的文档格式：{suffix}")

    def export_pdf(
        self,
        project_dir: Path,
        file_path: Path,
        scale: int,
        page_start: int | None,
        page_end: int | None,
        subfolder_output: bool,
    ) -> dict[str, Any]:
        output_root = project_dir / "pages"
        output_dir = output_root / file_path.stem if subfolder_output else output_root
        output_dir.mkdir(parents=True, exist_ok=True)
        registry = AssetRegistry(project_dir)
        assets = []

        doc = fitz.open(file_path)
        try:
            start = max((page_start or 1), 1)
            end = min((page_end or doc.page_count), doc.page_count)
            matrix = fitz.Matrix(scale, scale)
            for page_number in range(start, end + 1):
                page = doc.load_page(page_number - 1)
                pixmap = page.get_pixmap(matrix=matrix, alpha=False)
                output_path = output_dir / f"{file_path.stem}_p{page_number:03d}.png"
                pixmap.save(output_path)
                assets.append(registry.add_asset(output_path, "文档页", str(file_path)))
        finally:
            doc.close()

        return {"assets": assets}
