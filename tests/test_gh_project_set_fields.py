"""Tests para scripts/gh_project_set_fields.py."""
import sys, json, subprocess
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from gh_project_set_fields import _get_project_id, _get_field_option_id


MOCK_PROJECT_FIELDS = json.dumps([
                    {
                        "id": "field_status",
                        "name": "Status",
                        "options": [
                            {"id": "opt_todo", "name": "Todo"},
                            {"id": "opt_progress", "name": "In Progress"},
                            {"id": "opt_done", "name": "Done"},
                        ]
                    },
                    {
                        "id": "field_priority",
                        "name": "Priority",
                        "options": [
                            {"id": "opt_high", "name": "High"},
                            {"id": "opt_medium", "name": "Medium"},
                            {"id": "opt_low", "name": "Low"},
                        ]
                    }
])


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
        # user falla (stdout vacío), org funciona
        mock_run.side_effect = [
            subprocess.CompletedProcess([], 0, stdout=""),
            subprocess.CompletedProcess([], 0, stdout="PVT_org_456"),
        ]
        pid = _get_project_id("testorg", 1)
        assert pid == "PVT_org_456"


def test_get_field_option_id_exact():
    """Debe encontrar option ID por match exacto."""
    with patch.object(subprocess, "run") as mock_run:
        mock_run.return_value.stdout = MOCK_PROJECT_FIELDS
        mock_run.return_value.returncode = 0
        opt_id = _get_field_option_id("proj_id", "Status", "In Progress")
        assert opt_id == "opt_progress"


def test_get_field_option_id_case_insensitive():
    """Debe ser case-insensitive."""
    with patch.object(subprocess, "run") as mock_run:
        mock_run.return_value.stdout = MOCK_PROJECT_FIELDS
        mock_run.return_value.returncode = 0
        opt_id = _get_field_option_id("proj_id", "status", "in progress")
        assert opt_id == "opt_progress"


def test_get_field_option_id_not_found():
    """Campo/valor inexistente debe retornar None."""
    with patch.object(subprocess, "run") as mock_run:
        mock_run.return_value.stdout = MOCK_PROJECT_FIELDS
        mock_run.return_value.returncode = 0
        opt_id = _get_field_option_id("proj_id", "Status", "NonExistent")
        assert opt_id is None
