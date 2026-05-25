"""Tests para scripts/gh_project_fields.py."""
import sys, json, subprocess
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from gh_project_fields import get_fields, _get_project_id


def test_get_project_id_user():
    with patch.object(subprocess, "run") as mock_run:
        mock_run.return_value.stdout = "PVT_user\n"
        mock_run.return_value.returncode = 0
        assert _get_project_id("testuser", 1) == "PVT_user"


def test_get_project_id_fallback():
    with patch.object(subprocess, "run") as mock_run:
        mock_run.side_effect = [
            subprocess.CompletedProcess([], 0, stdout=""),
            subprocess.CompletedProcess([], 0, stdout="PVT_org"),
        ]
        assert _get_project_id("testorg", 1) == "PVT_org"


MOCK_FIELDS = json.dumps({
    "fields": {
        "nodes": [
            {"__typename": "ProjectV2SingleSelectField", "id": "f1", "name": "Status",
             "options": [{"id": "o1", "name": "Todo"}, {"id": "o2", "name": "In Progress"}]},
            {"__typename": "ProjectV2SingleSelectField", "id": "f2", "name": "Priority",
             "options": [{"id": "o3", "name": "P0"}, {"id": "o4", "name": "P1"}]},
            {"__typename": "ProjectV2Field", "id": "f3", "name": "Estimate"},
            {"__typename": "ProjectV2IterationField", "id": "f4", "name": "Iteration"},
        ]
    },
    "number": 2,
    "title": "Test Project",
})


def test_get_fields_structure():
    with patch.object(subprocess, "run") as mock_run:
        # project ID + fields query
        mock_run.side_effect = [
            subprocess.CompletedProcess([], 0, stdout="PVT_test"),
            subprocess.CompletedProcess([], 0, stdout=MOCK_FIELDS),
        ]
        result = get_fields("testuser", 2)
        assert result["project"]["number"] == 2
        assert "fields" in result


def test_get_fields_single_select():
    with patch.object(subprocess, "run") as mock_run:
        mock_run.side_effect = [
            subprocess.CompletedProcess([], 0, stdout="PVT_test"),
            subprocess.CompletedProcess([], 0, stdout=MOCK_FIELDS),
        ]
        result = get_fields("testuser", 2)
        status = result["fields"].get("Status", {})
        assert status["type"] == "single_select"
        assert "Todo" in status["options"]
        assert "In Progress" in status["options"]


def test_get_fields_estimate_is_number():
    with patch.object(subprocess, "run") as mock_run:
        mock_run.side_effect = [
            subprocess.CompletedProcess([], 0, stdout="PVT_test"),
            subprocess.CompletedProcess([], 0, stdout=MOCK_FIELDS),
        ]
        result = get_fields("testuser", 2)
        assert result["fields"]["Estimate"]["type"] == "number"


def test_get_fields_iteration():
    with patch.object(subprocess, "run") as mock_run:
        mock_run.side_effect = [
            subprocess.CompletedProcess([], 0, stdout="PVT_test"),
            subprocess.CompletedProcess([], 0, stdout=MOCK_FIELDS),
        ]
        result = get_fields("testuser", 2)
        assert result["fields"]["Iteration"]["type"] == "iteration"
