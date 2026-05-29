"""Image attachment helpers: PNG persistence and markdown reference building."""
import pytest

from attachments import AttachmentManager

PIL = pytest.importorskip("PIL")
from PIL import Image  # noqa: E402


def test_add_image_persists_png(tmp_path):
    am = AttachmentManager(tmp_path / "att")
    img = Image.new("RGB", (4, 4), (255, 0, 0))
    name = am.add_image(img, "note1")
    assert name.endswith(".png")
    assert am.path_for(name).exists()
    assert "note1" in am.refs[name]


def test_add_image_dedup(tmp_path):
    am = AttachmentManager(tmp_path / "att")
    img = Image.new("RGB", (4, 4), (0, 128, 0))
    assert am.add_image(img, "a") == am.add_image(img, "b")  # same content


def test_markdown_reference_image_vs_file():
    assert AttachmentManager.markdown_reference("abc.png", "x") == "![x](attachments/abc.png)"
    assert AttachmentManager.markdown_reference("doc.pdf", "y") == "[y](attachments/doc.pdf)"
