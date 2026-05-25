#!/usr/bin/env python3
"""Obtiene métricas de un GitHub Project (v2) usando gh CLI + GraphQL.

Uso:
    uv run python3 scripts/gh_project_metrics.py <numero> [--owner <owner>]

Ejemplo:
    uv run python3 scripts/gh_project_metrics.py 1 --owner @me

Salida: JSON con project info, total de items, desglose por status/priority/size,
y lista de items recientes.
"""
import sys
import json
import subprocess
import argparse
import os
from utils import load_env


def get_owner() -> str:
    r = subprocess.run(
        ["gh", "api", "user", "--jq", ".login"],
        capture_output=True, text=True, check=True,
    )
    return r.stdout.strip()


def _run_gh(args: list[str]) -> str:
    """Ejecuta un comando gh y retorna stdout. Errores se propagan."""
    r = subprocess.run(args, capture_output=True, text=True, check=True)
    return r.stdout


def project_metrics(number: int, owner: str | None = None) -> dict:
    """Obtiene métricas completas de un proyecto vía GraphQL.

    Paso 1: Obtener el node ID del proyecto con `gh project view`.
    Paso 2: Consultar items + field values con GraphQL.
    """
    if owner is None:
        owner = get_owner()

    # ── Paso 1: info básica + node ID ──────────────────────────────
    raw = _run_gh([
        "gh", "project", "view", str(number),
        "--owner", owner,
        "--format", "json",
    ])
    meta = json.loads(raw)

    project_id = meta["id"]
    project_title = meta.get("title", "")
    project_url = meta.get("url", "")
    total_count = meta.get("items", {}).get("totalCount", 0)

    # ── Paso 2: GraphQL — items con field values ───────────────────
    query = """
    query($id:ID!) {
      node(id:$id) {
        ... on ProjectV2 {
          items(first: 100) {
            nodes {
              content {
                ... on Issue { title }
                ... on DraftIssue { title }
                ... on PullRequest { title }
              }
              updatedAt
              fieldValues(first: 20) {
                nodes {
                  ... on ProjectV2ItemFieldSingleSelectValue {
                    name
                    field {
                      ... on ProjectV2SingleSelectField {
                        name
                        id
                      }
                    }
                  }
                }
              }
            }
          }
        }
      }
    }
    """

    raw2 = _run_gh([
        "gh", "api", "graphql",
        "-f", f"query={query}",
        "-F", f"id={project_id}",
    ])
    gql = json.loads(raw2)
    items = (gql.get("data", {})
                .get("node", {})
                .get("items", {})
                .get("nodes", []))

    # ── Procesar items ─────────────────────────────────────────────
    by_status: dict[str, int] = {}
    by_priority: dict[str, int] = {}
    by_size: dict[str, int] = {}
    recent_items: list[dict] = []

    for item in items:
        content = item.get("content") or {}
        title = content.get("title", "") or ""
        updated_at = item.get("updatedAt", "") or ""

        # Extraer field values por tipo de campo
        status = ""
        priority = ""
        size = ""

        for fv in item.get("fieldValues", {}).get("nodes", []):
            fv_field = fv.get("field") or {}
            fv_name = fv.get("name", "") or ""
            field_name = (fv_field.get("name", "") or "").lower()

            if field_name in ("status", "state", "estado"):
                status = fv_name
                by_status[status] = by_status.get(status, 0) + 1
            elif field_name in ("priority", "prioridad"):
                priority = fv_name
                by_priority[priority] = by_priority.get(priority, 0) + 1
            elif field_name in ("size", "tamaño", "story points"):
                size = fv_name
                by_size[size] = by_size.get(size, 0) + 1

        recent_items.append({
            "title": title,
            "status": status,
            "updated_at": updated_at,
        })

    # Ordenar por updated_at descendente
    recent_items.sort(key=lambda x: x["updated_at"], reverse=True)

    return {
        "project": {
            "number": number,
            "title": project_title,
            "url": project_url,
        },
        "total_items": total_count,
        "loaded_items": len(items),
        "by_status": dict(sorted(by_status.items())),
        "by_priority": dict(sorted(by_priority.items())),
        "by_size": dict(sorted(by_size.items())),
        "recent_items": recent_items[:10],
    }


def main():
    load_env()
    parser = argparse.ArgumentParser(
        description="Métricas de GitHub Project (con GraphQL)"
    )
    parser.add_argument("number", type=int, help="Número del project")
    parser.add_argument("--owner", default=os.environ.get("GITHUB_OWNER"),
                        help="Owner. Default: .env → gh api user")
    args = parser.parse_args()

    try:
        metrics = project_metrics(args.number, args.owner)
        print(json.dumps(metrics, indent=2, ensure_ascii=False))
    except subprocess.CalledProcessError as e:
        print(f"❌ Error gh: {e.stderr.strip()}", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print("❌ gh CLI no encontrado. ¿Instalaste github-cli?", file=sys.stderr)
        sys.exit(1)
    except (KeyError, IndexError, json.JSONDecodeError) as e:
        print(f"❌ Error procesando datos: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
