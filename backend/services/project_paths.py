import hashlib
from pathlib import Path

from backend.storage import paths


def project_state_file(project_dir: Path) -> Path:
    normalized = str(project_dir.expanduser().resolve()).lower()
    project_id = hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]
    return paths.PROJECTS_DIR / project_id / "project.json"
