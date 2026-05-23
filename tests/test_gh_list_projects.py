"""Tests para scripts/gh_list_projects.py."""
import sys
import json
import subprocess
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from gh_list_projects import list_projects


MOCK_PROJECTS = json.dumps({
    "projects": [
        {"number": 1, "title": "Sprint 24", "url": "https://github.com/orgs/test/projects/1", "closed": False},
        {"number": 2, "title": "Backlog", "url": "https://github.com/orgs/test/projects/2", "closed": False},
        {"number": 3, "title": "Done Q1", "url": "https://github.com/orgs/test/projects/3", "closed": True},
    ]
})


def test_list_projects_with_owner():
    """Debe listar projects del owner."""
    with patch.object(subprocess, "run") as mock_run:
        mock_run.return_value.stdout = MOCK_PROJECTS
        mock_run.return_value.returncode = 0

        projects = list_projects("testorg")
        assert len(projects) == 3
        assert projects[0]["number"] == 1
        assert projects[0]["title"] == "Sprint 24"
        assert projects[2]["is_closed"] is True


def test_list_projects_with_repo():
    """Listar projects de un repo específico."""
    with patch.object(subprocess, "run") as mock_run:
        mock_run.return_value.stdout = MOCK_PROJECTS
        mock_run.return_value.returncode = 0

        projects = list_projects("testuser", "doc2issue")
        assert len(projects) == 3
        # Verificar que el comando incluye --repo
        args = mock_run.call_args[0][0]
        assert "--repo" in args
        assert any("doc2issue" in a for a in args), "doc2issue debe estar en los args"


def test_list_projects_empty():
    """Owner sin projects debe retornar lista vacía."""
    with patch.object(subprocess, "run") as mock_run:
        mock_run.return_value.stdout = json.dumps({"projects": []})
        mock_run.return_value.returncode = 0

        projects = list_projects("testuser")
        assert projects == []


def test_list_projects_gh_error():
    """Error de gh debe propagar CalledProcessError."""
    with patch.object(subprocess, "run") as mock_run:
        mock_run.side_effect = subprocess.CalledProcessError(1, [], stderr="not found")
        try:
            list_projects("testuser")
            assert False, "Debió lanzar error"
        except subprocess.CalledProcessError:
            pass
