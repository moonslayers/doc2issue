#!/usr/bin/env python3
"""Extrae texto e imágenes de un PDF usando PyMuPDF (reemplaza pdftotext + pdfimages)."""
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
        text_parts.append(f"## Página {page_num}\n{page.get_text()}")
        for img_idx, img in enumerate(page.get_images(), 1):
            xref = img[0]
            base_image = doc.extract_image(xref)
            img_bytes = base_image["image"]
            ext = base_image["ext"]
            img_name = f"{pdf.stem}_p{page_num}_{img_idx}.{ext}"
            img_path = out / "images" / img_name
            img_path.write_bytes(img_bytes)
            images.append(str(img_path))

    txt_path = out / f"{pdf.stem}.txt"
    txt_path.write_text("\n\n".join(text_parts), encoding="utf-8")

    manifest = {
        "source": str(pdf),
        "type": "pdf",
        "text_file": str(txt_path),
        "pages": len(doc),
        "images": images,
        "char_count": sum(len(p) for p in text_parts)
    }
    (out / f"{pdf.stem}.manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(json.dumps(manifest, indent=2))

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python3 scripts/extract_pdf.py docs/archivo.pdf [output/]", file=sys.stderr)
        sys.exit(1)
    extract(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "output")
