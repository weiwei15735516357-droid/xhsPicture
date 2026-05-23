from pathlib import Path
from typing import Any

from fastapi import FastAPI

from backend.models.schemas import CreateLogRequest, CreateProjectRequest, ImportAssetsRequest
from backend.services.asset_importer import AssetImporter
from backend.services.asset_registry import AssetRegistry
from backend.services.log_service import LogService
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

    @app.get("/api/assets")
    def list_assets(project_dir: str) -> dict[str, Any]:
        return {"assets": AssetRegistry(Path(project_dir)).list_assets()}

    @app.post("/api/assets/import")
    def import_assets(request: ImportAssetsRequest) -> dict[str, Any]:
        paths_to_import = [Path(item) for item in request.paths]
        assets = AssetImporter().import_paths(Path(request.project_dir), paths_to_import)
        return {"assets": assets}

    @app.get("/api/logs")
    def list_logs() -> list[dict[str, Any]]:
        return LogService(paths.LOG_DIR / "app.log").list_entries()

    @app.post("/api/logs")
    def create_log(request: CreateLogRequest) -> dict[str, Any]:
        return LogService(paths.LOG_DIR / "app.log").append(request.level, request.message, request.context)

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.server:app", host="127.0.0.1", port=8787, reload=False)
