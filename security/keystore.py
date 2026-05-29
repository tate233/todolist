"""Master-password verifier storage.

We never store the password. We store a small encrypted sentinel; if it
decrypts with the supplied password, the password is correct. The derived key
lives only in memory for the session.
"""
import json
import logging
from pathlib import Path

from security import crypto

logger = logging.getLogger(__name__)

_SENTINEL = "smart_notes_unlock_ok"


def is_initialized(keystore_path: Path) -> bool:
    return Path(keystore_path).exists()


def initialize(keystore_path: Path, password: str) -> None:
    """Create the verifier for a new master password."""
    token = crypto.encrypt(_SENTINEL, password)
    Path(keystore_path).write_text(json.dumps({"verifier": token}), encoding="utf-8")


def verify(keystore_path: Path, password: str) -> bool:
    """Return True if password unlocks the keystore."""
    try:
        data = json.loads(Path(keystore_path).read_text(encoding="utf-8"))
        return crypto.decrypt(data["verifier"], password) == _SENTINEL
    except (ValueError, KeyError, OSError):
        return False
    except Exception:
        logger.exception("校验主密码失败")
        return False
