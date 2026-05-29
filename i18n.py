"""Minimal i18n framework.

Loads JSON locale resources from locales/ and exposes t(key) with runtime
language switching and fallback to the default language (then the key itself).
"""
import json
import logging
from pathlib import Path
from typing import Dict

logger = logging.getLogger(__name__)

DEFAULT_LANG = "zh_CN"
_LOCALES_DIR = Path(__file__).resolve().parent / "locales"

_cache: Dict[str, Dict[str, str]] = {}
_current = DEFAULT_LANG


def _load(lang: str) -> Dict[str, str]:
    if lang in _cache:
        return _cache[lang]
    path = _LOCALES_DIR / f"{lang}.json"
    data: Dict[str, str] = {}
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception as e:
            logger.exception("加载语言资源失败 %s: %s", lang, e)
    _cache[lang] = data
    return data


def available_languages():
    if not _LOCALES_DIR.exists():
        return [DEFAULT_LANG]
    return sorted(p.stem for p in _LOCALES_DIR.glob("*.json"))


def set_language(lang: str):
    global _current  # noqa: PLW0603 - module-level current-language singleton
    _current = lang


def get_language() -> str:
    return _current


def t(key: str, default: str = None) -> str:
    """Translate key for the current language; fall back to default lang, then
    the provided default, then the key itself."""
    val = _load(_current).get(key)
    if val is not None:
        return val
    val = _load(DEFAULT_LANG).get(key)
    if val is not None:
        return val
    return default if default is not None else key
