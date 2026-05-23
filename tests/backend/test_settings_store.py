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
