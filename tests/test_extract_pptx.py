"""Tests para scripts/extract_pptx.py."""
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from extract_pptx import extract


def test_extract_pptx_creates_manifest(test_pptx, tmp_path):
    """Debe crear un manifest.json con la estructura correcta."""
    extract(str(test_pptx), str(tmp_path))
    manifest_path = tmp_path / f"{test_pptx.stem}.manifest.json"
    assert manifest_path.exists(), "manifest.json no fue creado"

    manifest = json.loads(manifest_path.read_text())
    assert manifest["source"] == str(test_pptx)
    assert manifest["type"] == "pptx"
    assert manifest["slides"] >= 1
    assert "markdown_file" in manifest


def test_extract_pptx_creates_markdown(test_pptx, tmp_path):
    """Debe generar un markdown con el texto de los slides."""
    extract(str(test_pptx), str(tmp_path))
    manifest = json.loads((tmp_path / f"{test_pptx.stem}.manifest.json").read_text())

    md_path = Path(manifest["markdown_file"])
    assert md_path.exists(), "Archivo markdown no creado"
    content = md_path.read_text(encoding="utf-8")
    assert "Dashboard" in content or "Arquitectura" in content, (
        "Debe contener los títulos de los slides"
    )


def test_extract_pptx_slide_count(test_pptx, tmp_path):
    """El conteo de slides debe ser correcto."""
    extract(str(test_pptx), str(tmp_path))
    manifest = json.loads((tmp_path / f"{test_pptx.stem}.manifest.json").read_text())
    assert manifest["slides"] == 2, "El PPTX de prueba tiene 2 slides"


def test_extract_pptx_notes_included(test_pptx, tmp_path):
    """Las notas del presentador deben estar incluidas en el markdown."""
    extract(str(test_pptx), str(tmp_path))
    manifest = json.loads((tmp_path / f"{test_pptx.stem}.manifest.json").read_text())

    md_path = Path(manifest["markdown_file"])
    content = md_path.read_text(encoding="utf-8")
    assert "microservicios" in content or "Notas" in content, (
        "Las notas del presentador deben aparecer en el markdown"
    )


def test_extract_pptx_images_list(test_pptx, tmp_path):
    """Debe incluir la lista de imágenes en el manifest."""
    extract(str(test_pptx), str(tmp_path))
    manifest = json.loads((tmp_path / f"{test_pptx.stem}.manifest.json").read_text())
    assert "images" in manifest
    assert isinstance(manifest["images"], list)
