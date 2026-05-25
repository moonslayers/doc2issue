#!/usr/bin/env python3
"""Agrega un issue a un GitHub Project y setea sus campos custom vía GraphQL.

Usa GraphQL directo (addProjectV2ItemById) en vez de parsear output
de gh CLI, que cambia entre versiones.

Uso:
    uv run python3 scripts/gh_project_set_fields.py \\
      --project 2 --owner moonslayers \\
      --item-number 1345 --repo owner/repo \\
      --fields '{"Status":"Todo","Priority":"High","Size":"M","Estimate":40}'
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


def _get_issue_node_id(repo: str, number: int) -> str:
    """Obtiene node ID del issue."""
    q = 'query{repository(owner:"' + repo.split('/')[0] + '",name:"' + repo.split('/')[1] + '"){issue(number:' + str(number) + '){id}}}'
    r = _run_gh(["gh","api","graphql","-f",f"query={q}","--jq",".data.repository.issue.id"])
    return r.strip()


def _get_project_fields(project_id: str) -> list[dict]:
    """Obtiene todos los campos del proyecto con sus opciones y tipos."""
    q = 'query{node(id:"' + project_id + '"){...on ProjectV2{fields(first:30){nodes{...on ProjectV2SingleSelectField{__typename id name options{id name}}...on ProjectV2Field{__typename id name}}}}}}'
    r = _run_gh(["gh","api","graphql","-f",f"query={q}","--jq",".data.node.fields.nodes"])
    return json.loads(r)


def _item_exists(project_id: str, issue_node_id: str) -> bool:
    """Verifica si el issue ya está en el project (evita duplicados)."""
    q = 'query{node(id:"' + project_id + '"){...on ProjectV2{items(first:100){nodes{content{...on Issue{id}}}}}}}'
    r = _run_gh(["gh","api","graphql","-f",f"query={q}","--jq",".data.node.items.nodes[].content.id"])
    return issue_node_id in r.splitlines()


def _add_item_to_project(project_id: str, issue_node_id: str) -> str:
    """Agrega issue al proyecto via GraphQL, retorna item ID."""
    q = 'mutation{addProjectV2ItemById(input:{projectId:"' + project_id + '" contentId:"' + issue_node_id + '"}){item{id}}}'
    r = _run_gh(["gh","api","graphql","-f",f"query={q}","--jq",".data.addProjectV2ItemById.item.id"])
    return r.strip()


def _set_field(project_id: str, item_id: str, field_id: str, value) -> bool:
    """Setea un campo del proyecto, detectando el tipo de valor."""
    if isinstance(value, dict):
        parts = []
        for k, v in value.items():
            if isinstance(v, str):
                parts.append(f'{k}: "{v}"')
            elif isinstance(v, bool):
                parts.append(f'{k}: {"true" if v else "false"}')
            elif isinstance(v, (int, float)):
                parts.append(f'{k}: {v}')
            else:
                parts.append(f'{k}: "{v}"')
        value_str = "{" + ",".join(parts) + "}"
    else:
        value_str = json.dumps(value)
    q = 'mutation{updateProjectV2ItemFieldValue(input:{projectId:"' + project_id + '" itemId:"' + item_id + '" fieldId:"' + field_id + '" value:' + value_str + '}){projectV2Item{id}}}'
    r = _run_gh(["gh","api","graphql","-f",f"query={q}","--jq",".data.updateProjectV2ItemFieldValue.projectV2Item.id"])
    return bool(r.strip())


def set_fields(project: int, owner: str, item_number: int,
               repo: str, fields: dict) -> dict:
    """Agrega issue al proyecto y setea sus campos via GraphQL directo."""
    results = {}

    # 1. Obtener IDs
    print("  Obteniendo IDs...", file=sys.stderr)
    project_id = _get_project_id(owner, project)
    results["project_id"] = project_id
    print(f"  ✅ Project ID: {project_id}", file=sys.stderr)

    issue_node_id = _get_issue_node_id(repo, item_number)
    results["issue_node_id"] = issue_node_id
    print(f"  ✅ Issue node ID: {issue_node_id}", file=sys.stderr)

    # 2. Obtener campos del proyecto para conocer tipos y option IDs
    proj_fields = _get_project_fields(project_id)
    field_map = {}  # field_name_lower -> {id, __typename, options}
    for f in proj_fields:
        field_map[f.get("name", "").lower()] = f

    # 3. Agregar item al proyecto (idempotente)
    if _item_exists(project_id, issue_node_id):
        print("  ⚠️  Issue ya está en el project, saltando add", file=sys.stderr)
        # Obtener item ID existente para setear campos después
        q = 'query{node(id:"' + project_id + '"){...on ProjectV2{items(first:100){nodes{id content{...on Issue{id}}}}}}}'
        r = _run_gh(["gh","api","graphql","-f",f"query={q}","--jq",".data.node.items.nodes[] | select(.content.id==\"" + issue_node_id + '\") | .id'])
        item_id = r.strip()
        print(f"  ✅ Item ID existente: {item_id}", file=sys.stderr)
    else:
        print("  Agregando al proyecto...", file=sys.stderr)
        item_id = _add_item_to_project(project_id, issue_node_id)
    if not item_id:
        results["error"] = "No se pudo agregar item al proyecto"
        print("  ❌ Falló", file=sys.stderr)
        return results
    results["item_id"] = item_id
    print(f"  ✅ Item ID: {item_id}", file=sys.stderr)

    # 4. Setear cada campo según su tipo
    field_results = {}
    for field_name, value in fields.items():
        if value is None or value == "":
            continue

        fn = field_name.lower()
        field_def = field_map.get(fn)

        if not field_def:
            field_results[field_name] = "❌ Campo no encontrado en project"
            print(f"  ⚠️  '{field_name}' no encontrado en project", file=sys.stderr)
            continue

        typename = field_def.get("__typename", "")
        field_id = field_def.get("id", "")

        print(f"  Seteando {field_name} ({typename}) = {value}...", file=sys.stderr)

        if typename == "ProjectV2SingleSelectField":
            # Buscar option ID por nombre
            opt_id = None
            for opt in field_def.get("options", []):
                if opt.get("name", "").lower() == str(value).lower():
                    opt_id = opt["id"]
                    break
            if not opt_id:
                # Búsqueda parcial
                for opt in field_def.get("options", []):
                    if str(value).lower() in opt.get("name", "").lower():
                        opt_id = opt["id"]
                        break
            if opt_id:
                ok = _set_field(project_id, item_id, field_id,
                               {"singleSelectOptionId": opt_id})
                field_results[field_name] = "✅" if ok else "❌"
            else:
                field_results[field_name] = "⚠️  Opción no encontrada"
                print(f"  ⚠️  Opción '{value}' no encontrada en {field_name}", file=sys.stderr)

        elif typename == "ProjectV2Field":
            # Detectar por nombre si es numérico
            if fn in ("estimate", "estimación", "hours", "horas", "story points"):
                ok = _set_field(project_id, item_id, field_id, {"number": float(value)})
            else:
                ok = _set_field(project_id, item_id, field_id, {"text": str(value)})
            field_results[field_name] = "✅" if ok else "❌"

        else:
            # Otros tipos: intentar como texto
            ok = _set_field(project_id, item_id, field_id, {"text": str(value)})
            field_results[field_name] = "✅" if ok else "❌"

    results["fields"] = field_results
    return results


def main():
    load_env()
    parser = argparse.ArgumentParser(
        description="Agrega issue a proyecto y setea campos vía GraphQL"
    )
    parser.add_argument("--project", required=True, type=int)
    parser.add_argument("--owner", default=os.environ.get("GITHUB_OWNER"))
    parser.add_argument("--item-number", required=True, type=int,
                        help="Número del issue")
    parser.add_argument("--repo", required=True,
                        help="owner/repo del issue")
    parser.add_argument("--fields", required=True,
                        help='JSON: {"Status":"Todo","Priority":"High","Estimate":40}')
    args = parser.parse_args()

    try:
        fields = json.loads(args.fields)
        result = set_fields(args.project, args.owner,
                           args.item_number, args.repo, fields)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except subprocess.CalledProcessError as e:
        print(f"❌ Error gh: {e.stderr.strip()[:300]}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
