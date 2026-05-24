import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

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
        project.setdefault("assets", []).append(asset)
        self._save_project(project)
        return asset

    def list_assets(self) -> list[dict[str, Any]]:
        return self._load_project().get("assets", [])

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
