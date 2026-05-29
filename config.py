import logging
import json
import re
from pathlib import Path

from storage.atomic_io import atomic_write_json


logger = logging.getLogger(__name__)


def _detect_version() -> str:
    """Resolve the application version from a single source of truth.

    Order: installed package metadata -> pyproject.toml -> fallback. This
    avoids the version drifting between config.py and pyproject.toml.
    """
    try:
        from importlib.metadata import PackageNotFoundError, version
        try:
            return version("todolist")
        except PackageNotFoundError:
            pass
    except Exception:
        pass

    pyproject = Path(__file__).resolve().parent / "pyproject.toml"
    if pyproject.exists():
        try:
            import tomllib
            with open(pyproject, "rb") as f:
                return tomllib.load(f)["project"]["version"]
        except Exception:
            try:
                text = pyproject.read_text(encoding="utf-8")
                m = re.search(r'^version\s*=\s*"([^"]+)"', text, re.MULTILINE)
                if m:
                    return m.group(1)
            except Exception:
                pass
    return "0.0.0"


class Config:
    def __init__(self):
        self.app_name = "智能笔记管理系统"
        self.version = _detect_version()
        self.author = "开源项目"

        self.data_dir = Path.home() / ".smart_notes"
        self.notes_dir = self.data_dir / "notes"
        self.attachments_dir = self.data_dir / "attachments"
        self.exports_dir = self.data_dir / "exports"
        self.database_file = self.data_dir / "notes.db"
        self.config_file = self.data_dir / "config.json"
        self.index_file = self.data_dir / "search_index.json"

        self.window_width = 1200
        self.window_height = 800
        self.theme_color = "#2c3e50"
        self.accent_color = "#3498db"
        self.bg_color = "#ecf0f1"
        self.text_color = "#2c3e50"
        self.sidebar_width = 250

        self.editor_font = ("Consolas", 11)
        self.ui_font = ("Microsoft YaHei UI", 10)
        self.title_font = ("Microsoft YaHei UI", 12, "bold")

        self.auto_save = True
        self.auto_save_interval = 30
        self.max_recent_notes = 10
        self.enable_markdown_preview = True
        self.enable_syntax_highlight = True

        self.default_category = "未分类"
        self.categories = ["工作", "学习", "生活", "项目", "想法"]

        self._ensure_directories()
        self._load_config()

    def _ensure_directories(self):
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.notes_dir.mkdir(parents=True, exist_ok=True)
        self.attachments_dir.mkdir(parents=True, exist_ok=True)
        self.exports_dir.mkdir(parents=True, exist_ok=True)

    def _load_config(self):
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for key, value in data.items():
                        if hasattr(self, key) and key not in ['data_dir', 'notes_dir']:
                            setattr(self, key, value)
            except Exception as e:
                logger.exception("加载配置失败: %s", e)

    def save_config(self):
        try:
            config_data = {
                'window_width': self.window_width,
                'window_height': self.window_height,
                'auto_save': self.auto_save,
                'auto_save_interval': self.auto_save_interval,
                'categories': self.categories,
                'enable_markdown_preview': self.enable_markdown_preview,
                'enable_syntax_highlight': self.enable_syntax_highlight
            }
            atomic_write_json(self.config_file, config_data)
            return True
        except Exception as e:
            logger.exception("保存配置失败: %s", e)
            return False

    def add_category(self, category):
        if category and category not in self.categories:
            self.categories.append(category)
            self.save_config()
            return True
        return False

    def remove_category(self, category):
        if category in self.categories and category != self.default_category:
            self.categories.remove(category)
            self.save_config()
            return True
        return False

    def get_app_info(self):
        return {
            'name': self.app_name,
            'version': self.version,
            'author': self.author,
            'data_dir': str(self.data_dir),
            'notes_count': len(list(self.notes_dir.glob('*.md')))
        }

config = Config()
