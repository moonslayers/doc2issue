#!/usr/bin/env python3
"""Extrae texto e imágenes de un DOCX usando mammoth + zipfile (reemplaza pandoc + unzip)."""
import sys, json, zipfile
from pathlib import Path
import mammoth

def extract(docx_path: str, output_dir: str = "output"):
    docx = Path(docx_path)
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "images").mkdir(exist_ok=True)

    images = []
    with zipfile.ZipFile(docx) as z:
        for name in z.namelist():
            if name.startswith("word/media/"):
                img_name = f"{docx.stem}_{Path(name).name}"
                img_path = out / "images" / img_name
                img_path.write_bytes(z.read(name))
                images.append(str(img_path))

    with open(docx, "rb") as f:
        result = mammoth.convert_to_markdown(f)

    md_path = out / f"{docx.stem}.md"
    md_path.write_text(result.value, encoding="utf-8")

    manifest = {
        "source": str(docx),
        "type": "docx",
        "markdown_file": str(md_path),
        "images": images,
        "warnings": [str(w) for w in result.messages]
    }
    (out / f"{docx.stem}.manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(json.dumps(manifest, indent=2))

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python3 scripts/extract_docx.py docs/archivo.docx [output/]", file=sys.stderr)
        sys.exit(1)
    extract(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "output")
