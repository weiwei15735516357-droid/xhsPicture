from pathlib import Path
from threading import Thread
from typing import Any

from fastapi import FastAPI, HTTPException

from backend.models.schemas import (
    CreateLogRequest,
    CreateProjectRequest,
    FeishuFolderPreviewRequest,
    FeishuUploadRequest,
    ExportDocumentRequest,
    ImportAssetsRequest,
    PerspectiveComposeRequest,
)
from backend.services.asset_importer import AssetImporter
from backend.services.asset_registry import AssetRegistry
from backend.services.document_exporter import DocumentExporter
from backend.services.feishu_uploader import FeishuUploader
from backend.services.log_service import LogService
from backend.services.perspective_composer import PerspectiveComposer
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
    def list_assets(project_dir: str, source_type: str | None = None, q: str | None = None, sort: str = "created_desc") -> dict[str, Any]:
        return {"assets": AssetRegistry(Path(project_dir)).list_assets(source_type=source_type, query=q, sort=sort)}

    @app.post("/api/assets/import")
    def import_assets(request: ImportAssetsRequest) -> dict[str, Any]:
        paths_to_import = [Path(item) for item in request.paths]
        assets = AssetImporter().import_paths(Path(request.project_dir), paths_to_import)
        return {"assets": assets}

    @app.delete("/api/assets/{asset_id}")
    def delete_asset(asset_id: str, project_dir: str, delete_file: bool = False) -> dict[str, Any]:
        try:
            asset = AssetRegistry(Path(project_dir)).delete_asset(asset_id, delete_file=delete_file)
        except KeyError:
            raise HTTPException(status_code=404, detail="Asset not found") from None
        return {"asset": asset}

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
            custom_layout=[slot.model_dump() for slot in request.custom_layout] if request.custom_layout else None,
            followup_layout=[slot.model_dump() for slot in request.followup_layout] if request.followup_layout else None,
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
                    custom_layout=[slot.model_dump() for slot in request.custom_layout] if request.custom_layout else None,
                    followup_layout=[slot.model_dump() for slot in request.followup_layout] if request.followup_layout else None,
                    progress_callback=lambda current, total, message: task_store.update_progress(
                        task["id"], current, total, message
                    ),
                )
                task_store.complete(task["id"], result)
            except Exception as exc:
                task_store.fail(task["id"], str(exc))

        Thread(target=run_export, daemon=True).start()
        return {"task": task}

    @app.post("/api/perspective/compose/start")
    def start_perspective_compose(request: PerspectiveComposeRequest) -> dict[str, Any]:
        task = task_store.create_running("perspective_compose", "等待开始透视合成")

        def run_compose() -> None:
            try:
                composer = PerspectiveComposer()
                progress = lambda current, total, message: task_store.update_progress(task["id"], current, total, message)
                if request.mode == "excel":
                    if not request.excel_path:
                        raise ValueError("请选择 Excel 表格")
                    result = composer.compose_text_batch(
                        project_dir=Path(request.project_dir),
                        scene_path=Path(request.scene_path),
                        excel_path=Path(request.excel_path),
                        text_options=request.text_options.model_dump(),
                        text_rows=[row.model_dump() for row in request.text_rows],
                        progress_callback=progress,
                    )
                else:
                    if request.overlay_items:
                        result = composer.compose_items_batch(
                            project_dir=Path(request.project_dir),
                            scene_path=Path(request.scene_path),
                            overlay_items=[item.model_dump() for item in request.overlay_items],
                            progress_callback=progress,
                        )
                    else:
                        result = composer.compose_batch(
                            project_dir=Path(request.project_dir),
                            scene_path=Path(request.scene_path),
                            overlay_paths=[Path(item) for item in request.overlay_paths],
                            points=[point.model_dump() for point in request.points],
                            opacity=request.opacity,
                            shadow=request.shadow,
                            progress_callback=progress,
                        )
                task_store.complete(task["id"], result)
            except Exception as exc:
                task_store.fail(task["id"], str(exc))

        Thread(target=run_compose, daemon=True).start()
        return {"task": task}

    @app.get("/api/perspective/excel/rows")
    def list_perspective_excel_rows(excel_path: str) -> dict[str, Any]:
        rows = PerspectiveComposer().read_excel_rows(Path(excel_path))
        return {"rows": rows, "count": len(rows)}

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

    @app.post("/api/feishu/preview-folders")
    def preview_feishu_folders(request: FeishuFolderPreviewRequest) -> dict[str, Any]:
        return FeishuUploader().preview_folder_mapping(Path(request.upload_root), request.row_range)

    @app.post("/api/feishu/test")
    def test_feishu_connection(request: FeishuUploadRequest) -> dict[str, Any]:
        return FeishuUploader().test_connection(request.model_dump())

    @app.post("/api/feishu/upload/start")
    def start_feishu_upload(request: FeishuUploadRequest) -> dict[str, Any]:
        task = task_store.create_running("feishu_upload", "等待开始飞书上传")

        def run_upload() -> None:
            try:
                result = FeishuUploader().upload_by_folders(
                    request.model_dump(),
                    progress_callback=lambda current, total, message: task_store.update_progress(
                        task["id"], current, total, message
                    ),
                )
                task_store.complete(task["id"], result)
            except Exception as exc:
                task_store.fail(task["id"], str(exc))

        Thread(target=run_upload, daemon=True).start()
        return {"task": task}

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.server:app", host="127.0.0.1", port=8787, reload=False)
