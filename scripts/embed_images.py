#!/usr/bin/env python3
"""Embebe imágenes como data URIs y renderiza el template del issue.

Uso:
    uv run python3 scripts/embed_images.py output/archivo.issue.json [templates/issue-body.md]

El script:
1. Lee el JSON con los datos del issue
2. Convierte cada imagen (path local) a data URI base64
3. Renderiza el template Mustache con los datos
4. Guarda el body listo para gh issue create --body-file
"""
import sys, json, base64, re, subprocess, argparse
from pathlib import Path


# ---------------------------------------------------------------------------
# MIME types para imágenes
# ---------------------------------------------------------------------------
MIME_MAP = {
    '.png': 'image/png',
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.gif': 'image/gif',
    '.webp': 'image/webp',
    '.svg': 'image/svg+xml',
    '.bmp': 'image/bmp',
}


def _mime_type(path: str) -> str:
    """Detecta el MIME type según la extensión del archivo."""
    ext = Path(path).suffix.lower()
    return MIME_MAP.get(ext, 'application/octet-stream')


# ---------------------------------------------------------------------------
# Conversión de imágenes a data URIs
# ---------------------------------------------------------------------------
def embed_images(data: dict) -> dict:
    """Convierte las rutas de `images[].path` a data URIs base64.

    Modifica el dict in-place y lo retorna para conveniencia.
    Si una imagen no existe en disco, deja el path vacío.
    """
    for img in data.get('images', []):
        path = img.get('path', '')
        if path and Path(path).is_file():
            try:
                raw = Path(path).read_bytes()
                b64 = base64.b64encode(raw).decode('ascii')
                mime = _mime_type(path)
                img['path'] = f'data:{mime};base64,{b64}'
            except (OSError, ValueError):
                img['path'] = ''  # imagen corrupta o inaccesible
        else:
            img['path'] = ''
    return data


# ---------------------------------------------------------------------------
# Renderizador Mustache mínimo
# ---------------------------------------------------------------------------
def render_template(template: str, data: dict) -> str:
    """Renderiza un template Mustache simple.

    Soporta:
    - ``{{var}}``         → reemplazo de variable simple
    - ``{{#list}}``...``{{/list}}``   → iteración de array
      - ``{{.}}`` dentro  → valor del ítem (strings)
      - ``{{field}}`` dentro → atributo del ítem (dicts)
    """
    result = template

    # 1. Secciones {{#key}} ... {{/key}}
    _sec = re.compile(r'\{\{#(\w+)\}\}(.*?)\{\{/\1\}\}', re.DOTALL)

    def _replace_section(match):
        key = match.group(1)
        body = match.group(2)
        items = data.get(key, [])
        if not items:
            return ''
        rendered = []
        for item in items:
            if isinstance(item, dict):
                tmp = body
                for k, v in item.items():
                    tmp = tmp.replace('{{' + k + '}}', str(v or ''))
                rendered.append(tmp)
            else:
                rendered.append(body.replace('{{.}}', str(item or '')))
        return ''.join(rendered)

    result = _sec.sub(_replace_section, result)

    # 2. Variables simples {{var}}
    for key, value in data.items():
        if not isinstance(value, (list, dict)):
            result = result.replace('{{' + key + '}}', str(value or ''))

    return result


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
BODY_SIZE_LIMIT = 60_000  # 60KB (GitHub max es 65KB, dejamos margen)


def _upload_and_replace(issue_data: dict, repo: str, issue_number: int) -> dict:
    """Sube imágenes al repo y reemplaza paths por URLs."""
    import tempfile, json as _json

    # Recolectar paths de imágenes
    img_paths = [img['path'] for img in issue_data.get('images', []) if img.get('path')]
    if not img_paths:
        return issue_data

    print(f"  Subiendo {len(img_paths)} imágenes al repo...", file=sys.stderr)
    # Llamar a gh_upload_images como subprocess
    cmd = [
        "uv", "run", "python3", "scripts/gh_upload_images.py",
        "--repo", repo,
        "--issue", str(issue_number),
        "--images", _json.dumps(img_paths),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"  ⚠️  Error subiendo imágenes: {r.stderr.strip()[:200]}", file=sys.stderr)
        return issue_data

    urls = _json.loads(r.stdout.strip())
    # Reemplazar paths por URLs (en orden)
    url_idx = 0
    for img in issue_data.get('images', []):
        if img.get('path') and url_idx < len(urls):
            img['path'] = urls[url_idx]
            url_idx += 1
    return issue_data


def main():
    parser = argparse.ArgumentParser(
        description="Embebe imágenes como data URIs o las sube al repo"
    )
    parser.add_argument("json_file", help="output/archivo.issue.json")
    parser.add_argument("template", nargs="?", default="templates/issue-body.md",
                        help="template a usar (default: templates/issue-body.md)")
    parser.add_argument("--upload", action="store_true",
                        help="Subir imágenes al repo en vez de usar data URIs")
    parser.add_argument("--repo", help="owner/repo (requerido con --upload)")
    parser.add_argument("--issue", type=int, help="Número del issue (requerido con --upload)")
    args = parser.parse_args()

    json_path = Path(args.json_file)
    template_path = Path(args.template)
    output_dir = json_path.parent

    if args.upload and (not args.repo or not args.issue):
        print("❌ --upload requiere --repo y --issue", file=sys.stderr)
        sys.exit(1)

    # 1. Leer JSON
    if not json_path.exists():
        print(f"❌ No existe: {json_path}", file=sys.stderr)
        sys.exit(1)
    with open(json_path, encoding='utf-8') as f:
        issue_data = json.load(f)

    # 2. Procesar imágenes según modo
    if args.upload:
        issue_data = _upload_and_replace(issue_data, args.repo, args.issue)
    else:
        issue_data = embed_images(issue_data)

    # 3. Leer template
    if not template_path.exists():
        print(f"❌ No existe: {template_path}", file=sys.stderr)
        sys.exit(1)
    with open(template_path, encoding='utf-8') as f:
        template = f.read()

    # 4. Renderizar
    body = render_template(template, issue_data)

    # 5. Verificar tamaño
    if len(body) > BODY_SIZE_LIMIT and not args.upload:
        print(f"⚠️  Body demasiado grande: {len(body)} bytes (límite 65KB)", file=sys.stderr)
        print(f"💡 Usa --upload --repo owner/repo --issue N para subir imágenes al repo", file=sys.stderr)

    # 6. Guardar body
    stem = json_path.stem.replace('.issue', '')  # archivo.issue.json → archivo
    body_path = output_dir / f'{stem}.body.md'
    body_path.write_text(body, encoding='utf-8')

    # 7. Reportar
    img_count = len(issue_data.get('images', []))
    print(f'✅ Body generado: {body_path}')
    print(f'📏 {len(body)} bytes')
    print(f'🖼️  {img_count} imagen(es) procesada(s)')
    if not args.upload and img_count:
        total_img_bytes = 0
        for img in issue_data.get('images', []):
            uri = img.get('path', '')
            if uri and uri.startswith('data:'):
                total_img_bytes += len(uri) * 3 // 4
        print(f'📦 ~{total_img_bytes // 1024} KB aproximados en imágenes')
    if args.upload:
        print(f'☁️  Imágenes subidas al repo {args.repo}')


if __name__ == '__main__':
    main()
