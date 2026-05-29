"""Central command registry powering the command palette and shortcuts.

Core actions and plugin-provided actions register here under a unique id with a
human title and a callable. The palette does fuzzy filtering over titles.
"""
from dataclasses import dataclass
from typing import Callable, Dict, List


@dataclass
class Command:
    id: str
    title: str
    handler: Callable
    shortcut: str = ""


class CommandRegistry:
    def __init__(self):
        self._commands: Dict[str, Command] = {}

    def register(self, command_id: str, title: str, handler: Callable, shortcut: str = ""):
        if command_id in self._commands:
            raise ValueError(f"命令已注册: {command_id}")
        self._commands[command_id] = Command(command_id, title, handler, shortcut)

    def unregister(self, command_id: str):
        self._commands.pop(command_id, None)

    def get(self, command_id: str) -> Command:
        return self._commands[command_id]

    def all(self) -> List[Command]:
        return list(self._commands.values())

    def execute(self, command_id: str, *args, **kwargs):
        return self._commands[command_id].handler(*args, **kwargs)

    def search(self, query: str) -> List[Command]:
        """Subsequence (fuzzy) match over titles and ids, ranked by position."""
        q = query.lower().strip()
        if not q:
            return self.all()
        scored = []
        for cmd in self._commands.values():
            hay = (cmd.title + " " + cmd.id).lower()
            score = _subseq_score(q, hay)
            if score is not None:
                scored.append((score, cmd))
        scored.sort(key=lambda s: s[0])
        return [cmd for _s, cmd in scored]


def _subseq_score(query: str, text: str):
    """Return a score (lower=better) if query is a subsequence of text, else None."""
    pos = 0
    first = None
    for ch in query:
        idx = text.find(ch, pos)
        if idx == -1:
            return None
        if first is None:
            first = idx
        pos = idx + 1
    return (first, pos - first)  # prefer earlier + tighter matches
