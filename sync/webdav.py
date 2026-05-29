"""WebDAV sync backend (requires the optional 'requests' dependency).

Thin adapter over WebDAV PUT/GET/PROPFIND. Import-safe without requests;
``is_available`` reports whether the dependency is present.
"""
from typing import List, Tuple

from sync.base import SyncBackend


def is_available() -> bool:
    try:
        import requests  # noqa: F401,PLC0415
    except ImportError:
        return False
    return True


class WebDAVBackend(SyncBackend):
    def __init__(self, base_url: str, username: str = "", password: str = ""):
        if not is_available():
            raise RuntimeError("WebDAV 后端需要安装 requests")
        import requests  # noqa: PLC0415
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        if username:
            self.session.auth = (username, password)

    def _url(self, key: str) -> str:
        return f"{self.base_url}/{key}"

    def upload(self, key: str, data: bytes, mtime: float) -> None:
        self.session.put(self._url(key), data=data,
                         headers={"X-OC-Mtime": str(int(mtime))})

    def download(self, key: str) -> Tuple[bytes, float]:
        resp = self.session.get(self._url(key))
        if resp.status_code == 404:
            raise KeyError(key)
        resp.raise_for_status()
        return resp.content, self.get_mtime(key)

    def list_keys(self) -> List[str]:
        # PROPFIND parsing is server-specific; left for deployment configuration.
        raise NotImplementedError("WebDAV list_keys depends on server PROPFIND format")

    def get_mtime(self, key: str) -> float:
        resp = self.session.head(self._url(key))
        last_mod = resp.headers.get("Last-Modified")
        if not last_mod:
            return -1.0
        from email.utils import parsedate_to_datetime  # noqa: PLC0415
        try:
            return parsedate_to_datetime(last_mod).timestamp()
        except (TypeError, ValueError):
            return -1.0
