"""Tests para scripts/gh_project_metrics.py."""
import sys
import json
import subprocess
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from gh_project_metrics import project_metrics


MOCK_VIEW = json.dumps({
    "title": "Sprint 24",
    "url": "https://github.com/orgs/test/projects/1",
    "fields": {
        "nodes": [
            {"id": "field_status", "name": "Status"},
            {"id": "field_priority", "name": "Priority"},
        ]
    },
    "items": {
        "nodes": [
            {
                "content": {"title": "Feature A"},
                "updatedAt": "2025-06-01T00:00:00Z",
                "fieldValues": {
                    "nodes": [
                        {"field": {"id": "field_status"}, "name": "In Progress"},
                        {"field": {"id": "field_priority"}, "name": "High"},
                    ]
                },
            },
            {
                "content": {"title": "Bug B"},
                "updatedAt": "2025-05-01T00:00:00Z",
                "fieldValues": {
                    "nodes": [
                        {"field": {"id": "field_status"}, "name": "Todo"},
                        {"field": {"id": "field_priority"}, "name": "Medium"},
                    ]
                },
            },
            {
                "content": None,
                "updatedAt": "2025-04-01T00:00:00Z",
                "fieldValues": {"nodes": []},
            },
        ]
    },
})


def test_project_metrics_structure():
    """Debe retornar la estructura esperada."""
    with patch.object(subprocess, "run") as mock_run:
        mock_run.return_value.stdout = MOCK_VIEW
        mock_run.return_value.returncode = 0

        metrics = project_metrics(1, "testuser")

        assert "project" in metrics
        assert metrics["project"]["title"] == "Sprint 24"
        assert "total_items" in metrics
        assert metrics["total_items"] == 3


def test_project_metrics_by_status():
    """Debe agrupar correctamente por status."""
    with patch.object(subprocess, "run") as mock_run:
        mock_run.return_value.stdout = MOCK_VIEW
        mock_run.return_value.returncode = 0

        metrics = project_metrics(1, "testuser")
        assert metrics["by_status"]["In Progress"] == 1
        assert metrics["by_status"]["Todo"] == 1


def test_project_metrics_by_priority():
    """Debe agrupar correctamente por prioridad."""
    with patch.object(subprocess, "run") as mock_run:
        mock_run.return_value.stdout = MOCK_VIEW
        mock_run.return_value.returncode = 0

        metrics = project_metrics(1, "testuser")
        assert metrics["by_priority"]["High"] == 1
        assert metrics["by_priority"]["Medium"] == 1


def test_project_metrics_recent_items():
    """Los items más recientes deben aparecer primero."""
    with patch.object(subprocess, "run") as mock_run:
        mock_run.return_value.stdout = MOCK_VIEW
        mock_run.return_value.returncode = 0

        metrics = project_metrics(1, "testuser")
        assert metrics["recent_items"][0]["title"] == "Feature A"
        assert metrics["recent_items"][1]["title"] == "Bug B"


def test_project_metrics_empty_project():
    """Proyecto vacío debe retornar métricas en cero."""
    empty = json.dumps({
        "title": "Empty",
        "url": "",
        "fields": {"nodes": []},
        "items": {"nodes": []},
    })
    with patch.object(subprocess, "run") as mock_run:
        mock_run.return_value.stdout = empty
        mock_run.return_value.returncode = 0

        metrics = project_metrics(1, "testuser")
        assert metrics["total_items"] == 0
        assert metrics["by_status"] == {}
        assert metrics["recent_items"] == []
