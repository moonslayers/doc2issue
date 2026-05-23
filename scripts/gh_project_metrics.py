#!/usr/bin/env python3
"""Obtiene métricas de un GitHub Project (v2) usando gh CLI.

Uso:
    uv run python3 scripts/gh_project_metrics.py <numero> --owner <owner>

Ejemplo:
    uv run python3 scripts/gh_project_metrics.py 1 --owner testuser

Salida: JSON con:
  - project: info del proyecto
  - total_items: cantidad total de ítems
  - by_status: ítems agrupados por columna de estado
  - recent_items: últimos ítems actualizados
"""
import sys
import json
import subprocess
import argparse
from datetime import datetime, timezone


def get_owner() -> str:
    r = subprocess.run(
        ["gh", "api", "user", "--jq", ".login"],
        capture_output=True, text=True, check=True,
    )
    return r.stdout.strip()


def project_metrics(number: int, owner: str | None = None) -> dict:
    """Obtiene métricas de un proyecto.

    Retorna un dict con:
    - project: {number, title, url}
    - total_items: int
    - by_status: {columna: cantidad}
    - by_priority: {prioridad: cantidad}
    - by_size: {tamaño: cantidad}
    - recent_items: [{title, status, updated_at}]
    """
    if owner is None:
        owner = get_owner()

    # Obtener info del proyecto + items con campos
    r = subprocess.run(
        [
            "gh", "project", "view", str(number),
            "--owner", owner,
            "--json", "title,url,items,fields",
            "--limit", "200",
        ],
        capture_output=True, text=True, check=True,
    )
    data = json.loads(r.stdout)

    project_info = {
        "number": number,
        "title": data.get("title", ""),
        "url": data.get("url", ""),
    }

    items = data.get("items", {}).get("nodes", [])

    # Mapear field names para status y otros
    fields = data.get("fields", {}).get("nodes", [])
    status_field_id = None
    priority_field_id = None
    size_field_id = None

    for f in fields:
        fname = f.get("name", "").lower()
        if fname in ("status", "state", "estado"):
            status_field_id = f["id"]
        elif fname in ("priority", "prioridad"):
            priority_field_id = f["id"]
        elif fname in ("size", "tamaño", "story points"):
            size_field_id = f["id"]

    # Procesar items
    by_status: dict[str, int] = {}
    by_priority: dict[str, int] = {}
    by_size: dict[str, int] = {}
    recent_items: list[dict] = []

    for item in items:
        content = item.get("content", {})
        title = ""
        if content:
            title = content.get("title", "") or ""

        updated_at = item.get("updatedAt", "")
        status = ""
        priority = ""
        size = ""

        # Extraer field values
        for fv in item.get("fieldValues", {}).get("nodes", []):
            fv_field = fv.get("field", {})
            fv_field_id = fv_field.get("id", "")
            fv_name = fv.get("name", "")

            if fv_field_id == status_field_id:
                status = fv_name
                by_status[status] = by_status.get(status, 0) + 1
            elif fv_field_id == priority_field_id:
                priority = fv_name
                by_priority[priority] = by_priority.get(priority, 0) + 1
            elif fv_field_id == size_field_id:
                size = fv_name
                by_size[size] = by_size.get(size, 0) + 1

        recent_items.append({
            "title": title,
            "status": status,
            "updated_at": updated_at,
        })

    # Ordenar recent_items por updated_at descendente
    def _sort_key(item):
        dt = item.get("updated_at", "")
        return dt if dt else ""

    recent_items.sort(key=_sort_key, reverse=True)

    return {
        "project": project_info,
        "total_items": len(items),
        "by_status": dict(sorted(by_status.items())),
        "by_priority": dict(sorted(by_priority.items())),
        "by_size": dict(sorted(by_size.items())),
        "recent_items": recent_items[:10],
    }


def main():
    parser = argparse.ArgumentParser(description="Métricas de GitHub Project")
    parser.add_argument("number", type=int, help="Número del project")
    parser.add_argument("--owner", help="Owner del proyecto")
    args = parser.parse_args()

    try:
        metrics = project_metrics(args.number, args.owner)
        print(json.dumps(metrics, indent=2, ensure_ascii=False))
    except subprocess.CalledProcessError as e:
        print(f"❌ Error gh: {e.stderr.strip()}", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print("❌ gh CLI no encontrado", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
