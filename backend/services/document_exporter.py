from pathlib import Path
from typing import Any

import fitz

from backend.services.asset_registry import AssetRegistry


class DocumentExporter:
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
