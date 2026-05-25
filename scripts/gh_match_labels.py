#!/usr/bin/env python3
"""Mapea labels de un JSON a labels existentes en un repo de GitHub.

Busca los labels más cercanos por similitud de texto (Levenshtein).
Si un label no tiene match cercano, lo omite con un warning.

Uso:
    uv run python3 scripts/gh_match_labels.py --repo owner/repo --labels '["lab1","lab2"]'
"""
import sys, json, subprocess, argparse, os
from utils import load_env


def levenshtein(a: str, b: str) -> int:
    """Distancia de Levenshtein entre dos strings (case-insensitive)."""
    a, b = a.lower(), b.lower()
    if len(a) < len(b):
        a, b = b, a
    if not b:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a):
        curr = [i + 1]
        for j, cb in enumerate(b):
            cost = 0 if ca == cb else 1
            curr.append(min(curr[j] + 1, prev[j + 1] + 1, prev[j] + cost))
        prev = curr
    return prev[-1]


def normalize(name: str) -> str:
    """Normaliza un label para comparación: lowercase, sin acentos, sin espacios."""
    import unicodedata
    name = name.lower().strip()
    name = unicodedata.normalize('NFKD', name).encode('ascii', 'ignore').decode('ascii')
    return name.replace('-', '').replace('_', '').replace(' ', '')


def fetch_repo_labels(repo: str) -> list[dict]:
    """Obtiene labels existentes del repo."""
    r = subprocess.run(
        ["gh", "label", "list", "--repo", repo,
         "--limit", "200",
         "--json", "name,description,color"],
        capture_output=True, text=True, check=True,
    )
    return json.loads(r.stdout)


def match_labels(desired: list[str], repo: str,
                 threshold: float = 0.4) -> dict:
    """Mapea labels deseados a labels existentes del repo.

    Retorna:
    - matched: {label_deseado: label_existente}
    - unmatched: [labels sin match]
    - all_found: [labels existentes únicos a usar]
    """
    existing = fetch_repo_labels(repo)
    existing_names = [e["name"] for e in existing]

    matched = {}
    unmatched = []

    for desired_label in desired:
        dl_norm = normalize(desired_label)

        # Buscar match exacto (case-insensitive)
        exact = [e for e in existing_names if e.lower() == desired_label.lower()]
        if exact:
            matched[desired_label] = exact[0]
            continue

        # Buscar por similitud
        scores = []
        for ex in existing_names:
            ex_norm = normalize(ex)
            dist = levenshtein(dl_norm, ex_norm)
            max_len = max(len(dl_norm), len(ex_norm))
            similarity = 1 - (dist / max_len) if max_len > 0 else 0
            scores.append((similarity, ex))

        scores.sort(key=lambda x: x[0], reverse=True)
        best_score, best_label = scores[0] if scores else (0, "")

        if best_score >= threshold:
            matched[desired_label] = best_label
        else:
            unmatched.append(desired_label)

    all_found = list(set(matched.values()))
    return {"matched": matched, "unmatched": unmatched, "all_found": all_found}


def main():
    load_env()
    parser = argparse.ArgumentParser(
        description="Mapea labels a labels existentes en un repo"
    )
    parser.add_argument("--repo", required=True, help="owner/repo")
    parser.add_argument("--labels", required=True,
                        help='JSON array: ["lab1","lab2"]')
    parser.add_argument("--threshold", type=float, default=0.4,
                        help="Similitud mínima (0-1, default: 0.4)")
    args = parser.parse_args()

    try:
        desired = json.loads(args.labels)
        result = match_labels(desired, args.repo, args.threshold)
        print(json.dumps(result, indent=2, ensure_ascii=False))

        if result["unmatched"]:
            print(f"\n⚠️  Labels sin match: {result['unmatched']}",
                  file=sys.stderr)

    except subprocess.CalledProcessError as e:
        print(f"❌ Error gh: {e.stderr.strip()}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError:
        print("❌ --labels debe ser un JSON array válido", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
