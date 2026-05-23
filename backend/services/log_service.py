import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4


class LogService:
    def __init__(self, path: Path):
        self.path = path

    def append(self, level: str, message: str, context: dict[str, Any]) -> dict[str, Any]:
        entry = {
            "id": uuid4().hex,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": level,
            "message": message,
            "context": context,
        }
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
        return entry

    def list_entries(self, limit: int = 100) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        lines = self.path.read_text(encoding="utf-8").splitlines()
        entries = [json.loads(line) for line in lines if line.strip()]
        return list(reversed(entries))[:limit]
