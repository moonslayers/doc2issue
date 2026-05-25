"""Tests para scripts/merge_vision.py."""
import sys, json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from merge_vision import merge


def test_merge_basic(tmp_path):
    """Debe asignar analysis a cada imagen que tenga vision JSON."""
    manifest = {
        "source": "test.pdf",
        "images": [
            {"path": str(tmp_path / "slides" / "doc_slide_001.png"), "caption": "Slide 1"},
            {"path": str(tmp_path / "slides" / "doc_slide_002.png"), "caption": "Slide 2"},
        ]
    }
    manifest_path = tmp_path / "manifest.json"
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f)

    # Crear JSONs de vision
    (tmp_path / "slides").mkdir()
    vision_1 = {"type": "full_slide", "text_in_image": "Texto slide 1"}
    vision_2 = {"type": "full_slide", "text_in_image": "Texto slide 2"}
    v1_path = tmp_path / "slides" / "doc_slide_001.json"
    v2_path = tmp_path / "slides" / "doc_slide_002.json"
    with open(v1_path, 'w') as f:
        json.dump(vision_1, f)
    with open(v2_path, 'w') as f:
        json.dump(vision_2, f)

    result = merge(str(manifest_path), [str(v1_path), str(v2_path)])
    assert result["vision_enriched"] == 2
    for img in result["images"]:
        assert "analysis" in img
        parsed = json.loads(img["analysis"])
        assert "text_in_image" in parsed


def test_merge_no_vision_jsons(tmp_path):
    """Sin JSONs de vision, debe dejar analysis vacío."""
    manifest = {
        "source": "test.pdf",
        "images": [{"path": "slide_001.png", "caption": "Slide 1"}],
    }
    manifest_path = tmp_path / "manifest.json"
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f)

    result = merge(str(manifest_path), [])
    assert result["vision_enriched"] == 0
    assert "analysis" not in result["images"][0]


def test_merge_no_images(tmp_path):
    """Manifest sin imágenes no debe fallar."""
    manifest = {"source": "test.pdf", "images": []}
    manifest_path = tmp_path / "manifest.json"
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f)

    result = merge(str(manifest_path), ["some.json"])
    assert result["vision_enriched"] == 0
