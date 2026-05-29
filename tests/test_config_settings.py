"""Settings persist to config.json and reload (new silent_auto_save field)."""
import importlib

import config as config_module


def test_settings_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    importlib.reload(config_module)
    cfg = config_module.Config()

    cfg.auto_save_interval = 99
    cfg.silent_auto_save = False
    cfg.enable_syntax_highlight = False
    assert cfg.save_config()

    reloaded = config_module.Config()
    assert reloaded.auto_save_interval == 99
    assert reloaded.silent_auto_save is False
    assert reloaded.enable_syntax_highlight is False
