from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


class TaskStore:
    def __init__(self):
        self._tasks: dict[str, dict[str, Any]] = {}

    def create_completed(self, task_type: str, result: dict[str, Any]) -> dict[str, Any]:
        task = {
            "id": uuid4().hex,
            "type": task_type,
            "status": "completed",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "result": result,
        }
        self._tasks[task["id"]] = task
        return task

    def get(self, task_id: str) -> dict[str, Any] | None:
        return self._tasks.get(task_id)


task_store = TaskStore()
