# XHS Picture Phase 1 Skeleton Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first runnable Windows desktop skeleton: Electron starts a local Python API, verifies health, saves settings, creates project folders, and writes task logs.

**Architecture:** Electron owns the desktop window and process lifecycle. Python FastAPI exposes a local API on `127.0.0.1`, stores JSON settings under `data/config.json`, creates user project directories, and writes logs under `data/logs` and project `logs/` folders.

**Tech Stack:** Electron v30 from `D:\WindowsUtils\Electron\electron-v30.5.1-win32-x64`, Python 3, FastAPI, Uvicorn, Pydantic, pytest, Node.js built-in modules, plain HTML/CSS/JavaScript.

---

## Scope

This plan implements only phase one from the approved spec:

1. Project skeleton.
2. Python local service.
3. Health check API.
4. Settings API.
5. Project directory creation API.
6. Logging API.
7. Electron shell that starts Python and displays backend status.

The following approved features are assigned to later phase plans: document conversion, image pool, perspective composition, collage template rendering, export pipeline, and Feishu upload.

## File Structure

- Create `requirements.txt` for Python runtime and test dependencies.
- Create `backend/server.py` for FastAPI app factory and executable entrypoint.
- Create `backend/models/schemas.py` for request and response schemas.
- Create `backend/services/settings_store.py` for JSON settings read/write behavior.
- Create `backend/services/project_service.py` for project folder creation and `project.json` initialization.
- Create `backend/services/log_service.py` for append-only log records.
- Create `backend/storage/paths.py` for repository-relative path helpers.
- Create backend tests under `tests/backend/`.
- Create Electron files under `app/electron/`.
- Create `.gitignore` and `README.md`.

Generated runtime paths:

- `data/config.json`
- `data/logs/app.log`
- `data/projects/`
- selected user project folders containing `source/`, `pages/`, `compositions/`, `collages/`, `exports/`, `logs/`, `templates/`, and `project.json`

---

### Task 1: Python Dependency and Health Endpoint

**Files:**
- Create: `requirements.txt`
- Create: `backend/__init__.py`
- Create: `backend/server.py`
- Create: `tests/backend/test_health.py`

- [ ] **Step 1: Write dependencies**

Create `requirements.txt`:

```text
fastapi==0.115.6
uvicorn==0.32.1
pydantic==2.10.3
pytest==8.3.4
httpx==0.28.1
```

- [ ] **Step 2: Write failing test**

Create `tests/backend/test_health.py`:

```python
from fastapi.testclient import TestClient

from backend.server import create_app


def test_health_endpoint_reports_service_ready():
    client = TestClient(create_app())

    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"ok": True, "service": "xhs-picture-backend"}
```

- [ ] **Step 3: Run test to verify it fails**

Run:

```powershell
python -m pytest tests/backend/test_health.py -v
```

Expected: FAIL or ERROR because `backend.server.create_app` does not exist yet.

- [ ] **Step 4: Implement minimal app**

Create `backend/__init__.py`:

```python
"""Local backend for the XHS picture desktop app."""
```

Create `backend/server.py`:

```python
from fastapi import FastAPI


def create_app() -> FastAPI:
    app = FastAPI(title="XHS Picture Backend")

    @app.get("/api/health")
    def health() -> dict[str, object]:
        return {"ok": True, "service": "xhs-picture-backend"}

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.server:app", host="127.0.0.1", port=8787, reload=False)
```

- [ ] **Step 5: Run test to verify it passes**

Run:

```powershell
python -m pytest tests/backend/test_health.py -v
```

Expected: PASS.

---

### Task 2: Settings Storage and API

**Files:**
- Create: `backend/storage/__init__.py`
- Create: `backend/storage/paths.py`
- Create: `backend/services/__init__.py`
- Create: `backend/services/settings_store.py`
- Create: `backend/models/__init__.py`
- Create: `backend/models/schemas.py`
- Modify: `backend/server.py`
- Create: `tests/backend/test_settings_store.py`

- [ ] **Step 1: Write failing settings tests**

Create `tests/backend/test_settings_store.py`:

```python
from pathlib import Path

from backend.services.settings_store import SettingsStore


def test_settings_store_returns_defaults_when_file_is_missing(tmp_path: Path):
    store = SettingsStore(tmp_path / "config.json")

    settings = store.load()

    assert settings["backend_port"] == 8787
    assert settings["default_export_scale"] == 2
    assert settings["default_canvas_ratio"] == "3:4"
    assert settings["default_export_format"] == "png"
    assert settings["recent_project_dir"] is None
    assert settings["feishu"]["app_id"] == ""


def test_settings_store_saves_known_values_and_preserves_defaults(tmp_path: Path):
    store = SettingsStore(tmp_path / "config.json")

    saved = store.save({"default_canvas_ratio": "4:5", "feishu": {"app_id": "cli_xxx"}})
    loaded = store.load()

    assert saved["default_canvas_ratio"] == "4:5"
    assert loaded["default_canvas_ratio"] == "4:5"
    assert loaded["default_export_scale"] == 2
    assert loaded["feishu"]["app_id"] == "cli_xxx"
    assert loaded["feishu"]["app_secret"] == ""
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```powershell
python -m pytest tests/backend/test_settings_store.py -v
```

Expected: FAIL or ERROR because `SettingsStore` does not exist.

- [ ] **Step 3: Implement storage, schemas, and settings store**

Create `backend/storage/__init__.py`:

```python
"""Storage helpers for local JSON files and project folders."""
```

Create `backend/storage/paths.py`:

```python
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = REPO_ROOT / "data"
CONFIG_PATH = DATA_DIR / "config.json"
LOG_DIR = DATA_DIR / "logs"
PROJECTS_DIR = DATA_DIR / "projects"
```

Create `backend/services/__init__.py`:

```python
"""Backend service modules."""
```

Create `backend/models/__init__.py`:

```python
"""Request and response models."""
```

Create `backend/models/schemas.py`:

```python
from pydantic import BaseModel, Field


class FeishuSettings(BaseModel):
    app_id: str = ""
    app_secret: str = ""
    bitable_url: str = ""
    table_id: str = ""
    attachment_field_name: str = ""
    row_range: str = ""


class AppSettings(BaseModel):
    backend_port: int = 8787
    recent_project_dir: str | None = None
    office_available: bool | None = None
    default_export_scale: int = Field(default=2, ge=1, le=4)
    default_canvas_ratio: str = "3:4"
    default_export_format: str = "png"
    feishu: FeishuSettings = Field(default_factory=FeishuSettings)
```

Create `backend/services/settings_store.py`:

```python
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
```

- [ ] **Step 4: Add settings routes**

Replace `backend/server.py`:

```python
from typing import Any

from fastapi import FastAPI

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

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.server:app", host="127.0.0.1", port=8787, reload=False)
```

- [ ] **Step 5: Run tests to verify they pass**

Run:

```powershell
python -m pytest tests/backend/test_settings_store.py tests/backend/test_health.py -v
```

Expected: PASS.

---

### Task 3: Project Creation API

**Files:**
- Create: `backend/services/project_service.py`
- Modify: `backend/models/schemas.py`
- Modify: `backend/server.py`
- Create: `tests/backend/test_project_service.py`

- [ ] **Step 1: Write failing project service tests**

Create `tests/backend/test_project_service.py`:

```python
import json
from pathlib import Path

from fastapi.testclient import TestClient

from backend.server import create_app
from backend.services.project_service import ProjectService


def test_create_project_builds_required_directory_tree(tmp_path: Path):
    service = ProjectService()
    project_dir = tmp_path / "MayCampaign"

    result = service.create_project(project_dir)

    assert result["project_dir"] == str(project_dir)
    for name in ["source", "pages", "compositions", "collages", "exports", "logs", "templates"]:
        assert (project_dir / name).is_dir()
    assert (project_dir / "project.json").is_file()


def test_create_project_initializes_project_json(tmp_path: Path):
    service = ProjectService()
    project_dir = tmp_path / "MayCampaign"

    service.create_project(project_dir)
    data = json.loads((project_dir / "project.json").read_text(encoding="utf-8"))

    assert data["name"] == "MayCampaign"
    assert data["assets"] == []
    assert data["tasks"] == []
    assert data["templates"] == []


def test_create_project_api_returns_created_project(tmp_path: Path):
    client = TestClient(create_app())
    project_dir = tmp_path / "ApiProject"

    response = client.post("/api/project/create", json={"project_dir": str(project_dir)})

    assert response.status_code == 200
    assert response.json()["project_dir"] == str(project_dir)
    assert (project_dir / "project.json").is_file()
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```powershell
python -m pytest tests/backend/test_project_service.py -v
```

Expected: FAIL or ERROR because `ProjectService` does not exist.

- [ ] **Step 3: Implement project service and route**

Create `backend/services/project_service.py`:

```python
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_SUBDIRS = ["source", "pages", "compositions", "collages", "exports", "logs", "templates"]


class ProjectService:
    def create_project(self, project_dir: Path) -> dict[str, Any]:
        project_dir.mkdir(parents=True, exist_ok=True)
        for name in PROJECT_SUBDIRS:
            (project_dir / name).mkdir(exist_ok=True)

        project_data = {
            "name": project_dir.name,
            "project_dir": str(project_dir),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "assets": [],
            "tasks": [],
            "templates": [],
            "exports": [],
        }
        project_file = project_dir / "project.json"
        if not project_file.exists():
            project_file.write_text(json.dumps(project_data, ensure_ascii=False, indent=2), encoding="utf-8")
        return {"project_dir": str(project_dir), "project_file": str(project_file)}
```

Append to `backend/models/schemas.py`:

```python

class CreateProjectRequest(BaseModel):
    project_dir: str
```

Update `backend/server.py` to include:

```python
from pathlib import Path
from backend.models.schemas import CreateProjectRequest
from backend.services.project_service import ProjectService

@app.post("/api/project/create")
def create_project(request: CreateProjectRequest) -> dict[str, Any]:
    return ProjectService().create_project(Path(request.project_dir))
```

- [ ] **Step 4: Run tests to verify they pass**

Run:

```powershell
python -m pytest tests/backend/test_project_service.py -v
```

Expected: PASS.

---

### Task 4: Log Service and API

**Files:**
- Create: `backend/services/log_service.py`
- Modify: `backend/models/schemas.py`
- Modify: `backend/server.py`
- Create: `tests/backend/test_log_service.py`

- [ ] **Step 1: Write failing log tests**

Create `tests/backend/test_log_service.py`:

```python
import json
from pathlib import Path

from fastapi.testclient import TestClient

from backend.server import create_app
from backend.services.log_service import LogService


def test_log_service_appends_json_lines(tmp_path: Path):
    log_path = tmp_path / "app.log"
    service = LogService(log_path)

    first = service.append("info", "created project", {"project": "A"})
    second = service.append("error", "failed task", {"task_id": "t1"})

    lines = log_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    assert json.loads(lines[0])["message"] == "created project"
    assert json.loads(lines[1])["level"] == "error"
    assert first["id"] != second["id"]


def test_log_service_reads_latest_entries_first(tmp_path: Path):
    log_path = tmp_path / "app.log"
    service = LogService(log_path)
    service.append("info", "one", {})
    service.append("info", "two", {})

    entries = service.list_entries(limit=1)

    assert len(entries) == 1
    assert entries[0]["message"] == "two"


def test_logs_api_returns_entries(tmp_path: Path, monkeypatch):
    from backend.storage import paths

    monkeypatch.setattr(paths, "LOG_DIR", tmp_path)
    client = TestClient(create_app())

    post_response = client.post("/api/logs", json={"level": "info", "message": "hello", "context": {"a": 1}})
    get_response = client.get("/api/logs")

    assert post_response.status_code == 200
    assert get_response.status_code == 200
    assert get_response.json()[0]["message"] == "hello"
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```powershell
python -m pytest tests/backend/test_log_service.py -v
```

Expected: FAIL or ERROR because `LogService` does not exist.

- [ ] **Step 3: Implement log service and routes**

Create `backend/services/log_service.py`:

```python
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
```

Append to `backend/models/schemas.py`:

```python

class CreateLogRequest(BaseModel):
    level: str
    message: str
    context: dict = Field(default_factory=dict)
```

Update `backend/server.py` to include:

```python
from backend.models.schemas import CreateLogRequest
from backend.services.log_service import LogService

@app.get("/api/logs")
def list_logs() -> list[dict[str, Any]]:
    return LogService(paths.LOG_DIR / "app.log").list_entries()

@app.post("/api/logs")
def create_log(request: CreateLogRequest) -> dict[str, Any]:
    return LogService(paths.LOG_DIR / "app.log").append(request.level, request.message, request.context)
```

- [ ] **Step 4: Run backend tests**

Run:

```powershell
python -m pytest tests/backend -v
```

Expected: PASS.

---

### Task 5: Electron Shell and Renderer

**Files:**
- Create: `app/electron/package.json`
- Create: `app/electron/main.js`
- Create: `app/electron/preload.js`
- Create: `app/electron/renderer/index.html`
- Create: `app/electron/renderer/styles.css`
- Create: `app/electron/renderer/app.js`
- Create: `app/electron/tests/main.test.js`

- [ ] **Step 1: Write failing Electron helper test**

Create `app/electron/tests/main.test.js`:

```javascript
const assert = require('node:assert');
const test = require('node:test');
const path = require('node:path');

const { getBackendArgs, getBackendWorkingDirectory } = require('../main');

test('backend launch args run the Python module', () => {
  assert.deepStrictEqual(getBackendArgs(), ['-m', 'backend.server']);
});

test('backend working directory points at repo root', () => {
  const cwd = getBackendWorkingDirectory();
  assert.strictEqual(path.basename(cwd), 'xhsPicture');
});
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```powershell
node --test app/electron/tests/main.test.js
```

Expected: FAIL or ERROR because `app/electron/main.js` does not exist.

- [ ] **Step 3: Implement Electron app files**

Create `app/electron/package.json`:

```json
{
  "name": "xhs-picture-desktop",
  "version": "0.1.0",
  "private": true,
  "main": "main.js",
  "scripts": {
    "start": "electron .",
    "test": "node --test tests/*.test.js"
  }
}
```

Create `app/electron/main.js`:

```javascript
const { app, BrowserWindow, ipcMain } = require('electron');
const { spawn } = require('node:child_process');
const path = require('node:path');

let backendProcess = null;

function getBackendWorkingDirectory() {
  return path.resolve(__dirname, '..', '..');
}

function getBackendArgs() {
  return ['-m', 'backend.server'];
}

function getPythonExecutable() {
  return process.env.XHS_PYTHON || 'python';
}

function startBackend() {
  if (backendProcess) {
    return backendProcess;
  }
  backendProcess = spawn(getPythonExecutable(), getBackendArgs(), {
    cwd: getBackendWorkingDirectory(),
    windowsHide: true,
    stdio: 'ignore'
  });
  backendProcess.on('exit', () => {
    backendProcess = null;
  });
  return backendProcess;
}

function stopBackend() {
  if (backendProcess) {
    backendProcess.kill();
    backendProcess = null;
  }
}

function createWindow() {
  const win = new BrowserWindow({
    width: 1280,
    height: 820,
    minWidth: 1000,
    minHeight: 680,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js')
    }
  });
  win.loadFile(path.join(__dirname, 'renderer', 'index.html'));
}

if (require.main === module) {
  app.whenReady().then(() => {
    startBackend();
    createWindow();
  });
  app.on('before-quit', stopBackend);
  ipcMain.handle('backend:base-url', () => 'http://127.0.0.1:8787');
}

module.exports = { getBackendArgs, getBackendWorkingDirectory, getPythonExecutable, startBackend, stopBackend };
```

Create `app/electron/preload.js`:

```javascript
const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('xhsApp', {
  getBackendBaseUrl: () => ipcRenderer.invoke('backend:base-url')
});
```

Create `app/electron/renderer/index.html`, `styles.css`, and `app.js` with a sidebar workbench page and a health status element that calls `/api/health`.

- [ ] **Step 4: Run Electron helper tests**

Run:

```powershell
node --test app/electron/tests/main.test.js
```

Expected: PASS.

---

### Task 6: README and Final Verification

**Files:**
- Create: `.gitignore`
- Create: `README.md`

- [ ] **Step 1: Create ignore rules**

Create `.gitignore`:

```text
__pycache__/
.pytest_cache/
*.pyc
node_modules/
data/config.json
data/logs/
data/projects/
.DS_Store
```

- [ ] **Step 2: Create README**

Create `README.md`:

```markdown
# 小红书图片工作台

Windows 单机桌面工具，用于制作小红书图片笔记、商品主图和详情图。

## 第一阶段能力

- Electron 桌面壳
- Python FastAPI 本地后端
- 健康检查
- 设置读写
- 项目目录创建
- 本地日志

## 环境

- Windows
- Python 3
- Electron: `D:\WindowsUtils\Electron\electron-v30.5.1-win32-x64`

## 安装 Python 依赖

```powershell
python -m pip install -r requirements.txt
```

## 运行后端

```powershell
python -m backend.server
```

## 运行桌面端

```powershell
& 'D:\WindowsUtils\Electron\electron-v30.5.1-win32-x64\electron.exe' 'G:\CodeWork\CodeX\xhsPicture\app\electron'
```

## 测试

```powershell
python -m pytest tests/backend -v
node --test app/electron/tests/main.test.js
```
```

- [ ] **Step 3: Run final verification**

Run:

```powershell
python -m pytest tests/backend -v
node --test app/electron/tests/main.test.js
```

Expected: all tests PASS.

Run:

```powershell
& 'D:\WindowsUtils\Electron\electron-v30.5.1-win32-x64\electron.exe' 'G:\CodeWork\CodeX\xhsPicture\app\electron'
```

Expected: desktop window opens and shows `后端已连接` within five seconds.

---

## Plan Self-Review

Spec coverage for phase one:

- Electron starts Python backend: Task 5.
- Health check: Task 1 and Task 6.
- Settings API foundation: Task 2.
- Project directory creation: Task 3.
- Logging system: Task 4.
- Local file layout: Task 3 and Task 6.

Gaps intentionally deferred to later phase plans:

- Document export.
- Image pool.
- Perspective composition.
- Collage rendering.
- Export task pipeline.
- Feishu upload.

Placeholder scan: no task uses placeholder implementation language for backend behavior. Renderer details are intentionally minimal because the first phase UI is a workbench shell; the production behavior is the health connection.

Type consistency: route names, schema names, and service class names are consistent across tests and implementation steps.
