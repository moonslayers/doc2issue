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
import sys, json, base64, re, argparse
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
    - Si la ruta es URL (http/https): la deja intacta
    - Si es data URI: la deja intacta
    - Si es archivo local: la convierte a data URI base64
    - Si no existe: la deja vacía
    """
    for img in data.get('images', []):
        path = img.get('path', '')
        if not path:
            continue
        # URLs y data URIs se dejan intactas
        if path.startswith(('http://', 'https://', 'data:')):
            continue
        if Path(path).is_file():
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



def main():
    parser = argparse.ArgumentParser(
        description="Embebe imágenes como data URIs y renderiza el template del issue"
    )
    parser.add_argument("json_file", help="output/archivo.issue.json")
    parser.add_argument("template", nargs="?", default="templates/issue-body.md",
                        help="template a usar (default: templates/issue-body.md)")
    parser.add_argument("--text-only", action="store_true",
                        help="Generar body sin imágenes (para crear issue primero, luego subir imágenes)")
    args = parser.parse_args()

    json_path = Path(args.json_file)
    template_path = Path(args.template)
    output_dir = json_path.parent

    # 1. Leer JSON
    if not json_path.exists():
        print(f"❌ No existe: {json_path}", file=sys.stderr)
        sys.exit(1)
    with open(json_path, encoding='utf-8') as f:
        issue_data = json.load(f)

    # 2. Procesar imágenes
    if args.text_only:
        # Guardar imágenes para después, generar body sin ellas
        issue_data["_images_backup"] = issue_data.get("images", [])
        issue_data["images"] = []
        print("  📝 Body solo texto (sin imágenes)", file=sys.stderr)
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
    if len(body) > BODY_SIZE_LIMIT:
        print(f"⚠️  Body demasiado grande: {len(body)} bytes (límite 65KB)", file=sys.stderr)
        print(f"💡 Las imágenes se suben al repo con gh_upload_images.py", file=sys.stderr)

    # 6. Guardar body
    stem = json_path.stem.replace('.issue', '')  # archivo.issue.json → archivo
    body_path = output_dir / f'{stem}.body.md'
    body_path.write_text(body, encoding='utf-8')

    # 7. Reportar
    img_count = len(issue_data.get('_images_backup', issue_data.get('images', [])))
    print(f'✅ Body generado: {body_path}')
    print(f'📏 {len(body)} bytes')
    print(f'🖼️  {img_count} imagen(es) en total')
    if args.text_only:
        print(f'💡 Usa gh issue edit <N> --body-file para agregar imágenes después')
    elif img_count:
        total_img_bytes = 0
        for img in issue_data.get('images', []):
            uri = img.get('path', '')
            if uri and uri.startswith('data:'):
                total_img_bytes += len(uri) * 3 // 4
        print(f'📦 ~{total_img_bytes // 1024} KB aproximados en imágenes')



if __name__ == '__main__':
    main()
