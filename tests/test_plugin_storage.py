from __future__ import annotations

import importlib
import sys
import types
from pathlib import Path


def test_resolve_plugin_data_dir_uses_plugin_data(tmp_path, monkeypatch):
    astrbot_module = types.ModuleType("astrbot")
    core_module = types.ModuleType("astrbot.core")
    utils_module = types.ModuleType("astrbot.core.utils")
    astrbot_path_module = types.ModuleType("astrbot.core.utils.astrbot_path")

    astrbot_path_module.get_astrbot_data_path = lambda: tmp_path

    monkeypatch.setitem(sys.modules, "astrbot", astrbot_module)
    monkeypatch.setitem(sys.modules, "astrbot.core", core_module)
    monkeypatch.setitem(sys.modules, "astrbot.core.utils", utils_module)
    monkeypatch.setitem(
        sys.modules,
        "astrbot.core.utils.astrbot_path",
        astrbot_path_module,
    )

    sys.modules.pop("astrbot_plugin_fishing.core.plugin_storage", None)
    plugin_storage = importlib.import_module(
        "astrbot_plugin_fishing.core.plugin_storage"
    )

    data_dir = plugin_storage.resolve_plugin_data_dir("astrbot_plugin_fishing_again")

    assert data_dir == Path(tmp_path) / "plugin_data" / "astrbot_plugin_fishing_again"
    assert data_dir.exists()
    assert data_dir.is_dir()
