# XHS Picture Phase 2 Assets and Documents Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the first usable production workflow: import image files/folders into a project asset pool and convert PDF pages into PNG assets.

**Architecture:** Python owns all file processing. Assets are indexed in `project.json`; images can be imported by copying into `source/`, and PDF pages render into `pages/<source-name>/`. Electron remains a shell for now; the API is ready for the next UI wiring step.

**Tech Stack:** FastAPI, Pydantic, Pillow, PyMuPDF, pytest.

---

## Scope

Included in this phase:

1. Asset model stored in `project.json`.
2. Image file and folder import API.
3. PDF to PNG export API with scale, page limits, and subfolder output.
4. Task status API for synchronous completed/failed task records.
5. Office conversion service boundary with availability detection.

Deferred:

1. Full Electron UI for file pickers.
2. Word/PPT COM conversion implementation.
3. Image thumbnail generation.
4. Perspective and collage tools.

## Tasks

### Task 1: Asset Registry

- [ ] Write failing tests for adding/listing assets in `project.json`.
- [ ] Implement `backend/services/asset_registry.py`.
- [ ] Verify tests pass.

### Task 2: Image Import API

- [ ] Write failing tests for importing one image and one folder.
- [ ] Implement `POST /api/assets/import` and `GET /api/assets`.
- [ ] Copy imported images into project `source/`.
- [ ] Verify tests pass.

### Task 3: PDF Export API

- [ ] Write failing tests that create a tiny PDF and export selected pages to PNG.
- [ ] Add `PyMuPDF` and `Pillow` dependencies.
- [ ] Implement `backend/services/document_exporter.py` for PDF rendering.
- [ ] Implement `POST /api/documents/export`.
- [ ] Verify tests pass.

### Task 4: Task Status

- [ ] Write failing tests for task records.
- [ ] Add `GET /api/tasks/{task_id}`.
- [ ] Store completed/failed task summaries in memory for phase two.
- [ ] Verify tests pass.

### Task 5: Final Verification

- [ ] Run `python -m pytest tests/backend -v`.
- [ ] Run `node --test app/electron/tests/main.test.js`.
- [ ] Start backend and call `/api/health`.
