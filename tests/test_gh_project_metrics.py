"""Tests para scripts/gh_project_metrics.py (ahora con GraphQL)."""
import sys
import json
import subprocess
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from gh_project_metrics import project_metrics


# ── Mock: respuesta de gh project view (paso 1) ─────────────────────
MOCK_PROJECT_VIEW = json.dumps({
    "id": "PVT_kwHOBQKpns4A9lsF",
    "title": "Desarrollo SEI",
    "url": "https://github.com/users/test/projects/2",
    "items": {"totalCount": 847},
})

# ── Mock: respuesta de gh api graphql (paso 2) ─────────────────────
MOCK_GRAPHQL = json.dumps({
    "data": {
        "node": {
            "items": {
                "nodes": [
                    {
                        "content": {"title": "Feature Login"},
                        "updatedAt": "2025-06-10T00:00:00Z",
                        "fieldValues": {
                            "nodes": [
                                {
                                    "name": "In Progress",
                                    "field": {"name": "Status", "id": "field_status"},
                                },
                                {
                                    "name": "High",
                                    "field": {"name": "Priority", "id": "field_priority"},
                                },
                                {
                                    "name": "M",
                                    "field": {"name": "Size", "id": "field_size"},
                                },
                            ]
                        },
                    },
                    {
                        "content": {"title": "Bug fix"},
                        "updatedAt": "2025-06-05T00:00:00Z",
                        "fieldValues": {
                            "nodes": [
                                {
                                    "name": "Todo",
                                    "field": {"name": "Status", "id": "field_status"},
                                },
                                {
                                    "name": "Medium",
                                    "field": {"name": "Priority", "id": "field_priority"},
                                },
                            ]
                        },
                    },
                    {
                        "content": None,
                        "updatedAt": "2025-06-01T00:00:00Z",
                        "fieldValues": {"nodes": []},
                    },
                ]
            }
        }
    }
})

# ── Mock: GraphQL vacío (proyecto sin items cargados) ──────────────
MOCK_GRAPHQL_EMPTY = json.dumps({
    "data": {
        "node": {
            "items": {"nodes": []}
        }
    }
})


def test_metrics_structure():
    """Debe retornar la estructura esperada."""
    with patch.object(subprocess, "run") as mock_run:
        mock_run.side_effect = [
            # Paso 1: gh project view
            subprocess.CompletedProcess([], 0, stdout=MOCK_PROJECT_VIEW),
            # Paso 2: gh api graphql
            subprocess.CompletedProcess([], 0, stdout=MOCK_GRAPHQL),
        ]

        metrics = project_metrics(2, "@me")

        assert metrics["project"]["title"] == "Desarrollo SEI"
        assert metrics["total_items"] == 847
        assert metrics["loaded_items"] == 3


def test_metrics_by_status():
    """Debe agrupar correctamente por status."""
    with patch.object(subprocess, "run") as mock_run:
        mock_run.side_effect = [
            subprocess.CompletedProcess([], 0, stdout=MOCK_PROJECT_VIEW),
            subprocess.CompletedProcess([], 0, stdout=MOCK_GRAPHQL),
        ]

        metrics = project_metrics(2, "@me")
        assert metrics["by_status"]["In Progress"] == 1
        assert metrics["by_status"]["Todo"] == 1


def test_metrics_by_priority():
    """Debe agrupar correctamente por prioridad."""
    with patch.object(subprocess, "run") as mock_run:
        mock_run.side_effect = [
            subprocess.CompletedProcess([], 0, stdout=MOCK_PROJECT_VIEW),
            subprocess.CompletedProcess([], 0, stdout=MOCK_GRAPHQL),
        ]

        metrics = project_metrics(2, "@me")
        assert metrics["by_priority"]["High"] == 1
        assert metrics["by_priority"]["Medium"] == 1


def test_metrics_by_size():
    """Debe agrupar correctamente por tamaño."""
    with patch.object(subprocess, "run") as mock_run:
        mock_run.side_effect = [
            subprocess.CompletedProcess([], 0, stdout=MOCK_PROJECT_VIEW),
            subprocess.CompletedProcess([], 0, stdout=MOCK_GRAPHQL),
        ]

        metrics = project_metrics(2, "@me")
        assert metrics["by_size"]["M"] == 1
        assert "S" not in metrics["by_size"]


def test_metrics_recent_items():
    """Items más recientes primero."""
    with patch.object(subprocess, "run") as mock_run:
        mock_run.side_effect = [
            subprocess.CompletedProcess([], 0, stdout=MOCK_PROJECT_VIEW),
            subprocess.CompletedProcess([], 0, stdout=MOCK_GRAPHQL),
        ]

        metrics = project_metrics(2, "@me")
        assert metrics["recent_items"][0]["title"] == "Feature Login"
        assert metrics["recent_items"][1]["title"] == "Bug fix"


def test_metrics_empty_project():
    """Proyecto vacío debe retornar métricas en cero."""
    empty_view = json.dumps({
        "id": "PVT_test",
        "title": "Empty",
        "url": "",
        "items": {"totalCount": 0},
    })

    with patch.object(subprocess, "run") as mock_run:
        mock_run.side_effect = [
            subprocess.CompletedProcess([], 0, stdout=empty_view),
            subprocess.CompletedProcess([], 0, stdout=MOCK_GRAPHQL_EMPTY),
        ]

        metrics = project_metrics(99, "@me")
        assert metrics["total_items"] == 0
        assert metrics["by_status"] == {}
        assert metrics["recent_items"] == []


def test_metrics_calls_graphql_with_project_id():
    """La consulta GraphQL debe usar el project ID obtenido."""
    with patch.object(subprocess, "run") as mock_run:
        mock_run.side_effect = [
            subprocess.CompletedProcess([], 0, stdout=MOCK_PROJECT_VIEW),
            subprocess.CompletedProcess([], 0, stdout=MOCK_GRAPHQL),
        ]

        project_metrics(2, "@me")

        # Segunda llamada debe ser gh api graphql con el ID correcto
        second_call_args = mock_run.call_args_list[1][0][0]
        assert "gh" in second_call_args
        assert "api" in second_call_args
        assert "graphql" in second_call_args
        # Verificar que pasa el project ID
        id_found = any("PVT_kwHOBQKpns4A9lsF" in a for a in second_call_args)
        assert id_found, "El project ID debe estar en la consulta GraphQL"
