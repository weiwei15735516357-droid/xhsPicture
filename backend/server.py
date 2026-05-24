from pathlib import Path
from threading import Thread
from typing import Any

from fastapi import FastAPI, HTTPException

from backend.models.schemas import CreateLogRequest, CreateProjectRequest, ExportDocumentRequest, ImportAssetsRequest
from backend.services.asset_importer import AssetImporter
from backend.services.asset_registry import AssetRegistry
from backend.services.document_exporter import DocumentExporter
from backend.services.log_service import LogService
from backend.services.project_service import ProjectService
from backend.services.settings_store import SettingsStore
from backend.services.task_store import task_store
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

    @app.post("/api/documents/export")
    def export_document(request: ExportDocumentRequest) -> dict[str, Any]:
        result = DocumentExporter().export(
            project_dir=Path(request.project_dir),
            file_path=Path(request.file_path),
            scale=request.scale,
            page_start=request.page_start,
            page_end=request.page_end,
            subfolder_output=request.subfolder_output,
            summary_group_size=request.summary_group_size,
            background_path=Path(request.background_path) if request.background_path else None,
            background_has_text=request.background_has_text,
        )
        task = task_store.create_completed("document_export", result)
        return {"task": task, "assets": result["assets"]}

    @app.post("/api/documents/export/start")
    def start_document_export(request: ExportDocumentRequest) -> dict[str, Any]:
        task = task_store.create_running("document_export", "等待开始导出")

        def run_export() -> None:
            try:
                result = DocumentExporter().export(
                    project_dir=Path(request.project_dir),
                    file_path=Path(request.file_path),
                    scale=request.scale,
                    page_start=request.page_start,
                    page_end=request.page_end,
                    subfolder_output=request.subfolder_output,
                    summary_group_size=request.summary_group_size,
                    background_path=Path(request.background_path) if request.background_path else None,
                    background_has_text=request.background_has_text,
                    progress_callback=lambda current, total, message: task_store.update_progress(
                        task["id"], current, total, message
                    ),
                )
                task_store.complete(task["id"], result)
            except Exception as exc:
                task_store.fail(task["id"], str(exc))

        Thread(target=run_export, daemon=True).start()
        return {"task": task}

    @app.get("/api/tasks/{task_id}")
    def get_task(task_id: str) -> dict[str, Any]:
        task = task_store.get(task_id)
        if task is None:
            raise HTTPException(status_code=404, detail="Task not found")
        return task

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
