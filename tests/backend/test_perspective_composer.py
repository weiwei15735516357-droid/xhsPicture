from pathlib import Path
from time import sleep

from fastapi.testclient import TestClient
from PIL import Image

from backend.server import create_app
from backend.services.perspective_composer import PerspectiveComposer
from backend.services.project_service import ProjectService


def test_perspective_composer_batches_overlays_to_xhs_canvas(tmp_path: Path):
    project_dir = tmp_path / "ProjectA"
    ProjectService().create_project(project_dir)
    scene_path = tmp_path / "scene.png"
    overlay_a = tmp_path / "a.png"
    overlay_b = tmp_path / "b.png"
    Image.new("RGB", (900, 1200), (240, 240, 240)).save(scene_path)
    Image.new("RGB", (400, 300), (180, 20, 20)).save(overlay_a)
    Image.new("RGB", (400, 300), (20, 40, 180)).save(overlay_b)

    result = PerspectiveComposer().compose_batch(
        project_dir=project_dir,
        scene_path=scene_path,
        overlay_paths=[overlay_a, overlay_b],
        points=[
            {"x": 0.20, "y": 0.20},
            {"x": 0.80, "y": 0.20},
            {"x": 0.80, "y": 0.70},
            {"x": 0.20, "y": 0.70},
        ],
        shadow=False,
    )

    assert len(result["assets"]) == 2
    output = Image.open(result["assets"][0]["path"]).convert("RGB")
    assert output.size == (1080, 1440)
    assert output.getpixel((540, 600)) == (180, 20, 20)
    assert result["assets"][0]["source_type"] == "透视合成图"


def test_perspective_compose_start_api_reports_completed_task(tmp_path: Path):
    project_dir = tmp_path / "ProjectA"
    ProjectService().create_project(project_dir)
    scene_path = tmp_path / "scene.png"
    overlay_path = tmp_path / "overlay.png"
    Image.new("RGB", (900, 1200), (240, 240, 240)).save(scene_path)
    Image.new("RGB", (400, 300), (180, 20, 20)).save(overlay_path)
    client = TestClient(create_app())

    response = client.post(
        "/api/perspective/compose/start",
        json={
            "project_dir": str(project_dir),
            "scene_path": str(scene_path),
            "overlay_paths": [str(overlay_path)],
            "points": [
                {"x": 0.20, "y": 0.20},
                {"x": 0.80, "y": 0.20},
                {"x": 0.80, "y": 0.70},
                {"x": 0.20, "y": 0.70},
            ],
        },
    )

    task_id = response.json()["task"]["id"]
    task = client.get(f"/api/tasks/{task_id}").json()
    for _ in range(20):
        if task["status"] != "running":
            break
        sleep(0.05)
        task = client.get(f"/api/tasks/{task_id}").json()

    assert response.status_code == 200
    assert task["status"] == "completed"
    assert len(task["result"]["assets"]) == 1
