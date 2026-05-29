"""Filesystem sync backend — useful for testing and local folder sync."""
import json
from pathlib import Path
from typing import List, Tuple

from sync.base import SyncBackend

_META = "_mtimes.json"


class LocalSyncBackend(SyncBackend):
    def __init__(self, root: Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def _meta(self):
        p = self.root / _META
        if p.exists():
            try:
                return json.loads(p.read_text(encoding="utf-8"))
            except Exception:
                return {}
        return {}

    def _save_meta(self, meta):
        (self.root / _META).write_text(json.dumps(meta), encoding="utf-8")

    def upload(self, key: str, data: bytes, mtime: float) -> None:
        (self.root / key).write_bytes(data)
        meta = self._meta()
        meta[key] = mtime
        self._save_meta(meta)

    def download(self, key: str) -> Tuple[bytes, float]:
        path = self.root / key
        if not path.exists():
            raise KeyError(key)
        return path.read_bytes(), self.get_mtime(key)

    def list_keys(self) -> List[str]:
        return [p.name for p in self.root.iterdir() if p.is_file() and p.name != _META]

    def get_mtime(self, key: str) -> float:
        return self._meta().get(key, -1.0)
