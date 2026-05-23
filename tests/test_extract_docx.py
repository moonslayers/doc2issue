"""Tests para scripts/extract_docx.py."""
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from extract_docx import extract


def test_extract_docx_creates_manifest(test_docx, tmp_path):
    """Debe crear un manifest.json con la estructura correcta."""
    extract(str(test_docx), str(tmp_path))
    manifest_path = tmp_path / f"{test_docx.stem}.manifest.json"
    assert manifest_path.exists(), "manifest.json no fue creado"

    manifest = json.loads(manifest_path.read_text())
    assert manifest["source"] == str(test_docx)
    assert manifest["type"] == "docx"
    assert "markdown_file" in manifest
    assert "images" in manifest


def test_extract_docx_creates_markdown(test_docx, tmp_path):
    """Debe convertir el DOCX a markdown."""
    extract(str(test_docx), str(tmp_path))
    manifest = json.loads((tmp_path / f"{test_docx.stem}.manifest.json").read_text())

    md_path = Path(manifest["markdown_file"])
    assert md_path.exists(), "Archivo markdown no creado"
    content = md_path.read_text(encoding="utf-8")
    assert "Pagos" in content or "pagos" in content.lower(), (
        "El markdown debe contener el texto del documento"
    )


def test_extract_docx_handles_images(test_docx, tmp_path):
    """Debe manejar documentos con y sin imágenes sin errores."""
    extract(str(test_docx), str(tmp_path))
    manifest = json.loads((tmp_path / f"{test_docx.stem}.manifest.json").read_text())
    # No debe fallar aunque no tenga imágenes
    assert isinstance(manifest["images"], list)


def test_extract_docx_warnings_field(test_docx, tmp_path):
    """Debe incluir el campo warnings en el manifest."""
    extract(str(test_docx), str(tmp_path))
    manifest = json.loads((tmp_path / f"{test_docx.stem}.manifest.json").read_text())
    assert "warnings" in manifest
    assert isinstance(manifest["warnings"], list)
