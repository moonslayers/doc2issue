#!/usr/bin/env python3
"""Integra los análisis de vision en el issue.json.

Toma el manifest.json (que tiene images[]) y los JSONs generados por
vision (uno por slide), y asigna cada análisis al campo images[].analysis.

Uso:
    uv run python3 scripts/merge_vision.py output/manifest.json \
      output/images/*.json > output/enriched.issue.json
"""
import sys, json
from pathlib import Path


def merge(manifest_path: str, vision_jsons: list[str]) -> dict:
    """Fusiona análisis de vision en el manifest.

    Para cada imagen en manifest.images[], busca el JSON de vision
    correspondiente por nombre de archivo y asigna su contenido
    al campo 'analysis'.
    """
    with open(manifest_path) as f:
        manifest = json.load(f)

    # Indexar JSONs de vision por nombre base (ej: "slide_001" → path)
    vision_map = {}
    for vp in vision_jsons:
        stem = Path(vp).stem  # "slide_001.json" → "slide_001"
        # También buscar por patrón parcial
        vision_map[stem] = vp
        # Versión sin la extensión
        if '_' in stem:
            parts = stem.rsplit('_', 1)
            if len(parts) == 2:
                vision_map[parts[1]] = vp  # "001" → path

    # Asignar análisis a cada imagen
    enriched_count = 0
    for img in manifest.get("images", []):
        img_path = Path(img.get("path", ""))
        img_stem = img_path.stem  # "presentacion_slide_001"

        # Buscar JSON de vision
        vision_path = None
        # 1. Por nombre exacto
        if img_stem in vision_map:
            vision_path = vision_map[img_stem]
        # 2. Por último segmento después de _
        elif '_' in img_stem:
            suffix = img_stem.rsplit('_', 1)[-1]
            if suffix in vision_map:
                vision_path = vision_map[suffix]
        # 3. Por patrón de slide
        for key in vision_map:
            if key in img_stem or img_stem in key:
                vision_path = vision_map[key]
                break

        if vision_path:
            try:
                with open(vision_path) as f:
                    vision_data = json.load(f)
                img["analysis"] = json.dumps(vision_data, ensure_ascii=False)
                enriched_count += 1
            except (json.JSONDecodeError, OSError):
                pass

    manifest["vision_enriched"] = enriched_count
    return manifest


def main():
    if len(sys.argv) < 3:
        print("Uso: uv run python3 scripts/merge_vision.py output/manifest.json output/images/*.json",
              file=sys.stderr)
        sys.exit(1)

    manifest_path = sys.argv[1]
    vision_jsons = sys.argv[2:]

    if not Path(manifest_path).exists():
        print(f"❌ No existe: {manifest_path}", file=sys.stderr)
        sys.exit(1)

    result = merge(manifest_path, vision_jsons)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print(f"\n✅ {result['vision_enriched']}/{len(result.get('images',[]))} imágenes enriquecidas",
          file=sys.stderr)


if __name__ == "__main__":
    main()
