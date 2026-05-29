"""i18n: translation, language switching, fallback, and locale completeness."""
import json
from pathlib import Path

import i18n


def test_default_language_translates():
    i18n.set_language("zh_CN")
    assert i18n.t("menu.file") == "文件"


def test_switch_language():
    i18n.set_language("en_US")
    assert i18n.t("menu.file") == "File"
    i18n.set_language("zh_CN")  # restore


def test_missing_key_falls_back_to_key():
    i18n.set_language("en_US")
    assert i18n.t("does.not.exist") == "does.not.exist"
    assert i18n.t("does.not.exist", "Default") == "Default"
    i18n.set_language("zh_CN")


def test_available_languages():
    langs = i18n.available_languages()
    assert "zh_CN" in langs and "en_US" in langs


def test_locale_files_have_same_keys():
    locales = Path(i18n.__file__).resolve().parent / "locales"
    zh = json.loads((locales / "zh_CN.json").read_text(encoding="utf-8"))
    en = json.loads((locales / "en_US.json").read_text(encoding="utf-8"))
    assert set(zh) == set(en), "locale key sets differ"
