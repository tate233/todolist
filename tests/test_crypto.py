"""Encryption round-trip, wrong-password rejection, and keystore verify.

Round-trip tests are skipped if the optional 'cryptography' extra is absent.
"""
import pytest

from security import crypto, keystore

requires_crypto = pytest.mark.skipif(not crypto.is_available(),
                                     reason="cryptography not installed")


def test_is_encrypted_detection():
    assert not crypto.is_encrypted("plain text")
    assert crypto.is_encrypted("ENC1:abc")


@requires_crypto
def test_encrypt_decrypt_roundtrip():
    secret = "私密笔记内容 with unicode 🔒"
    blob = crypto.encrypt(secret, "correct horse")
    assert crypto.is_encrypted(blob)
    assert "私密" not in blob  # ciphertext does not leak plaintext
    assert crypto.decrypt(blob, "correct horse") == secret


@requires_crypto
def test_wrong_password_rejected():
    blob = crypto.encrypt("data", "right")
    with pytest.raises(ValueError):
        crypto.decrypt(blob, "wrong")


@requires_crypto
def test_decrypt_passthrough_for_plaintext():
    assert crypto.decrypt("not encrypted", "any") == "not encrypted"


@requires_crypto
def test_keystore_init_and_verify(tmp_path):
    ks = tmp_path / "keystore.json"
    assert not keystore.is_initialized(ks)
    keystore.initialize(ks, "master-pw")
    assert keystore.is_initialized(ks)
    assert keystore.verify(ks, "master-pw") is True
    assert keystore.verify(ks, "bad-pw") is False
