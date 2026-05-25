#!/usr/bin/env python3
"""Extrae texto y renderiza cada página como imagen PNG (full slide).

Reemplaza la extracción de imágenes incrustadas individuales por
el renderizado de la página completa, preservando el contexto visual
(diagramas, flechas, logos, footers) que el agente vision necesita.

Uso:
    uv run python3 scripts/extract_pdf.py docs/archivo.pdf [output/]
"""
import sys, json
from pathlib import Path
import fitz  # pymupdf


def extract(pdf_path: str, output_dir: str = "output"):
    pdf = Path(pdf_path)
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "images").mkdir(exist_ok=True)

    doc = fitz.open(pdf)
    text_parts = []
    images = []

    for page_num, page in enumerate(doc, 1):
        # Texto de la página
        text_parts.append(f"## Página {page_num}\n{page.get_text()}")

        # Renderizar página COMPLETA como PNG (200 DPI)
        pix = page.get_pixmap(dpi=200)
        img_name = f"{pdf.stem}_slide_{page_num:03d}.png"
        img_path = out / "images" / img_name
        pix.save(str(img_path))
        pix = None  # liberar memoria
        images.append(str(img_path))

    txt_path = out / f"{pdf.stem}.txt"
    txt_path.write_text("\n\n".join(text_parts), encoding="utf-8")

    manifest = {
        "source": str(pdf),
        "type": "pdf",
        "text_file": str(txt_path),
        "pages": len(doc),
        "images": images,
        "char_count": sum(len(p) for p in text_parts),
        "image_type": "full_page",
    }
    (out / f"{pdf.stem}.manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: uv run python3 scripts/extract_pdf.py docs/archivo.pdf [output/]",
              file=sys.stderr)
        sys.exit(1)
    extract(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "output")
