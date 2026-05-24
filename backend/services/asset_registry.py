import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from PIL import Image

from backend.services.project_paths import project_state_file


class AssetRegistry:
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.project_file = project_state_file(project_dir)

    def add_asset(self, path: Path, source_type: str, origin: str) -> dict[str, Any]:
        project = self._load_project()
        asset = {
            "id": uuid4().hex,
            "path": str(path),
            "filename": path.name,
            "source_type": source_type,
            "origin": origin,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        asset.update(self._file_metadata(path))
        project.setdefault("assets", []).append(asset)
        self._save_project(project)
        return asset

    def list_assets(self, source_type: str | None = None, query: str | None = None, sort: str = "created_desc") -> list[dict[str, Any]]:
        project = self._load_project()
        assets = project.get("assets", [])
        changed = False
        for asset in assets:
            if self._ensure_metadata(asset):
                changed = True
        if changed:
            self._save_project(project)
        filtered = assets
        if source_type and source_type != "全部":
            filtered = [asset for asset in filtered if asset.get("source_type") == source_type]
        if query:
            lowered = query.lower()
            filtered = [asset for asset in filtered if lowered in asset.get("filename", "").lower()]
        return self._sort_assets(filtered, sort)

    def delete_asset(self, asset_id: str, delete_file: bool = False) -> dict[str, Any]:
        project = self._load_project()
        assets = project.get("assets", [])
        for index, asset in enumerate(assets):
            if asset.get("id") != asset_id:
                continue
            removed = assets.pop(index)
            if delete_file:
                path = Path(removed.get("path", ""))
                if path.exists() and path.is_file():
                    path.unlink()
            self._save_project(project)
            return removed
        raise KeyError(asset_id)

    def _load_project(self) -> dict[str, Any]:
        legacy_project_file = self.project_dir / "project.json"
        if not self.project_file.exists() and legacy_project_file.exists():
            self.project_file.parent.mkdir(parents=True, exist_ok=True)
            self.project_file.write_text(legacy_project_file.read_text(encoding="utf-8"), encoding="utf-8")
            legacy_project_file.unlink()
        if not self.project_file.exists():
            self.project_file.parent.mkdir(parents=True, exist_ok=True)
            return {
                "name": self.project_dir.name,
                "project_dir": str(self.project_dir),
                "created_at": datetime.now(timezone.utc).isoformat(),
                "assets": [],
                "tasks": [],
                "templates": [],
                "exports": [],
            }
        return json.loads(self.project_file.read_text(encoding="utf-8"))

    def _save_project(self, project: dict[str, Any]) -> None:
        self.project_file.write_text(json.dumps(project, ensure_ascii=False, indent=2), encoding="utf-8")

    def _ensure_metadata(self, asset: dict[str, Any]) -> bool:
        missing = {"width", "height", "file_size"} - set(asset)
        if not missing:
            return False
        asset.update(self._file_metadata(Path(asset.get("path", ""))))
        return True

    def _file_metadata(self, path: Path) -> dict[str, Any]:
        metadata: dict[str, Any] = {
            "width": None,
            "height": None,
            "file_size": path.stat().st_size if path.exists() else 0,
        }
        try:
            with Image.open(path) as image:
                metadata["width"] = image.width
                metadata["height"] = image.height
        except Exception:
            pass
        return metadata

    def _sort_assets(self, assets: list[dict[str, Any]], sort: str) -> list[dict[str, Any]]:
        if sort == "filename_asc":
            return sorted(assets, key=lambda asset: asset.get("filename", ""))
        if sort == "filename_desc":
            return sorted(assets, key=lambda asset: asset.get("filename", ""), reverse=True)
        if sort == "created_asc":
            return sorted(assets, key=lambda asset: asset.get("created_at", ""))
        return sorted(assets, key=lambda asset: asset.get("created_at", ""), reverse=True)
