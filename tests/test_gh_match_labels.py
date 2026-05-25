"""Tests para scripts/gh_match_labels.py."""
import sys, json, subprocess
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from gh_match_labels import match_labels, levenshtein, normalize


MOCK_LABELS = json.dumps([
    {"name": "bug", "description": "Bug report", "color": "d73a4a"},
    {"name": "feature", "description": "Nueva funcionalidad", "color": "a2eeef"},
    {"name": "mejoras", "description": "Mejora continua", "color": "7057ff"},
    {"name": "reportes", "description": "Reportes y dashboards", "color": "008672"},
    {"name": "apoyos", "description": "Apoyos económicos", "color": "0e8a16"},
])


def test_levenshtein():
    assert levenshtein("datos", "reportes") >= 4
    assert levenshtein("bug", "bug") == 0


def test_normalize():
    assert normalize("Créditos") == "creditos"
    assert normalize("Fondos BC") == "fondosbc"
    assert normalize("Alta") == "alta"


def test_match_exact():
    """Labels que existen exactamente deben matchear."""
    with patch.object(subprocess, "run") as mock_run:
        mock_run.return_value.stdout = MOCK_LABELS
        mock_run.return_value.returncode = 0
        result = match_labels(["bug", "feature"], "test/repo")
        assert result["matched"]["bug"] == "bug"
        assert result["matched"]["feature"] == "feature"
        assert result["unmatched"] == []


def test_match_fuzzy():
    """Labels similares deben matchear por similitud."""
    with patch.object(subprocess, "run") as mock_run:
        mock_run.return_value.stdout = MOCK_LABELS
        mock_run.return_value.returncode = 0
        # "reportes" debería matchear con "reporte" (sin s)
        result = match_labels(["reporte", "apoyo"], "test/repo")
        assert result["matched"]["reporte"] in ("reportes",)
        assert result["matched"]["apoyo"] in ("apoyos",)


def test_match_unmatched():
    """Labels sin similitud deben quedar en unmatched."""
    with patch.object(subprocess, "run") as mock_run:
        mock_run.return_value.stdout = MOCK_LABELS
        mock_run.return_value.returncode = 0
        result = match_labels(["xyz123"], "test/repo")
        assert "xyz123" in result["unmatched"]


def test_all_found_deduplicated():
    """all_found no debe tener duplicados."""
    with patch.object(subprocess, "run") as mock_run:
        mock_run.return_value.stdout = MOCK_LABELS
        mock_run.return_value.returncode = 0
        result = match_labels(["bug", "bug"], "test/repo")
        assert len(result["all_found"]) == 1


def test_threshold_effect():
    """Con threshold más alto, menos matches."""
    with patch.object(subprocess, "run") as mock_run:
        mock_run.return_value.stdout = MOCK_LABELS
        mock_run.return_value.returncode = 0
        result = match_labels(["bug"], "test/repo", threshold=0.9)
        assert result["matched"]["bug"] == "bug"
