"""Backend-agnostic sync interface and timestamp conflict resolution.

A SyncBackend is a simple key->(bytes, mtime) store. The merge policy is
last-writer-wins by modification time, with conflicts recorded for visibility.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Tuple


class SyncBackend(ABC):
    @abstractmethod
    def upload(self, key: str, data: bytes, mtime: float) -> None: ...

    @abstractmethod
    def download(self, key: str) -> Tuple[bytes, float]:
        """Return (data, mtime); raise KeyError if absent."""

    @abstractmethod
    def list_keys(self) -> List[str]: ...

    @abstractmethod
    def get_mtime(self, key: str) -> float:
        """Return mtime, or -1.0 if the key is absent."""


@dataclass
class SyncResult:
    uploaded: List[str] = field(default_factory=list)
    downloaded: List[str] = field(default_factory=list)
    conflicts: List[str] = field(default_factory=list)


def sync(local: Dict[str, Tuple[bytes, float]], backend: SyncBackend) -> SyncResult:
    """Two-way sync local {key: (data, mtime)} with a backend (last-writer-wins).

    Returns a SyncResult; mutates ``local`` in place for downloaded keys.
    """
    result = SyncResult()
    remote_keys = set(backend.list_keys())
    local_keys = set(local)

    # keys only local -> upload
    for key in local_keys - remote_keys:
        data, mtime = local[key]
        backend.upload(key, data, mtime)
        result.uploaded.append(key)

    # keys only remote -> download
    for key in remote_keys - local_keys:
        data, mtime = backend.download(key)
        local[key] = (data, mtime)
        result.downloaded.append(key)

    # keys in both -> resolve by mtime
    for key in local_keys & remote_keys:
        l_data, l_mtime = local[key]
        r_mtime = backend.get_mtime(key)
        if l_mtime > r_mtime:
            backend.upload(key, l_data, l_mtime)
            result.uploaded.append(key)
        elif r_mtime > l_mtime:
            data, mtime = backend.download(key)
            local[key] = (data, mtime)
            result.downloaded.append(key)
            result.conflicts.append(key)
    return result
