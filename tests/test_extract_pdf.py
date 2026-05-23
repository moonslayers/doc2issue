"""Tests para scripts/extract_pdf.py."""
import sys
import json
from pathlib import Path

# Agregar scripts/ al path para importar sin ejecutar __main__
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from extract_pdf import extract


def test_extract_pdf_creates_manifest(test_pdf, tmp_path):
    """Debe crear un manifest.json con la estructura correcta."""
    extract(str(test_pdf), str(tmp_path))
    manifest_path = tmp_path / f"{test_pdf.stem}.manifest.json"
    assert manifest_path.exists(), "manifest.json no fue creado"

    manifest = json.loads(manifest_path.read_text())
    assert manifest["source"] == str(test_pdf)
    assert manifest["type"] == "pdf"
    assert manifest["pages"] >= 1
    assert "text_file" in manifest
    assert "images" in manifest


def test_extract_pdf_creates_text_file(test_pdf, tmp_path):
    """Debe extraer el texto del PDF."""
    extract(str(test_pdf), str(tmp_path))
    manifest = json.loads((tmp_path / f"{test_pdf.stem}.manifest.json").read_text())

    txt_path = Path(manifest["text_file"])
    assert txt_path.exists(), "Archivo de texto no creado"
    content = txt_path.read_text(encoding="utf-8")
    assert "Login" in content, "El texto extraído debe contener el contenido del PDF"


def test_extract_pdf_creates_images(test_pdf, tmp_path):
    """Debe extraer imágenes incrustadas del PDF."""
    extract(str(test_pdf), str(tmp_path))
    manifest = json.loads((tmp_path / f"{test_pdf.stem}.manifest.json").read_text())

    assert len(manifest["images"]) > 0, "Debe extraer al menos una imagen"
    for img_path_str in manifest["images"]:
        img_path = Path(img_path_str)
        assert img_path.exists(), f"Imagen {img_path} no encontrada"


def test_extract_pdf_creates_images_folder(test_pdf, tmp_path):
    """Debe crear la carpeta images/ dentro del output."""
    extract(str(test_pdf), str(tmp_path))
    images_dir = tmp_path / "images"
    assert images_dir.exists(), "Carpeta images/ no fue creada"


def test_extract_pdf_char_count_matches(test_pdf, tmp_path):
    """El char_count debe coincidir con la longitud del texto extraído."""
    extract(str(test_pdf), str(tmp_path))
    manifest = json.loads((tmp_path / f"{test_pdf.stem}.manifest.json").read_text())

    txt_path = Path(manifest["text_file"])
    content = txt_path.read_text(encoding="utf-8")
    assert manifest["char_count"] == len(content), "char_count no coincide"
