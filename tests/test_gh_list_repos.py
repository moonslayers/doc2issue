"""Tests para scripts/gh_list_repos.py."""
import sys
import json
import subprocess
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from gh_list_repos import list_repos, get_owner


MOCK_REPOS = json.dumps([
    {
        "name": "doc2issue",
        "owner": {"login": "testuser"},
        "url": "https://github.com/testuser/doc2issue",
        "description": "Convert docs to issues",
        "isPrivate": False,
        "updatedAt": "2025-01-01T00:00:00Z",
        "primaryLanguage": {"name": "Python"},
    },
    {
        "name": "otro-repo",
        "owner": {"login": "testuser"},
        "url": "https://github.com/testuser/otro-repo",
        "description": None,
        "isPrivate": True,
        "updatedAt": None,
        "primaryLanguage": None,
    },
])


def test_list_repos_with_owner():
    """Debe listar repos y estandarizar campos."""
    with patch.object(subprocess, "run") as mock_run:
        mock_run.return_value.stdout = MOCK_REPOS
        mock_run.return_value.returncode = 0

        repos = list_repos("testuser")

        assert len(repos) == 2
        assert repos[0]["name"] == "doc2issue"
        assert repos[0]["full_name"] == "testuser/doc2issue"
        assert repos[0]["description"] == "Convert docs to issues"
        assert repos[0]["language"] == "Python"
        assert repos[1]["description"] is None or repos[1]["description"] == ""
        assert repos[1]["language"] is None or repos[1]["language"] == ""


def test_list_repos_none_owner_calls_get_owner():
    """Sin owner, debe llamar a get_owner primero."""
    with patch.object(subprocess, "run") as mock_run:
        # Primera llamada (get_owner)
        # Segunda llamada (gh repo list)
        mock_run.side_effect = [
            subprocess.CompletedProcess([], 0, stdout="testuser"),
            subprocess.CompletedProcess([], 0, stdout=MOCK_REPOS),
        ]
        repos = list_repos()
        assert len(repos) == 2
        assert mock_run.call_count == 2


def test_get_owner():
    """get_owner debe retornar el login del usuario."""
    with patch.object(subprocess, "run") as mock_run:
        mock_run.return_value.stdout = "testuser\n"
        mock_run.return_value.returncode = 0
        assert get_owner() == "testuser"


def test_list_repos_gh_not_found():
    """Si gh no está instalado, debe propagar FileNotFoundError."""
    with patch.object(subprocess, "run", side_effect=FileNotFoundError):
        try:
            list_repos("testuser")
            assert False, "Debió lanzar FileNotFoundError"
        except FileNotFoundError:
            pass
