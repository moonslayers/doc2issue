#!/usr/bin/env python3
"""Obtiene campos y valores válidos de un GitHub Project (v2).

Útil para que el analyzer valide Priority, Size, Status antes de asignarlos.

Uso:
    uv run python3 scripts/gh_project_fields.py --owner moonslayers --project 2

Output:
    {
      "project": {"number": 2, "title": "Desarrollo SEI"},
      "fields": {
        "Status": {"type": "single_select", "options": ["Todo", "In Progress", "Done"]},
        "Priority": {"type": "single_select", "options": ["P0", "P1", "P2", "P3", "P4"]},
        "Size": {"type": "single_select", "options": ["XS", "S", "M", "L", "XL"]},
        "Estimate": {"type": "number"}
      }
    }
"""
import sys, json, subprocess, argparse, os
from utils import load_env


def _run_gh(args: list[str]) -> str:
    r = subprocess.run(args, capture_output=True, text=True, check=True)
    return r.stdout


def _get_project_id(owner: str, project: int) -> str:
    """Obtiene node ID del proyecto (user → org fallback)."""
    q = 'query{user(login:"' + owner + '"){projectV2(number:' + str(project) + '){id}}}'
    r = _run_gh(["gh","api","graphql","-f",f"query={q}","--jq",".data.user.projectV2.id"])
    if r.strip():
        return r.strip()
    q = 'query{organization(login:"' + owner + '"){projectV2(number:' + str(project) + '){id}}}'
    r = _run_gh(["gh","api","graphql","-f",f"query={q}","--jq",".data.organization.projectV2.id"])
    return r.strip()


def get_fields(owner: str, project: int) -> dict:
    """Obtiene campos del proyecto con sus tipos y opciones."""
    project_id = _get_project_id(owner, project)

    q = """query{
      node(id:"%s"){
        ...on ProjectV2{
          title number
          fields(first:30){
            nodes{
              ...on ProjectV2SingleSelectField{__typename id name options{id name}}
              ...on ProjectV2IterationField{__typename id name}
              ...on ProjectV2Field{__typename id name}
            }
          }
        }
      }
    }""" % project_id

    r = _run_gh(["gh","api","graphql","-f",f"query={q}","--jq",".data.node"])
    data = json.loads(r)

    fields = {}
    for f in data.get("fields", {}).get("nodes", []):
        typename = f.get("__typename", "")
        name = f.get("name", "")

        if typename == "ProjectV2SingleSelectField":
            options = [opt["name"] for opt in f.get("options", [])]
            fields[name] = {"type": "single_select", "options": options}
        elif typename == "ProjectV2IterationField":
            fields[name] = {"type": "iteration"}
        elif typename == "ProjectV2Field":
            # No podemos saber si es text o number sin más datos,
            # pero por nombre podemos inferir
            if name.lower() in ("estimate", "estimación", "hours", "story points"):
                fields[name] = {"type": "number"}
            else:
                fields[name] = {"type": "text"}

    return {
        "project": {
            "number": data.get("number"),
            "title": data.get("title", ""),
        },
        "fields": fields,
    }


def main():
    load_env()
    parser = argparse.ArgumentParser(
        description="Obtiene campos y valores válidos de un GitHub Project"
    )
    parser.add_argument("--project", required=True, type=int,
                        help="Número del project")
    parser.add_argument("--owner", default=os.environ.get("GITHUB_OWNER"),
                        help="Owner. Default: .env → gh api user")
    args = parser.parse_args()

    try:
        result = get_fields(args.owner, args.project)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except subprocess.CalledProcessError as e:
        print(f"❌ Error gh: {e.stderr.strip()[:200]}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
