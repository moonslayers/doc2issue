"""Tests para scripts/embed_images.py (data URIs + template)."""
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from embed_images import embed_images, render_template


# ---------------------------------------------------------------------------
# Tests: embed_images (conversión de rutas a data URIs)
# ---------------------------------------------------------------------------

def test_embed_images_converts_path_to_data_uri(tmp_path):
    """Una imagen existente debe convertirse a data URI."""
    img_path = tmp_path / "test.png"
    img_path.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 20)  # PNG mínimo

    data = {"images": [{"path": str(img_path), "caption": "Test"}]}
    result = embed_images(data)

    uri = result["images"][0]["path"]
    assert uri.startswith("data:image/png;base64,"), (
        f"Debe empezar con data URI, obtenido: {uri[:50]}"
    )


def test_embed_images_missing_image_leaves_empty(tmp_path):
    """Una imagen que no existe debe quedar con path vacío."""
    data = {"images": [{"path": "/no/existe.png", "caption": "Test"}]}
    result = embed_images(data)
    assert result["images"][0]["path"] == "", "Path debe quedar vacío"


def test_embed_images_no_images(tmp_path):
    """Sin imágenes, el dict no debe modificarse."""
    data = {"title": "Test", "images": []}
    result = embed_images(data)
    assert result["images"] == []


def test_embed_images_multiple_images(tmp_path):
    """Múltiples imágenes deben procesarse todas."""
    paths = []
    for i in range(3):
        p = tmp_path / f"img_{i}.png"
        p.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 20)
        paths.append(str(p))

    data = {"images": [{"path": p, "caption": f"Img {i}"} for i, p in enumerate(paths)]}
    result = embed_images(data)

    assert all(r["path"].startswith("data:") for r in result["images"])


# ---------------------------------------------------------------------------
# Tests: render_template (Mustache mínimo)
# ---------------------------------------------------------------------------

SAMPLE_TEMPLATE = """# {{title}}

## Descripción
{{description}}

## Criterios de Aceptación
{{#acceptance_criteria}}
- [ ] {{.}}
{{/acceptance_criteria}}

## Imágenes / Mockups
{{#images}}
### {{caption}}
![{{caption}}]({{path}})
{{/images}}

## Metadata
- **Prioridad**: {{priority}}
"""


def test_render_simple_variable():
    """Las variables simples {{var}} deben reemplazarse."""
    data = {"title": "Mi Issue", "description": "Test desc", "priority": "alta"}
    result = render_template(SAMPLE_TEMPLATE, data)
    assert "# Mi Issue" in result
    assert "Test desc" in result
    assert "alta" in result


def test_render_list_simple():
    """La lista {{#list}}{{.}}{{/list}} debe iterar."""
    data = {
        "title": "T",
        "description": "D",
        "priority": "P",
        "acceptance_criteria": ["AC1", "AC2", "AC3"],
        "images": [],
    }
    result = render_template(SAMPLE_TEMPLATE, data)
    assert "- [ ] AC1" in result
    assert "- [ ] AC2" in result
    assert "- [ ] AC3" in result


def test_render_list_objects():
    """La lista de objetos {{#images}}{{field}}{{/images}} debe funcionar."""
    data = {
        "title": "T",
        "description": "D",
        "priority": "P",
        "acceptance_criteria": [],
        "images": [
            {"caption": "Mockup 1", "path": "data:image/png;base64,abc"},
            {"caption": "Mockup 2", "path": "data:image/png;base64,def"},
        ],
    }
    result = render_template(SAMPLE_TEMPLATE, data)
    assert "Mockup 1" in result
    assert "Mockup 2" in result
    assert "data:image/png;base64,abc" in result
    assert "data:image/png;base64,def" in result


def test_render_empty_list():
    """Una lista vacía debe omitir los items pero el heading del template se mantiene."""
    data = {
        "title": "T",
        "description": "D",
        "priority": "P",
        "acceptance_criteria": [],
        "images": [],
    }
    result = render_template(SAMPLE_TEMPLATE, data)
    # El heading está fuera de {{#list}}...{{/list}}, se mantiene
    assert "Criterios de Aceptación" in result
    assert "Imágenes / Mockups" in result
    # Pero no debe haber items renderizados
    assert "- [ ]" not in result
    assert "data:image" not in result


def test_render_missing_variable_leaves_placeholder():
    """Variables no provistas deben quedar como {{var}}."""
    data = {"title": "T", "description": "D"}  # sin priority
    result = render_template(SAMPLE_TEMPLATE, data)
    assert "{{priority}}" in result
