"""Atomic file writes.

Writing directly to the destination with open(path, 'w') leaves a truncated,
corrupt file if the process dies mid-write (and the previous good data is
already gone). These helpers write to a temporary file in the same directory,
flush+fsync it, then atomically ``os.replace`` it over the destination, so a
crash leaves either the old file or the fully-written new file — never a
half-written one.
"""
import json
import os
import tempfile
from pathlib import Path
from typing import Any, Union

PathLike = Union[str, Path]


def atomic_write_text(path: PathLike, text: str, encoding: str = "utf-8") -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=f".{path.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding=encoding) as f:
            f.write(text)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def atomic_write_json(path: PathLike, obj: Any, indent: int = 4) -> None:
    atomic_write_text(path, json.dumps(obj, indent=indent, ensure_ascii=False))
