import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4


class AssetRegistry:
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.project_file = project_dir / "project.json"

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
        return json.loads(self.project_file.read_text(encoding="utf-8"))

    def _save_project(self, project: dict[str, Any]) -> None:
        self.project_file.write_text(json.dumps(project, ensure_ascii=False, indent=2), encoding="utf-8")
