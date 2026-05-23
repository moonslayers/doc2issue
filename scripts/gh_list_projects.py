#!/usr/bin/env python3
"""Lista proyectos de GitHub Projects (v2) usando gh CLI.

Uso:
    # Proyectos del owner (org/user)
    uv run python3 scripts/gh_list_projects.py --owner <owner>

    # Proyectos de un repo específico
    uv run python3 scripts/gh_list_projects.py --repo <repo> --owner <owner>

Si no se especifica --owner, usa el usuario autenticado.
"""
import sys
import json
import subprocess
import argparse


def get_owner() -> str:
    """Obtiene el usuario autenticado."""
    r = subprocess.run(
        ["gh", "api", "user", "--jq", ".login"],
        capture_output=True, text=True, check=True,
    )
    return r.stdout.strip()


def list_projects(owner: str | None = None, repo: str | None = None) -> list[dict]:
    """Lista proyectos GitHub Projects (v2).

    Si repo se especifica, lista proyectos vinculados a ese repo.
    Si no, lista proyectos del owner (org/user).
    """
    if owner is None:
        owner = get_owner()

    cmd = ["gh", "project", "list", "--owner", owner, "--json", "title,number,url,closed"]

    if repo:
        cmd.extend(["--repo", f"{owner}/{repo}" if "/" not in repo else repo])

    r = subprocess.run(cmd, capture_output=True, text=True, check=True)
    projects = json.loads(r.stdout)

    result = []
    for p in projects.get("projects", []):
        result.append({
            "number": p["number"],
            "title": p["title"],
            "url": p.get("url", ""),
            "is_closed": p.get("closed", False),
        })
    return result


def main():
    parser = argparse.ArgumentParser(description="Lista GitHub Projects")
    parser.add_argument("--owner", help="Owner (user u org)")
    parser.add_argument("--repo", help="Repo específico (ej: doc2issue)")
    args = parser.parse_args()

    try:
        projects = list_projects(args.owner, args.repo)
        if not projects:
            print("📭 No se encontraron proyectos.")
        else:
            print(json.dumps(projects, indent=2, ensure_ascii=False))
    except subprocess.CalledProcessError as e:
        print(f"❌ Error gh: {e.stderr.strip()}", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print("❌ gh CLI no encontrado", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
