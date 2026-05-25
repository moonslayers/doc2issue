"""Tests para scripts/validate_issue.py."""
import sys, json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from validate_issue import validate


def _make_issue(overrides: dict = None) -> dict:
    """Crea un issue.json válido base."""
    issue = {
        "title": "Feature Login",
        "description": "Implementar login con OAuth",
        "target_repo": "owner/repo",
        "target_project": 2,
        "labels_resolved": ["bug", "feature"],
        "priority_resolved": "High",
        "size": "M",
        "estimate_hours": 16,
        "status": "Todo",
        "images": [
            {"path": "slide_001.png", "caption": "Slide 1"},
        ],
        "references": [],
    }
    if overrides:
        issue.update(overrides)
    return issue


def test_valid_issue(tmp_path):
    """Issue válido no debe generar errores."""
    p = tmp_path / "valid.json"
    with open(p, 'w') as f:
        json.dump(_make_issue(), f)
    assert validate(str(p)) == []


def test_missing_title(tmp_path):
    """Sin title debe dar error."""
    p = tmp_path / "no_title.json"
    with open(p, 'w') as f:
        json.dump(_make_issue({"title": ""}), f)
    errs = validate(str(p))
    assert any("title" in e for e in errs)


def test_missing_required(tmp_path):
    """Sin campos requeridos debe dar errores."""
    p = tmp_path / "missing.json"
    with open(p, 'w') as f:
        json.dump({}, f)
    errs = validate(str(p))
    for field in ["title", "description", "target_repo"]:
        assert any(field in e for e in errs), f"Falta error para {field}"


def test_invalid_priority(tmp_path):
    """Prioridad inválida debe dar error."""
    p = tmp_path / "bad_prio.json"
    with open(p, 'w') as f:
        json.dump(_make_issue({"priority_resolved": "urgentíiiiisimo"}), f)
    errs = validate(str(p))
    assert any("priority" in e.lower() for e in errs)


def test_invalid_size(tmp_path):
    """Size inválido debe dar error."""
    p = tmp_path / "bad_size.json"
    with open(p, 'w') as f:
        json.dump(_make_issue({"size": "gigante"}), f)
    errs = validate(str(p))
    assert any("size" in e.lower() for e in errs)


def test_bad_repo_format(tmp_path):
    """target_repo sin '/' debe dar error."""
    p = tmp_path / "bad_repo.json"
    with open(p, 'w') as f:
        json.dump(_make_issue({"target_repo": "solounnombre"}), f)
    errs = validate(str(p))
    assert any("target_repo" in e for e in errs)


def test_images_missing_caption(tmp_path):
    """Imagen sin caption debe dar error."""
    p = tmp_path / "no_caption.json"
    with open(p, 'w') as f:
        json.dump(_make_issue({"images": [{"path": "img.png", "caption": ""}]}), f)
    errs = validate(str(p))
    assert any("caption" in e for e in errs)


def test_placeholder_title(tmp_path):
    """Title con {{...}} sin reemplazar debe dar error."""
    p = tmp_path / "placeholder.json"
    with open(p, 'w') as f:
        json.dump(_make_issue({"title": "{{title}}"}), f)
    errs = validate(str(p))
    assert any("placeholder" in e for e in errs)
