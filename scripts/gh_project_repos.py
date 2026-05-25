#!/usr/bin/env python3
"""Lista los repositorios asociados a un GitHub Project (v2) con paginación completa.

Uso:
    uv run python3 scripts/gh_project_repos.py <numero> [--owner <owner>]

Ejemplo:
    uv run python3 scripts/gh_project_repos.py 2
    uv run python3 scripts/gh_project_repos.py 2 --owner @me

Para cada repositorio muestra: cantidad de issues, PRs, y última actualización.
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
    r = subprocess.run(args, capture_output=True, text=True, check=True)
    return r.stdout


def _fetch_all_items(project_id: str, max_items: int = 5000) -> list[dict]:
    """Obtiene TODOS los items de un project con paginación vía GraphQL.

    Usa `first: 100` + cursor `after` para iterar hasta obtener todos.
    """
    all_nodes = []
    after = None
    fetched = 0

    query_base = """
    query($id:ID!, $first:Int!, $after:String) {
      node(id:$id) {
        ... on ProjectV2 {
          items(first: $first, after: $after) {
            totalCount
            pageInfo { hasNextPage endCursor }
            nodes {
              ... on ProjectV2Item {
                content {
                  __typename
                  ... on Issue {
                    title
                    repository { nameWithOwner }
                    state
                    updatedAt
                  }
                  ... on PullRequest {
                    title
                    repository { nameWithOwner }
                    state
                    updatedAt
                  }
                  ... on DraftIssue {
                    title
                  }
                }
              }
            }
          }
        }
      }
    }
    """

    while fetched < max_items:
        variables = {
            "id": project_id,
            "first": min(100, max_items - fetched),
        }
        if after:
            variables["after"] = after

        raw = _run_gh([
            "gh", "api", "graphql",
            "-f", f"query={query_base}",
            "-F", f"id={variables['id']}",
            "-F", f"first={variables['first']}",
        ] + (["-F", f"after={after}"] if after else []))

        data = json.loads(raw)
        items_node = (data.get("data", {})
                         .get("node", {})
                         .get("items", {}))
        nodes = items_node.get("nodes", [])
        page_info = items_node.get("pageInfo", {})

        all_nodes.extend(nodes)
        fetched += len(nodes)

        if not page_info.get("hasNextPage"):
            break

        after = page_info.get("endCursor")

    return all_nodes


def project_repos(number: int, owner: str | None = None,
                  max_items: int = 5000) -> dict:
    """Obtiene los repositorios asociados a un project.

    Retorna:
    - project: info básica
    - total_items: total de items en el project
    - draft_issues: items sin repo (DraftIssue)
    - repos: lista de repos con métricas agrupadas
    """
    if owner is None:
        owner = get_owner()

    # Paso 1: Obtener node ID del project
    raw = _run_gh([
        "gh", "project", "view", str(number),
        "--owner", owner, "--format", "json",
    ])
    meta = json.loads(raw)
    project_id = meta["id"]
    total_count = meta.get("items", {}).get("totalCount", 0)

    # Paso 2: Traer todos los items con paginación
    items = _fetch_all_items(project_id, max_items)

    # Paso 3: Agrupar por repo
    repos: dict[str, dict] = {}
    draft_count = 0

    for item in items:
        content = item.get("content") or {}
        typename = content.get("__typename", "")

        # Draft Issues y Notes no tienen repo
        if typename == "DraftIssue":
            draft_count += 1
            continue

        repo_data = content.get("repository")
        if not repo_data:
            continue

        full_name = repo_data.get("nameWithOwner", "")
        if not full_name:
            continue

        if full_name not in repos:
            repos[full_name] = {
                "full_name": full_name,
                "url": f"https://github.com/{full_name}",
                "item_count": 0,
                "issues": 0,
                "pull_requests": 0,
                "last_updated": "",
            }

        r = repos[full_name]
        r["item_count"] += 1

        if typename == "Issue":
            r["issues"] += 1
        elif typename == "PullRequest":
            r["pull_requests"] += 1

        updated = content.get("updatedAt", "") or ""
        if updated > r["last_updated"]:
            r["last_updated"] = updated

    return {
        "project": {
            "number": number,
            "title": meta.get("title", ""),
            "url": meta.get("url", ""),
        },
        "total_items": total_count,
        "loaded_items": len(items),
        "draft_issues": draft_count,
        "repos": sorted(repos.values(),
                       key=lambda x: x["item_count"], reverse=True),
    }


def main():
    load_env()
    parser = argparse.ArgumentParser(
        description="Lista repositorios asociados a un GitHub Project"
    )
    parser.add_argument("number", type=int, help="Número del project")
    parser.add_argument("--owner", default=os.environ.get("GITHUB_OWNER"),
                        help="Owner. Default: .env → gh api user")
    parser.add_argument("--max-items", type=int, default=5000,
                        help="Máximo de items a procesar (default: 5000)")
    args = parser.parse_args()

    try:
        result = project_repos(args.number, args.owner, args.max_items)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except subprocess.CalledProcessError as e:
        print(f"❌ Error gh: {e.stderr.strip()}", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print("❌ gh CLI no encontrado", file=sys.stderr)
        sys.exit(1)
    except (KeyError, IndexError, json.JSONDecodeError) as e:
        print(f"❌ Error procesando datos: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
