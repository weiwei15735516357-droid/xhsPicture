from pathlib import Path
from typing import Any
from io import BytesIO

import fitz
from PIL import Image, ImageDraw

from backend.services.asset_registry import AssetRegistry
from backend.services.office_converter import POWERPOINT_EXTENSIONS, WORD_EXTENSIONS, OfficeConverter


XHS_WIDTH = 1080
XHS_HEIGHT = 1440
PAGE_BACKGROUND = (248, 250, 252)
CARD_BACKGROUND = (255, 255, 255)


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
        summary_group_size: int | None = 5,
    ) -> dict[str, Any]:
        suffix = file_path.suffix.lower()
        if suffix == ".pdf":
            return self.export_pdf(
                project_dir,
                file_path,
                scale,
                page_start,
                page_end,
                subfolder_output,
                summary_group_size=summary_group_size,
            )
        if suffix in WORD_EXTENSIONS or suffix in POWERPOINT_EXTENSIONS:
            converted_pdf = self.office_converter.convert_to_pdf(file_path, project_dir / "pages" / "_office_pdf")
            return self.export_pdf(
                project_dir,
                converted_pdf,
                scale,
                page_start,
                page_end,
                subfolder_output,
                output_name=file_path.stem,
                origin_path=file_path,
                summary_group_size=summary_group_size,
            )
        raise ValueError(f"不支持的文档格式：{suffix}")

    def export_pdf(
        self,
        project_dir: Path,
        file_path: Path,
        scale: int,
        page_start: int | None,
        page_end: int | None,
        subfolder_output: bool,
        output_name: str | None = None,
        origin_path: Path | None = None,
        summary_group_size: int | None = None,
    ) -> dict[str, Any]:
        document_name = output_name or file_path.stem
        output_dir = project_dir / document_name if subfolder_output else project_dir
        output_dir.mkdir(parents=True, exist_ok=True)
        registry = AssetRegistry(project_dir)
        assets = []
        rendered_pages: list[tuple[int, Image.Image]] = []

        doc = fitz.open(file_path)
        try:
            start = max((page_start or 1), 1)
            end = min((page_end or doc.page_count), doc.page_count)
            matrix = fitz.Matrix(scale, scale)
            for page_number in range(start, end + 1):
                page = doc.load_page(page_number - 1)
                pixmap = page.get_pixmap(matrix=matrix, alpha=False)
                page_image = Image.open(BytesIO(pixmap.tobytes("png"))).convert("RGB")
                rendered_pages.append((page_number, page_image))
        finally:
            doc.close()

        origin = str(origin_path or file_path)
        if summary_group_size:
            assets.extend(self._save_summary_groups(registry, output_dir, document_name, rendered_pages, summary_group_size, origin))
        else:
            for page_number, page_image in rendered_pages:
                output_path = output_dir / f"{document_name}_p{page_number:03d}.png"
                self._compose_portrait_page(page_image).save(output_path)
                assets.append(registry.add_asset(output_path, "文档页", origin))

        return {"assets": assets}

    def _save_summary_groups(
        self,
        registry: AssetRegistry,
        output_dir: Path,
        document_name: str,
        rendered_pages: list[tuple[int, Image.Image]],
        group_size: int,
        origin: str,
    ) -> list[dict[str, Any]]:
        assets = []
        for group_index, start_index in enumerate(range(0, len(rendered_pages), group_size), start=1):
            group = rendered_pages[start_index : start_index + group_size]
            if not group:
                continue
            first_page = group[0][0]
            last_page = group[-1][0]
            canvas = self._compose_summary(group, is_first_group=group_index == 1)
            output_path = output_dir / f"{document_name}_汇总_{group_index:03d}_{first_page:03d}-{last_page:03d}.png"
            canvas.save(output_path)
            assets.append(registry.add_asset(output_path, "汇总图", origin))
        return assets

    def _compose_portrait_page(self, image: Image.Image) -> Image.Image:
        canvas = Image.new("RGB", (XHS_WIDTH, XHS_HEIGHT), PAGE_BACKGROUND)
        self._paste_contained(canvas, image, (54, 120, XHS_WIDTH - 54, XHS_HEIGHT - 120))
        return canvas

    def _compose_summary(self, group: list[tuple[int, Image.Image]], is_first_group: bool) -> Image.Image:
        canvas = Image.new("RGB", (XHS_WIDTH, XHS_HEIGHT), PAGE_BACKGROUND)
        draw = ImageDraw.Draw(canvas)
        if is_first_group:
            hero = (48, 48, XHS_WIDTH - 48, 560)
            self._draw_card(draw, hero)
            self._paste_contained(canvas, group[0][1], self._inset(hero, 12))
            remaining = group[1:]
            slots = self._grid_slots(remaining_count=len(remaining), top=600, bottom=XHS_HEIGHT - 70, columns=2)
            for (_, image), slot in zip(remaining, slots):
                self._draw_card(draw, slot)
                self._paste_contained(canvas, image, self._inset(slot, 10))
        else:
            columns = 2 if len(group) <= 6 else 3
            slots = self._grid_slots(remaining_count=len(group), top=54, bottom=XHS_HEIGHT - 54, columns=columns)
            for (_, image), slot in zip(group, slots):
                self._draw_card(draw, slot)
                self._paste_contained(canvas, image, self._inset(slot, 10))
        return canvas

    def _grid_slots(self, remaining_count: int, top: int, bottom: int, columns: int) -> list[tuple[int, int, int, int]]:
        if remaining_count <= 0:
            return []
        gap = 18
        rows = (remaining_count + columns - 1) // columns
        left = 48
        right = XHS_WIDTH - 48
        width = (right - left - gap * (columns - 1)) // columns
        height = (bottom - top - gap * (rows - 1)) // rows
        slots = []
        for index in range(remaining_count):
            row = index // columns
            column = index % columns
            x1 = left + column * (width + gap)
            y1 = top + row * (height + gap)
            slots.append((x1, y1, x1 + width, y1 + height))
        return slots

    def _draw_card(self, draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int]) -> None:
        draw.rounded_rectangle(box, radius=16, fill=CARD_BACKGROUND, outline=(210, 218, 228), width=2)

    def _inset(self, box: tuple[int, int, int, int], value: int) -> tuple[int, int, int, int]:
        return (box[0] + value, box[1] + value, box[2] - value, box[3] - value)

    def _paste_contained(self, canvas: Image.Image, image: Image.Image, box: tuple[int, int, int, int]) -> None:
        max_width = box[2] - box[0]
        max_height = box[3] - box[1]
        image_copy = image.copy()
        image_copy.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
        x = box[0] + (max_width - image_copy.width) // 2
        y = box[1] + (max_height - image_copy.height) // 2
        canvas.paste(image_copy, (x, y))
