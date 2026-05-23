from pathlib import Path
from typing import Any

from fastapi import FastAPI

from backend.models.schemas import CreateProjectRequest
from backend.services.project_service import ProjectService
from backend.services.settings_store import SettingsStore
from backend.storage import paths


def create_app() -> FastAPI:
    app = FastAPI(title="XHS Picture Backend")

    @app.get("/api/health")
    def health() -> dict[str, object]:
        return {"ok": True, "service": "xhs-picture-backend"}

    @app.get("/api/settings")
    def get_settings() -> dict[str, Any]:
        return SettingsStore(paths.CONFIG_PATH).load()

    @app.post("/api/settings")
    def save_settings(updates: dict[str, Any]) -> dict[str, Any]:
        return SettingsStore(paths.CONFIG_PATH).save(updates)

    @app.post("/api/project/create")
    def create_project(request: CreateProjectRequest) -> dict[str, Any]:
        return ProjectService().create_project(Path(request.project_dir))

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.server:app", host="127.0.0.1", port=8787, reload=False)
