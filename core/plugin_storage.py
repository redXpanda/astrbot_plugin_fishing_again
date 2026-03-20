from __future__ import annotations

from pathlib import Path

from astrbot.core.utils.astrbot_path import get_astrbot_data_path


def resolve_plugin_data_dir(plugin_name: str) -> Path:
    """按 AstrBot 标准返回插件数据目录，并确保目录存在。"""
    data_dir = Path(get_astrbot_data_path()) / "plugin_data" / plugin_name
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir
