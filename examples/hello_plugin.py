"""Example SmartNotes plugin.

Drop a copy into your plugins directory. On load it registers a command that
becomes available in the command palette (Ctrl+Shift+P).
"""


def register(context):
    registry = context["registry"]

    def say_hello():
        app = context.get("app")
        msg = "你好，来自示例插件 👋"
        if app is not None and hasattr(app, "_set_status"):
            app._set_status(msg)
        return msg

    registry.register("plugin.hello", "示例插件: 打招呼", say_hello)
