import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from backend.services.project_paths import project_state_file


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
        project_file = project_state_file(project_dir)
        project_file.parent.mkdir(parents=True, exist_ok=True)
        legacy_project_file = project_dir / "project.json"
        if legacy_project_file.exists() and not project_file.exists():
            project_file.write_text(legacy_project_file.read_text(encoding="utf-8"), encoding="utf-8")
            legacy_project_file.unlink()
        elif legacy_project_file.exists():
            legacy_project_file.unlink()
        if not project_file.exists():
            project_file.write_text(json.dumps(project_data, ensure_ascii=False, indent=2), encoding="utf-8")
        self._cleanup_legacy_temp_dirs(project_dir)
        return {"project_dir": str(project_dir), "project_file": str(project_file)}

    def _cleanup_legacy_temp_dirs(self, project_dir: Path) -> None:
        pages_dir = project_dir / "pages"
        office_temp_dir = pages_dir / "_office_pdf"
        if office_temp_dir.exists():
            shutil.rmtree(office_temp_dir)
        if pages_dir.exists() and not any(pages_dir.iterdir()):
            pages_dir.rmdir()
