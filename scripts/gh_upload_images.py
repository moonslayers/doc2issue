#!/usr/bin/env python3
"""Sube imágenes al repo vía Content API para usarlas en issues.

GitHub limita el body de issues a 65KB. Las imágenes en base64 lo superan.
Este script sube las imágenes al repo y retorna URLs ?raw=true.

Uso:
    uv run python3 scripts/gh_upload_images.py --repo owner/repo --issue 1345 \\
      --images '["ruta1.png","ruta2.png"]'
"""
import sys, json, subprocess, base64, argparse, os, time
import urllib.parse
from pathlib import Path
from utils import load_env


def upload_image(repo: str, issue_number: int, image_path: str,
                 max_retries: int = 3) -> str | None:
    """Sube una imagen al repo y retorna la URL ?raw=true.

    La imagen se guarda en .issue-assets/{issue_number}/{nombre}.
    Si ya existe, la salta (idempotente).
    """
    img = Path(image_path)
    if not img.exists():
        print(f"⚠️  No existe: {image_path}", file=sys.stderr)
        return None

    # Ruta en el repo: .issue-assets/{issue}/{nombre}
    repo_path = f".issue-assets/{issue_number}/{img.name}"

    # Verificar si ya existe
    check = subprocess.run(
        ["gh", "api", f"repos/{repo}/contents/{repo_path}",
         "--jq", ".download_url", "--silent"],
        capture_output=True, text=True,
    )
    if check.returncode == 0 and check.stdout.strip():
        # Construir URL github.com/blob (la de la API tiene token temporal)
        existing_url = f"https://github.com/{repo}/blob/main/.issue-assets/{issue_number}/{urllib.parse.quote(img.name)}?raw=true"
        print(f"  ↳ Ya existe: {existing_url}", file=sys.stderr)
        return existing_url

    # Leer y codificar imagen
    with open(img, "rb") as f:
        content_b64 = base64.b64encode(f.read()).decode("ascii")

    # Preparar payload en archivo temporal (evita "Argument list too long")
    payload = json.dumps({
        "message": f"docs: add issue asset #{issue_number} - {img.name}",
        "content": content_b64,
        "branch": "main",
    })
    payload_path = Path(f"/tmp/doc2issue_upload_{issue_number}_{img.name}.json")
    payload_path.write_text(payload)

    for attempt in range(max_retries):
        r = subprocess.run(
            ["gh", "api", f"repos/{repo}/contents/{repo_path}",
             "--method", "PUT",
             "--input", str(payload_path),
             "--jq", ".content.download_url"],
            capture_output=True, text=True,
        )
        if r.returncode == 0:
            # Ignorar URL de la API, construir URL github.com/blob
            raw_url = f"https://github.com/{repo}/blob/main/.issue-assets/{issue_number}/{urllib.parse.quote(img.name)}?raw=true"
            print(f"  ✅ Subida: {raw_url}", file=sys.stderr)
            payload_path.unlink()
            return raw_url

        print(f"  ⚠️  Intento {attempt+1} falló: {r.stderr.strip()[:100]}",
              file=sys.stderr)
        if attempt < max_retries - 1:
            time.sleep(2)

    payload_path.unlink()
    print(f"  ❌ No se pudo subir tras {max_retries} intentos",
          file=sys.stderr)
    return None


def main():
    load_env()
    parser = argparse.ArgumentParser(
        description="Sube imágenes al repo para usarlas en issues"
    )
    parser.add_argument("--repo", required=True, help="owner/repo")
    parser.add_argument("--issue", required=True, type=int,
                        help="Número del issue")
    parser.add_argument("--images", required=True,
                        help='JSON array de rutas: ["ruta1.png","ruta2.png"]')
    args = parser.parse_args()

    images = json.loads(args.images)
    if not images:
        print("[]")
        return

    print("Subiendo imágenes...", file=sys.stderr)
    urls = []
    for img_path in images:
        url = upload_image(args.repo, args.issue, img_path)
        if url:
            urls.append(url)

    print(json.dumps(urls, indent=2))


if __name__ == "__main__":
    main()
