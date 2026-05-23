from pathlib import Path

import fitz
from fastapi.testclient import TestClient

from backend.server import create_app
from backend.services.project_service import ProjectService


def test_task_status_api_returns_completed_document_export(tmp_path: Path):
    project_dir = tmp_path / "ProjectA"
    ProjectService().create_project(project_dir)
    pdf_path = tmp_path / "sample.pdf"
    doc = fitz.open()
    doc.new_page(width=100, height=100)
    doc.save(pdf_path)
    doc.close()
    client = TestClient(create_app())

    export_response = client.post(
        "/api/documents/export",
        json={"project_dir": str(project_dir), "file_path": str(pdf_path)},
    )
    task_id = export_response.json()["task"]["id"]
    task_response = client.get(f"/api/tasks/{task_id}")

    assert task_response.status_code == 200
    assert task_response.json()["id"] == task_id
    assert task_response.json()["status"] == "completed"
