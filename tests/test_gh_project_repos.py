"""Tests para scripts/gh_project_repos.py."""
import sys
import json
import subprocess
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from gh_project_repos import project_repos


# ── Mock: gh project view (paso 1) ────────────────────────────────
MOCK_VIEW = json.dumps({
    "id": "PVT_kwHOBQKpns4A9lsF",
    "title": "Desarrollo SEI",
    "url": "https://github.com/users/test/projects/2",
    "items": {"totalCount": 5},
})

# ── Mock: GraphQL con items (paso 2) ──────────────────────────────
def _make_graphql_response(nodes: list) -> str:
    return json.dumps({
        "data": {
            "node": {
                "items": {
                    "totalCount": len(nodes),
                    "pageInfo": {"hasNextPage": False, "endCursor": None},
                    "nodes": nodes,
                }
            }
        }
    })


MOCK_ITEMS_MIXED = _make_graphql_response([
    {
        "content": {
            "__typename": "Issue",
            "title": "Bug en login",
            "repository": {"nameWithOwner": "testuser/backend"},
            "state": "open",
            "updatedAt": "2026-05-20T00:00:00Z",
        }
    },
    {
        "content": {
            "__typename": "PullRequest",
            "title": "Fix navbar",
            "repository": {"nameWithOwner": "testuser/frontend"},
            "state": "merged",
            "updatedAt": "2026-05-25T00:00:00Z",
        }
    },
    {
        "content": {
            "__typename": "Issue",
            "title": "API docs",
            "repository": {"nameWithOwner": "testuser/backend"},
            "state": "closed",
            "updatedAt": "2026-05-15T00:00:00Z",
        }
    },
    {
        "content": {
            "__typename": "DraftIssue",
            "title": "Idea para feature X",
        }
    },
    {
        "content": None,
    },
])

MOCK_ITEMS_EMPTY = _make_graphql_response([])


def test_repos_structure():
    """Debe retornar la estructura esperada."""
    with patch.object(subprocess, "run") as mock_run:
        mock_run.side_effect = [
            subprocess.CompletedProcess([], 0, stdout=MOCK_VIEW),
            subprocess.CompletedProcess([], 0, stdout=MOCK_ITEMS_MIXED),
        ]

        result = project_repos(2, "@me")

        assert result["project"]["title"] == "Desarrollo SEI"
        assert "repos" in result
        assert "draft_issues" in result


def test_repos_grouped_correctly():
    """Items del mismo repo deben agruparse."""
    with patch.object(subprocess, "run") as mock_run:
        mock_run.side_effect = [
            subprocess.CompletedProcess([], 0, stdout=MOCK_VIEW),
            subprocess.CompletedProcess([], 0, stdout=MOCK_ITEMS_MIXED),
        ]

        result = project_repos(2, "@me")
        repo_map = {r["full_name"]: r for r in result["repos"]}

        assert "testuser/backend" in repo_map
        assert repo_map["testuser/backend"]["item_count"] == 2
        assert repo_map["testuser/backend"]["issues"] == 2
        assert repo_map["testuser/backend"]["pull_requests"] == 0

        assert "testuser/frontend" in repo_map
        assert repo_map["testuser/frontend"]["item_count"] == 1
        assert repo_map["testuser/frontend"]["pull_requests"] == 1


def test_repos_draft_count():
    """Draft Issues deben contarse por separado."""
    with patch.object(subprocess, "run") as mock_run:
        mock_run.side_effect = [
            subprocess.CompletedProcess([], 0, stdout=MOCK_VIEW),
            subprocess.CompletedProcess([], 0, stdout=MOCK_ITEMS_MIXED),
        ]

        result = project_repos(2, "@me")
        assert result["draft_issues"] == 1


def test_repos_sorted_by_count():
    """Repos deben ordenarse por item_count descendente."""
    with patch.object(subprocess, "run") as mock_run:
        mock_run.side_effect = [
            subprocess.CompletedProcess([], 0, stdout=MOCK_VIEW),
            subprocess.CompletedProcess([], 0, stdout=MOCK_ITEMS_MIXED),
        ]

        result = project_repos(2, "@me")
        counts = [r["item_count"] for r in result["repos"]]
        assert counts == sorted(counts, reverse=True)


def test_repos_empty_project():
    """Proyecto vacío debe retornar lista vacía de repos."""
    empty_view = json.dumps({
        "id": "PVT_empty",
        "title": "Empty",
        "url": "",
        "items": {"totalCount": 0},
    })

    with patch.object(subprocess, "run") as mock_run:
        mock_run.side_effect = [
            subprocess.CompletedProcess([], 0, stdout=empty_view),
            subprocess.CompletedProcess([], 0, stdout=MOCK_ITEMS_EMPTY),
        ]

        result = project_repos(99, "@me")
        assert result["repos"] == []
        assert result["total_items"] == 0


def test_repos_pagination():
    """Debe paginar si hay más de 100 items."""
    # Simular 2 páginas
    page1 = {
        "data": {
            "node": {
                "items": {
                    "totalCount": 150,
                    "pageInfo": {"hasNextPage": True, "endCursor": "cursor2"},
                    "nodes": [
                        {
                            "content": {
                                "__typename": "Issue",
                                "title": f"Item {i}",
                                "repository": {"nameWithOwner": "testuser/repo"},
                                "state": "open",
                                "updatedAt": "2026-01-01T00:00:00Z",
                            }
                        }
                        for i in range(100)
                    ],
                }
            }
        }
    }
    page2 = {
        "data": {
            "node": {
                "items": {
                    "totalCount": 150,
                    "pageInfo": {"hasNextPage": False, "endCursor": None},
                    "nodes": [
                        {
                            "content": {
                                "__typename": "Issue",
                                "title": f"Item {i}",
                                "repository": {"nameWithOwner": "testuser/repo"},
                                "state": "open",
                                "updatedAt": "2026-01-01T00:00:00Z",
                            }
                        }
                        for i in range(100, 150)
                    ],
                }
            }
        }
    }

    with patch.object(subprocess, "run") as mock_run:
        mock_run.side_effect = [
            subprocess.CompletedProcess([], 0, stdout=MOCK_VIEW),
            subprocess.CompletedProcess([], 0, stdout=json.dumps(page1)),
            subprocess.CompletedProcess([], 0, stdout=json.dumps(page2)),
        ]

        result = project_repos(2, "@me")
        assert result["loaded_items"] == 150
        # 3 llamadas: view + page1 + page2
        assert mock_run.call_count == 3
