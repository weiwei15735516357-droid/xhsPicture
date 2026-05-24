from datetime import datetime, timezone
from threading import Lock
from typing import Any
from uuid import uuid4


class TaskStore:
    def __init__(self):
        self._tasks: dict[str, dict[str, Any]] = {}
        self._lock = Lock()

    def create_running(self, task_type: str, message: str = "任务已开始") -> dict[str, Any]:
        task = {
            "id": uuid4().hex,
            "type": task_type,
            "status": "running",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "progress": {"current": 0, "total": 1, "percent": 0, "message": message},
            "result": None,
            "error": None,
        }
        with self._lock:
            self._tasks[task["id"]] = task
        return task

    def create_completed(self, task_type: str, result: dict[str, Any]) -> dict[str, Any]:
        task = {
            "id": uuid4().hex,
            "type": task_type,
            "status": "completed",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "progress": {"current": 1, "total": 1, "percent": 100, "message": "任务完成"},
            "result": result,
            "error": None,
        }
        with self._lock:
            self._tasks[task["id"]] = task
        return task

    def update_progress(self, task_id: str, current: int, total: int, message: str) -> None:
        total = max(total, 1)
        current = max(0, min(current, total))
        with self._lock:
            task = self._tasks.get(task_id)
            if not task:
                return
            task["progress"] = {
                "current": current,
                "total": total,
                "percent": int(current * 100 / total),
                "message": message,
            }

    def complete(self, task_id: str, result: dict[str, Any]) -> None:
        with self._lock:
            task = self._tasks.get(task_id)
            if not task:
                return
            task["status"] = "completed"
            task["progress"] = {"current": 1, "total": 1, "percent": 100, "message": "任务完成"}
            task["result"] = result
            task["error"] = None

    def fail(self, task_id: str, error: str) -> None:
        with self._lock:
            task = self._tasks.get(task_id)
            if not task:
                return
            task["status"] = "failed"
            task["error"] = error
            progress = task.get("progress") or {"current": 0, "total": 1, "percent": 0}
            task["progress"] = {**progress, "message": error}

    def get(self, task_id: str) -> dict[str, Any] | None:
        with self._lock:
            task = self._tasks.get(task_id)
            return dict(task) if task else None


task_store = TaskStore()
