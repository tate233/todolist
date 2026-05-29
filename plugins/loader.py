"""Discover and load plugins.

A plugin is a Python module exposing ``register(context)``, where context gives
access to the command registry (and, in the running app, the main window). We
discover ``*.py`` files in a plugins directory and import them.
"""
import importlib.util
import logging
from pathlib import Path
from typing import List

logger = logging.getLogger(__name__)


def discover(plugins_dir: Path) -> List[Path]:
    plugins_dir = Path(plugins_dir)
    if not plugins_dir.exists():
        return []
    return sorted(p for p in plugins_dir.glob("*.py") if not p.name.startswith("_"))


def load_module(path: Path):
    spec = importlib.util.spec_from_file_location(f"smartnotes_plugin_{path.stem}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_all(plugins_dir: Path, context) -> List[str]:
    """Import each plugin and call its register(context). Returns loaded names."""
    loaded = []
    for path in discover(plugins_dir):
        try:
            module = load_module(path)
            if hasattr(module, "register"):
                module.register(context)
                loaded.append(path.stem)
            else:
                logger.warning("插件 %s 缺少 register(context)", path.name)
        except Exception:  # noqa: PERF203 - isolate per-plugin failures
            logger.exception("加载插件失败: %s", path.name)
    return loaded
