import shutil
from pathlib import Path
from typing import Any

from backend.services.asset_registry import AssetRegistry


SUPPORTED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}


class AssetImporter:
    def import_paths(self, project_dir: Path, paths: list[Path]) -> list[dict[str, Any]]:
        imported = []
        registry = AssetRegistry(project_dir)
        target_dir = project_dir / "source"
        target_dir.mkdir(parents=True, exist_ok=True)

        for input_path in paths:
            for image_path in self._iter_images(input_path):
                target_path = self._unique_target_path(target_dir / image_path.name)
                shutil.copy2(image_path, target_path)
                imported.append(registry.add_asset(target_path, "普通图片", "import"))
        return imported

    def _iter_images(self, path: Path) -> list[Path]:
        if path.is_file() and path.suffix.lower() in SUPPORTED_IMAGE_EXTENSIONS:
            return [path]
        if path.is_dir():
            return [
                child
                for child in sorted(path.iterdir(), key=lambda item: item.name.lower())
                if child.is_file() and child.suffix.lower() in SUPPORTED_IMAGE_EXTENSIONS
            ]
        return []

    def _unique_target_path(self, path: Path) -> Path:
        if not path.exists():
            return path
        index = 1
        while True:
            candidate = path.with_name(f"{path.stem}_{index}{path.suffix}")
            if not candidate.exists():
                return candidate
            index += 1
