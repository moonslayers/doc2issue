#!/usr/bin/env python3
"""Agrega un issue a un GitHub Project y setea sus campos custom.

Elimina la necesidad de escribir 4+ queries GraphQL manuales.

Uso:
    uv run python3 scripts/gh_project_set_fields.py \\
      --project 2 --owner moonslayers \\
      --item-url "https://github.com/.../issues/1345" \\
      --fields '{"Status":"In Progress","Priority":"High","Size":"M"}'
"""
import sys, json, subprocess, argparse, os, re
from utils import load_env


def _run_gh(args: list[str]) -> str:
    r = subprocess.run(args, capture_output=True, text=True, check=True)
    return r.stdout


def _get_project_id(owner: str, project: int) -> str:
    """Obtiene el node ID del proyecto (maneja user vs org)."""
    # Intentar como usuario primero
    q_user = 'query { user(login: "' + owner + '") { projectV2(number: ' + str(project) + ') { id } } }'
    r = _run_gh(["gh", "api", "graphql", "-f", f"query={q_user}", "--jq", ".data.user.projectV2.id"])
    if r.strip():
        return r.strip()
    # Intentar como organización
    q_org = 'query { organization(login: "' + owner + '") { projectV2(number: ' + str(project) + ') { id } } }'
    r = _run_gh(["gh", "api", "graphql", "-f", f"query={q_org}", "--jq", ".data.organization.projectV2.id"])
    return r.strip()


def _get_field_option_id(project_id: str, field_name: str, value: str) -> str | None:
    """Obtiene el option ID de un campo single select.

    Busca entre los campos del proyecto el que coincida con field_name,
    y dentro de sus opciones la que coincida con value.
    """
    q = f'query {{ node(id: "{project_id}") {{ ... on ProjectV2 {{ fields(first: 20) {{ nodes {{ ... on ProjectV2SingleSelectField {{ id name options {{ id name }} }} }} }} }} }} }}'
    r = _run_gh(["gh", "api", "graphql", "-f", f"query={q}", "--jq", ".data.node.fields.nodes"])
    fields = json.loads(r)

    for field in fields:
        if field.get("name", "").lower() == field_name.lower():
            for opt in field.get("options", []):
                if opt.get("name", "").lower() == value.lower():
                    return opt["id"]
            # Buscar parcial
            for opt in field.get("options", []):
                if value.lower() in opt.get("name", "").lower():
                    return opt["id"]
            print(f"  ⚠️  No se encontró opción '{value}' en campo '{field_name}'",
                  file=sys.stderr)
            return None
    print(f"  ⚠️  No se encontró campo '{field_name}' en el proyecto",
          file=sys.stderr)
    return None


def _get_text_field_id(project_id: str, field_name: str) -> str | None:
    """Obtiene el ID de un campo de texto (para estimate, etc.)."""
    q = f'query {{ node(id: "{project_id}") {{ ... on ProjectV2 {{ fields(first: 20) {{ nodes {{ ... on ProjectV2Field {{ id name }} }} }} }} }} }}'
    r = _run_gh(["gh", "api", "graphql", "-f", f"query={q}", "--jq", ".data.node.fields.nodes"])
    fields = json.loads(r)
    for field in fields:
        if field.get("name", "").lower() == field_name.lower():
            return field["id"]
    return None


def set_fields(project: int, owner: str, item_url: str,
               fields: dict) -> dict:
    """Agrega un item al proyecto y setea sus campos.

    Retorna dict con los resultados de cada campo.
    """
    results = {}

    # 1. Obtener project ID
    print("Obteniendo project ID...", file=sys.stderr)
    project_id = _get_project_id(owner, project)
    if not project_id:
        raise ValueError(f"No se encontró project #{project} para {owner}")
    print(f"  ✅ Project ID: {project_id}", file=sys.stderr)
    results["project_id"] = project_id

    # 2. Agregar item al proyecto
    print("Agregando item al proyecto...", file=sys.stderr)
    r = _run_gh([
        "gh", "project", "item-add", str(project),
        "--owner", owner,
        "--url", item_url,
    ])
    # Extraer item ID del output
    # Formato: "Added item •PVTI_lAHOBQKpns4A9lsF...•"
    item_id = ""
    for line in r.splitlines():
        if "PVTI_" in line:
            match = re.search(r'PVTI_\w+', line)
            if match:
                item_id = match.group()
                break
    if not item_id:
        print(f"  ⚠️  No se pudo extraer item ID del output", file=sys.stderr)
        print(f"  Output: {r[:200]}", file=sys.stderr)
    else:
        print(f"  ✅ Item ID: {item_id}", file=sys.stderr)
    results["item_id"] = item_id

    if not item_id:
        results["error"] = "No se obtuvo item ID"
        return results

    # 3. Setear cada campo
    field_results = {}
    for field_name, value in fields.items():
        if not value:
            continue

        print(f"  Seteando {field_name} = {value}...", file=sys.stderr)
        value_str = str(value)

        # Intentar como single select primero
        opt_id = _get_field_option_id(project_id, field_name, value_str)
        if opt_id:
            q = f'mutation {{ updateProjectV2ItemFieldValue(input: {{ projectId: "{project_id}" itemId: "{item_id}" fieldId: "{_get_field_option_id.__globals__["_get_field_option_id"]}" }}) {{ clientMutationId }} }}'
            # Hacer la mutación
            mut = f'mutation {{ updateProjectV2ItemFieldValue(input: {{ projectId: "{project_id}" itemId: "{item_id}" fieldId: "{opt_id}" value: {{ singleSelectOptionId: "{opt_id}" }} }}) {{ projectV2Item {{ id }} }} }}'
            r = _run_gh(["gh", "api", "graphql", "-f", f"query={mut}", "--jq",
                        ".data.updateProjectV2ItemFieldValue.projectV2Item.id"])
            field_results[field_name] = "✅" if r.strip() else "❌"
        else:
            # Intentar como campo de texto
            text_fid = _get_text_field_id(project_id, field_name)
            if text_fid:
                mut = f'mutation {{ updateProjectV2ItemFieldValue(input: {{ projectId: "{project_id}" itemId: "{item_id}" fieldId: "{text_fid}" value: {{ text: "{value_str}" }} }}) {{ projectV2Item {{ id }} }} }}'
                r = _run_gh(["gh", "api", "graphql", "-f", f"query={mut}", "--jq",
                            ".data.updateProjectV2ItemFieldValue.projectV2Item.id"])
                field_results[field_name] = "✅" if r.strip() else "❌"
            else:
                field_results[field_name] = "⚠️  Campo no encontrado"

    results["fields"] = field_results
    return results


def main():
    load_env()
    parser = argparse.ArgumentParser(
        description="Agrega issue a proyecto y setea campos custom"
    )
    parser.add_argument("--project", required=True, type=int,
                        help="Número del project")
    parser.add_argument("--owner", default=os.environ.get("GITHUB_OWNER"),
                        help="Owner del project")
    parser.add_argument("--item-url", required=True,
                        help="URL del issue/PR a agregar")
    parser.add_argument("--fields", required=True,
                        help='JSON: {"Status":"In Progress","Priority":"High"}')
    args = parser.parse_args()

    try:
        fields = json.loads(args.fields)
        result = set_fields(args.project, args.owner, args.item_url, fields)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except subprocess.CalledProcessError as e:
        print(f"❌ Error gh: {e.stderr.strip()[:300]}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
