"""Tests para scripts/gh_project_set_fields.py (GraphQL directo)."""
import sys, json, subprocess
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from gh_project_set_fields import _get_project_id, _get_issue_node_id, _get_project_fields


def test_get_project_id_user():
    """Debe encontrar project ID como usuario."""
    with patch.object(subprocess, "run") as mock_run:
        mock_run.return_value.stdout = "PVT_user_123\n"
        mock_run.return_value.returncode = 0
        pid = _get_project_id("testuser", 1)
        assert pid == "PVT_user_123"


def test_get_project_id_fallback_to_org():
    """Si user falla, debe intentar como org."""
    with patch.object(subprocess, "run") as mock_run:
        mock_run.side_effect = [
            subprocess.CompletedProcess([], 0, stdout=""),
            subprocess.CompletedProcess([], 0, stdout="PVT_org_456"),
        ]
        pid = _get_project_id("testorg", 1)
        assert pid == "PVT_org_456"


def test_get_issue_node_id():
    """Debe obtener node ID del issue."""
    with patch.object(subprocess, "run") as mock_run:
        mock_run.return_value.stdout = "I_kwDOBQKpns5ABC\n"
        mock_run.return_value.returncode = 0
        nid = _get_issue_node_id("testuser/repo", 123)
        assert nid == "I_kwDOBQKpns5ABC"


def test_get_project_fields():
    """Debe retornar lista de campos con tipos."""
    mock = json.dumps([
        {"__typename": "ProjectV2SingleSelectField", "id": "f1", "name": "Status",
         "options": [{"id": "o1", "name": "Todo"}, {"id": "o2", "name": "In Progress"}]},
        {"__typename": "ProjectV2Field", "id": "f2", "name": "Estimate"},
    ])
    with patch.object(subprocess, "run") as mock_run:
        mock_run.return_value.stdout = mock
        mock_run.return_value.returncode = 0
        fields = _get_project_fields("PVT_test")
        assert len(fields) == 2
        assert fields[0]["__typename"] == "ProjectV2SingleSelectField"
        assert fields[1]["name"] == "Estimate"
