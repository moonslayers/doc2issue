#!/usr/bin/env python3
"""Valida que uno o más issue.json cumplan el output contract.

Uso:
    uv run python3 scripts/validate_issue.py output/*.issue.json

Retorna exit code 0 si todo ok, 1 si hay errores.
"""
import sys, json
from pathlib import Path


VALID_PRIORITIES = {"p0", "p1", "p2", "p3", "p4", "high", "medium", "low",
                    "alta", "media", "baja", "critica", "crítica"}
VALID_SIZES = {"xs", "s", "m", "l", "xl"}
REQUIRED_FIELDS = ["title", "description", "target_repo"]
OPTIONAL_FIELDS = ["target_project", "labels_resolved", "size",
                   "estimate_hours", "status", "priority_resolved",
                   "images", "stakeholders", "questions_for_pm",
                   "acceptance_criteria", "references"]


def validate(json_path: str) -> list[str]:
    """Valida un issue.json. Retorna lista de errores."""
    errors = []
    path = Path(json_path)

    if not path.exists():
        return [f"❌ Archivo no existe: {json_path}"]

    try:
        with open(path, encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        return [f"❌ JSON inválido: {e}"]

    if not isinstance(data, dict):
        return [f"❌ Debe ser un objeto JSON, no {type(data).__name__}"]

    # Verificar campos requeridos
    for field in REQUIRED_FIELDS:
        if field not in data or data[field] is None or data[field] == "":
            errors.append(f"❌ {field}: requerido y no vacío")
        elif isinstance(data[field], str) and not data[field].strip():
            errors.append(f"❌ {field}: no debe estar vacío")

    # title no debe ser placeholder
    title = data.get("title", "")
    if title and title.startswith("{{") and title.endswith("}}"):
        errors.append(f"❌ title: no reemplazado (contiene placeholder)")

    # labels_resolved debe ser array
    labels = data.get("labels_resolved", [])
    if not isinstance(labels, list):
        errors.append("❌ labels_resolved: debe ser un array")
    elif labels:
        for lbl in labels:
            if not isinstance(lbl, str) or not lbl.strip():
                errors.append(f"❌ labels_resolved: elemento inválido '{lbl}'")

    # priority_resolved debe ser válido
    pri = str(data.get("priority_resolved", "")).lower()
    if pri and pri not in VALID_PRIORITIES:
        errors.append(f"❌ priority_resolved: '{pri}' no es válido. Valores: {sorted(VALID_PRIORITIES)}")

    # size debe ser válido
    sz = str(data.get("size", "")).lower()
    if sz and sz not in VALID_SIZES:
        errors.append(f"❌ size: '{sz}' no es válido. Valores: {sorted(VALID_SIZES)}")

    # estimate_hours debe ser número
    est = data.get("estimate_hours")
    if est is not None and not isinstance(est, (int, float)):
        errors.append(f"❌ estimate_hours: debe ser número, no {type(est).__name__}")

    # images debe ser array
    images = data.get("images", [])
    if not isinstance(images, list):
        errors.append("❌ images: debe ser un array")
    else:
        for i, img in enumerate(images):
            if not isinstance(img, dict):
                errors.append(f"❌ images[{i}]: debe ser un objeto")
                continue
            if "path" not in img or not img["path"]:
                errors.append(f"❌ images[{i}]: path requerido")
            if "caption" not in img or not img["caption"]:
                errors.append(f"❌ images[{i}]: caption requerido")

    # references debe ser array si existe
    refs = data.get("references", [])
    if not isinstance(refs, list):
        errors.append("❌ references: debe ser un array")

    # target_repo debe tener formato owner/repo
    repo = data.get("target_repo", "")
    if repo and "/" not in repo:
        errors.append(f"❌ target_repo: debe ser 'owner/repo', no '{repo}'")

    return errors


def main():
    if len(sys.argv) < 2:
        print("Uso: uv run python3 scripts/validate_issue.py output/*.issue.json",
              file=sys.stderr)
        sys.exit(1)

    all_errors = {}
    total = 0
    for arg in sys.argv[1:]:
        for path in sorted(Path(".").glob(arg)) if "*" in arg else [Path(arg)]:
            if not path.exists():
                continue
            total += 1
            errors = validate(str(path))
            if errors:
                all_errors[str(path)] = errors

    # Reportar
    if all_errors:
        for path, errs in all_errors.items():
            print(f"\n📄 {path}:")
            for e in errs:
                print(f"  {e}")
        print(f"\n❌ {len(all_errors)}/{total} archivos con errores")
        sys.exit(1)
    else:
        print(f"✅ {total} archivos validados, 0 errores")


if __name__ == "__main__":
    main()
