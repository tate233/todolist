"""Optional content encryption.

Uses the well-reviewed ``cryptography`` library (Fernet = AES-128-CBC + HMAC)
with a PBKDF2-HMAC-SHA256 derived key — we never roll our own cipher. The
feature is optional: if ``cryptography`` is not installed, ``is_available`` is
False and the app stays in plaintext mode.

Format of an encrypted blob (base64 text):
    "ENC1:" + base64(salt(16) + fernet_token)
"""
import base64
import os

PREFIX = "ENC1:"
_PBKDF2_ITERATIONS = 200_000
_SALT_LEN = 16


def is_available() -> bool:
    try:
        import cryptography  # noqa: F401,PLC0415
    except ImportError:
        return False
    return True


def _fernet_for(password: str, salt: bytes):
    from cryptography.fernet import Fernet  # noqa: PLC0415
    from cryptography.hazmat.primitives import hashes  # noqa: PLC0415
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC  # noqa: PLC0415

    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt,
                     iterations=_PBKDF2_ITERATIONS)
    key = base64.urlsafe_b64encode(kdf.derive(password.encode("utf-8")))
    return Fernet(key)


def is_encrypted(text: str) -> bool:
    return isinstance(text, str) and text.startswith(PREFIX)


def encrypt(plaintext: str, password: str) -> str:
    if not is_available():
        raise RuntimeError("加密不可用：未安装 cryptography")
    salt = os.urandom(_SALT_LEN)
    token = _fernet_for(password, salt).encrypt(plaintext.encode("utf-8"))
    return PREFIX + base64.urlsafe_b64encode(salt + token).decode("ascii")


def decrypt(blob: str, password: str) -> str:
    if not is_encrypted(blob):
        return blob  # not encrypted; return as-is
    from cryptography.fernet import InvalidToken  # noqa: PLC0415
    raw = base64.urlsafe_b64decode(blob[len(PREFIX):].encode("ascii"))
    salt, token = raw[:_SALT_LEN], raw[_SALT_LEN:]
    try:
        return _fernet_for(password, salt).decrypt(token).decode("utf-8")
    except InvalidToken as e:
        raise ValueError("主密码错误或数据损坏") from e
