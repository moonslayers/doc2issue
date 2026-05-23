#!/usr/bin/env python3
"""Lista repositorios de GitHub usando gh CLI.

Uso:
    uv run python3 scripts/gh_list_repos.py [--owner <owner>]

Si no se especifica --owner, usa el usuario autenticado.
"""
import sys
import json
import subprocess
import argparse


def get_owner() -> str:
    """Obtiene el usuario autenticado de gh."""
    r = subprocess.run(
        ["gh", "api", "user", "--jq", ".login"],
        capture_output=True, text=True, check=True,
    )
    return r.stdout.strip()


def list_repos(owner: str | None = None) -> list[dict]:
    """Lista repositorios visibles para el owner dado.

    Retorna una lista de dicts con: name, full_name, url, description,
    is_private, updated_at, language.
    """
    if owner is None:
        owner = get_owner()

    r = subprocess.run(
        [
            "gh", "repo", "list", owner,
            "--json", "name,owner,url,description,isPrivate,updatedAt,primaryLanguage",
            "--limit", "100",
            "--source",  # solo forks no
        ],
        capture_output=True, text=True, check=True,
    )
    repos = json.loads(r.stdout)

    # Estandarizar campos
    result = []
    for repo in repos:
        result.append({
            "name": repo["name"],
            "full_name": f"{owner}/{repo['name']}",
            "url": repo["url"],
            "description": repo.get("description", ""),
            "is_private": repo.get("isPrivate", False),
            "updated_at": repo.get("updatedAt", ""),
            "language": (
                repo.get("primaryLanguage", {}) or {}
            ).get("name", ""),
        })
    return result


def main():
    parser = argparse.ArgumentParser(description="Lista repositorios de GitHub")
    parser.add_argument("--owner", help="Owner (user u org). Default: usuario autenticado")
    args = parser.parse_args()

    try:
        repos = list_repos(args.owner)
        print(json.dumps(repos, indent=2, ensure_ascii=False))
    except subprocess.CalledProcessError as e:
        print(f"❌ Error al ejecutar gh: {e.stderr.strip()}", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print("❌ gh CLI no encontrado. ¿Instalaste github-cli?", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
