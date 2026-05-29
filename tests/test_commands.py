"""Command registry: register/execute, fuzzy search, and plugin loading."""
import pathlib

from commands import CommandRegistry
from plugins import loader


def test_register_and_execute():
    reg = CommandRegistry()
    calls = []
    reg.register("a.b", "Do Thing", lambda: calls.append(1))
    reg.execute("a.b")
    assert calls == [1]


def test_duplicate_registration_rejected():
    reg = CommandRegistry()
    reg.register("x", "X", lambda: None)
    try:
        reg.register("x", "X again", lambda: None)
        assert False, "expected ValueError"
    except ValueError:
        pass


def test_fuzzy_search_subsequence():
    reg = CommandRegistry()
    reg.register("core.new_note", "新建笔记", lambda: None)
    reg.register("core.save_note", "保存笔记", lambda: None)
    reg.register("core.settings", "设置", lambda: None)
    titles = [c.title for c in reg.search("note")]
    assert "新建笔记" in titles and "保存笔记" in titles
    # empty query returns everything
    assert len(reg.search("")) == 3


def test_unregister():
    reg = CommandRegistry()
    reg.register("x", "X", lambda: None)
    reg.unregister("x")
    assert reg.all() == []


def test_plugin_discovery_and_load(tmp_path):
    plugin = tmp_path / "myplugin.py"
    plugin.write_text(
        "def register(context):\n"
        "    context['registry'].register('p.hi', 'Plugin Hi', lambda: 'hi')\n",
        encoding="utf-8",
    )
    reg = CommandRegistry()
    loaded = loader.load_all(tmp_path, {"registry": reg})
    assert "myplugin" in loaded
    assert reg.execute("p.hi") == "hi"


def test_example_plugin_registers(tmp_path):
    # the shipped example plugin should load and register its command
    example = pathlib.Path(loader.__file__).resolve().parent.parent / "examples" / "hello_plugin.py"
    reg = CommandRegistry()
    mod = loader.load_module(example)
    mod.register({"registry": reg, "app": None})
    assert any(c.id == "plugin.hello" for c in reg.all())
