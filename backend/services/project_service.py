import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class ProjectService:
    def create_project(self, project_dir: Path) -> dict[str, Any]:
        project_dir.mkdir(parents=True, exist_ok=True)

        project_data = {
            "name": project_dir.name,
            "project_dir": str(project_dir),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "assets": [],
            "tasks": [],
            "templates": [],
            "exports": [],
        }
        project_file = project_dir / "project.json"
        if not project_file.exists():
            project_file.write_text(json.dumps(project_data, ensure_ascii=False, indent=2), encoding="utf-8")
        return {"project_dir": str(project_dir), "project_file": str(project_file)}
