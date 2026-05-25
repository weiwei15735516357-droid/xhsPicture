from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from PIL import Image, ImageDraw, ImageFilter

from backend.services.asset_registry import AssetRegistry


XHS_WIDTH = 1080
XHS_HEIGHT = 1440


class PerspectiveComposer:
    def compose_batch(
        self,
        project_dir: Path,
        scene_path: Path,
        overlay_paths: list[Path],
        points: list[dict[str, float]],
        opacity: float = 1.0,
        shadow: bool = True,
        progress_callback: Callable[[int, int, str], None] | None = None,
    ) -> dict[str, Any]:
        if len(points) != 4:
            raise ValueError("透视合成需要 4 个角点")
        if not overlay_paths:
            raise ValueError("请至少选择一张叠图")
        output_dir = project_dir / "compositions" / datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir.mkdir(parents=True, exist_ok=True)
        registry = AssetRegistry(project_dir)
        scene = self._cover_to_canvas(Image.open(scene_path).convert("RGB"))
        quad = self._normalized_quad(points)
        assets = []
        total = len(overlay_paths)
        for index, overlay_path in enumerate(overlay_paths, start=1):
            overlay = Image.open(overlay_path).convert("RGBA")
            composed = self._compose_one(scene, overlay, quad, opacity=opacity, shadow=shadow)
            output_path = output_dir / f"{overlay_path.stem}_透视合成_{index:03d}.png"
            composed.save(output_path)
            assets.append(registry.add_asset(output_path, "透视合成图", str(overlay_path)))
            if progress_callback:
                progress_callback(index, total, f"正在生成透视合成 {index}/{total}")
        return {"assets": assets}

    def _compose_one(
        self,
        scene: Image.Image,
        overlay: Image.Image,
        quad: list[tuple[int, int]],
        opacity: float,
        shadow: bool,
    ) -> Image.Image:
        canvas = scene.convert("RGBA")
        if shadow:
            shadow_layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
            shadow_draw = ImageDraw.Draw(shadow_layer)
            shadow_draw.polygon([(x + 10, y + 14) for x, y in quad], fill=(0, 0, 0, 72))
            canvas.alpha_composite(shadow_layer.filter(ImageFilter.GaussianBlur(14)))
        warped = self._warp_overlay(overlay, quad)
        if opacity < 1:
            alpha = warped.getchannel("A").point(lambda value: int(value * opacity))
            warped.putalpha(alpha)
        canvas.alpha_composite(warped)
        return canvas.convert("RGB")

    def _warp_overlay(self, overlay: Image.Image, quad: list[tuple[int, int]]) -> Image.Image:
        coeffs = self._perspective_coefficients(
            quad,
            [(0, 0), (overlay.width, 0), (overlay.width, overlay.height), (0, overlay.height)],
        )
        return overlay.transform(
            (XHS_WIDTH, XHS_HEIGHT),
            Image.Transform.PERSPECTIVE,
            coeffs,
            Image.Resampling.BICUBIC,
        )

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

    def _normalized_quad(self, points: list[dict[str, float]]) -> list[tuple[int, int]]:
        quad = []
        for point in points:
            x = max(0, min(1, float(point["x"])))
            y = max(0, min(1, float(point["y"])))
            quad.append((int(x * XHS_WIDTH), int(y * XHS_HEIGHT)))
        return quad

    def _perspective_coefficients(
        self,
        source: list[tuple[int, int]],
        target: list[tuple[int, int]],
    ) -> tuple[float, float, float, float, float, float, float, float]:
        matrix = []
        vector = []
        for (x, y), (u, v) in zip(source, target):
            matrix.append([x, y, 1, 0, 0, 0, -u * x, -u * y])
            vector.append(u)
            matrix.append([0, 0, 0, x, y, 1, -v * x, -v * y])
            vector.append(v)
        return tuple(self._solve_linear_system(matrix, vector))

    def _solve_linear_system(self, matrix: list[list[float]], vector: list[float]) -> list[float]:
        rows = [row[:] + [value] for row, value in zip(matrix, vector)]
        size = len(vector)
        for pivot_index in range(size):
            pivot_row = max(range(pivot_index, size), key=lambda row: abs(rows[row][pivot_index]))
            if abs(rows[pivot_row][pivot_index]) < 1e-9:
                raise ValueError("透视角点无效，请调整四个角点")
            rows[pivot_index], rows[pivot_row] = rows[pivot_row], rows[pivot_index]
            pivot = rows[pivot_index][pivot_index]
            rows[pivot_index] = [value / pivot for value in rows[pivot_index]]
            for row_index in range(size):
                if row_index == pivot_index:
                    continue
                factor = rows[row_index][pivot_index]
                rows[row_index] = [
                    value - factor * pivot_value
                    for value, pivot_value in zip(rows[row_index], rows[pivot_index])
                ]
        return [row[-1] for row in rows]
