import json
from pathlib import Path
from typing import Any

from backend.models.schemas import AppSettings


class SettingsStore:
    def __init__(self, path: Path):
        self.path = path

    def load(self) -> dict[str, Any]:
        if not self.path.exists():
            return AppSettings().model_dump()
        raw = json.loads(self.path.read_text(encoding="utf-8"))
        return AppSettings.model_validate(raw).model_dump()

    def save(self, updates: dict[str, Any]) -> dict[str, Any]:
        current = self.load()
        merged = self._deep_merge(current, updates)
        settings = AppSettings.model_validate(merged).model_dump()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(settings, ensure_ascii=False, indent=2), encoding="utf-8")
        return settings

    def _deep_merge(self, base: dict[str, Any], updates: dict[str, Any]) -> dict[str, Any]:
        result = dict(base)
        for key, value in updates.items():
            if isinstance(value, dict) and isinstance(result.get(key), dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        return result
