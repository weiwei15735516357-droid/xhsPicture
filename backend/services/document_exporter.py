from pathlib import Path
from typing import Any
from io import BytesIO

import fitz
from PIL import Image

from backend.services.asset_registry import AssetRegistry
from backend.services.office_converter import POWERPOINT_EXTENSIONS, WORD_EXTENSIONS, OfficeConverter


XHS_WIDTH = 1080
XHS_HEIGHT = 1440
PAGE_BACKGROUND = (248, 250, 252)


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
        background_path: Path | None = None,
        background_has_text: bool = False,
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
                background_path=background_path,
                background_has_text=background_has_text,
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
                background_path=background_path,
                background_has_text=background_has_text,
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
        background_path: Path | None = None,
        background_has_text: bool = False,
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
            assets.extend(
                self._save_summary_groups(
                    registry,
                    output_dir,
                    document_name,
                    rendered_pages,
                    summary_group_size,
                    origin,
                    background_path,
                    background_has_text,
                )
            )
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
        background_path: Path | None,
        background_has_text: bool,
    ) -> list[dict[str, Any]]:
        assets = []
        for group_index, start_index in enumerate(range(0, len(rendered_pages), group_size), start=1):
            group = rendered_pages[start_index : start_index + group_size]
            if not group:
                continue
            first_page = group[0][0]
            last_page = group[-1][0]
            canvas = self._compose_summary(group, background_path=background_path, background_has_text=background_has_text)
            output_path = output_dir / f"{document_name}_汇总_{group_index:03d}_{first_page:03d}-{last_page:03d}.png"
            canvas.save(output_path)
            assets.append(registry.add_asset(output_path, "汇总图", origin))
        return assets

    def _compose_portrait_page(self, image: Image.Image) -> Image.Image:
        canvas = Image.new("RGB", (XHS_WIDTH, XHS_HEIGHT), PAGE_BACKGROUND)
        self._paste_contained(canvas, image, (54, 120, XHS_WIDTH - 54, XHS_HEIGHT - 120))
        return canvas

    def _compose_summary(
        self,
        group: list[tuple[int, Image.Image]],
        background_path: Path | None = None,
        background: Image.Image | None = None,
        background_has_text: bool = False,
    ) -> Image.Image:
        canvas = background.copy() if background else self._create_background(background_path)
        top = XHS_HEIGHT // 6 if background_has_text else 28
        hero_height = 430 if background_has_text else 542
        hero = (28, top, XHS_WIDTH - 28, top + hero_height)
        self._paste_contained(canvas, group[0][1], hero, vertical_align="top")
        remaining = group[1:]
        slots = self._dynamic_slots(count=len(remaining), top=hero[3] + 12, bottom=XHS_HEIGHT - 28)
        for (_, image), slot in zip(remaining, slots):
            self._paste_contained(canvas, image, slot, vertical_align="top")
        return canvas

    def _create_background(self, background_path: Path | None) -> Image.Image:
        if background_path and background_path.exists():
            image = Image.open(background_path).convert("RGB")
            return self._cover_to_canvas(image)
        return Image.new("RGB", (XHS_WIDTH, XHS_HEIGHT), PAGE_BACKGROUND)

    def _cover_to_canvas(self, image: Image.Image) -> Image.Image:
        canvas_ratio = XHS_WIDTH / XHS_HEIGHT
        image_ratio = image.width / image.height
        if image_ratio > canvas_ratio:
            new_height = XHS_HEIGHT
            new_width = int(new_height * image_ratio)
        else:
            new_width = XHS_WIDTH
            new_height = int(new_width / image_ratio)
        resized = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        left = (new_width - XHS_WIDTH) // 2
        top = (new_height - XHS_HEIGHT) // 2
        return resized.crop((left, top, left + XHS_WIDTH, top + XHS_HEIGHT))

    def _dynamic_slots(self, count: int, top: int, bottom: int) -> list[tuple[int, int, int, int]]:
        if count <= 0:
            return []
        gap = 12
        if count == 1:
            height = min(bottom - top, int((XHS_WIDTH - 56) / (16 / 9)))
            return [(28, top, XHS_WIDTH - 28, top + height)]
        if count == 2:
            mid = XHS_WIDTH // 2
            height = min(bottom - top, int((mid - gap // 2 - 28) / (16 / 9)))
            return [(28, top, mid - gap // 2, top + height), (mid + gap // 2, top, XHS_WIDTH - 28, top + height)]
        if count == 3:
            wide_height = min(int((XHS_WIDTH - 56) / (16 / 9)), max(1, (bottom - top - gap) // 2))
            lower_top = top + wide_height + gap
            mid = XHS_WIDTH // 2
            lower_height = min(bottom - lower_top, int((mid - gap // 2 - 28) / (16 / 9)))
            return [
                (28, top, XHS_WIDTH - 28, top + wide_height),
                (28, lower_top, mid - gap // 2, lower_top + lower_height),
                (mid + gap // 2, lower_top, XHS_WIDTH - 28, lower_top + lower_height),
            ]
        return self._grid_slots(remaining_count=count, top=top, bottom=bottom, columns=2 if count <= 6 else 3)

    def _grid_slots(self, remaining_count: int, top: int, bottom: int, columns: int) -> list[tuple[int, int, int, int]]:
        if remaining_count <= 0:
            return []
        gap = 12
        rows = (remaining_count + columns - 1) // columns
        left = 28
        right = XHS_WIDTH - 28
        width = (right - left - gap * (columns - 1)) // columns
        max_height = (bottom - top - gap * (rows - 1)) // rows
        height = min(max_height, int(width / (16 / 9)))
        slots = []
        for index in range(remaining_count):
            row = index // columns
            column = index % columns
            x1 = left + column * (width + gap)
            y1 = top + row * (height + gap)
            slots.append((x1, y1, x1 + width, y1 + height))
        return slots

    def _inset(self, box: tuple[int, int, int, int], value: int) -> tuple[int, int, int, int]:
        return (box[0] + value, box[1] + value, box[2] - value, box[3] - value)

    def _paste_contained(
        self,
        canvas: Image.Image,
        image: Image.Image,
        box: tuple[int, int, int, int],
        vertical_align: str = "center",
    ) -> None:
        max_width = box[2] - box[0]
        max_height = box[3] - box[1]
        image_copy = image.copy()
        image_copy.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
        x = box[0] + (max_width - image_copy.width) // 2
        y = box[1] if vertical_align == "top" else box[1] + (max_height - image_copy.height) // 2
        canvas.paste(image_copy, (x, y))

    def _paste_covered(self, canvas: Image.Image, image: Image.Image, box: tuple[int, int, int, int]) -> None:
        target_width = box[2] - box[0]
        target_height = box[3] - box[1]
        image_ratio = image.width / image.height
        target_ratio = target_width / target_height
        if image_ratio > target_ratio:
            new_height = target_height
            new_width = int(new_height * image_ratio)
        else:
            new_width = target_width
            new_height = int(new_width / image_ratio)
        resized = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        left = (new_width - target_width) // 2
        top = (new_height - target_height) // 2
        cropped = resized.crop((left, top, left + target_width, top + target_height))
        canvas.paste(cropped, (box[0], box[1]))
