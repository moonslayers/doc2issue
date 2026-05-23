#!/usr/bin/env python3
"""Extrae texto slide por slide + imágenes + notas de un PPTX."""
import sys, json, zipfile
from pathlib import Path
from pptx import Presentation

def extract(pptx_path: str, output_dir: str = "output"):
    pptx = Path(pptx_path)
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "images").mkdir(exist_ok=True)

    prs = Presentation(pptx)
    slides_text = []

    for i, slide in enumerate(prs.slides, 1):
        texts = []
        for shape in slide.shapes:
            if shape.has_text_frame:
                texts.append(shape.text_frame.text)
        notes = slide.notes_slide.notes_text_frame.text if slide.has_notes_slide else ""
        slides_text.append(f"## Slide {i}\n" + "\n".join(texts) +
                          (f"\n\n**Notas:** {notes}" if notes else ""))

    images = []
    with zipfile.ZipFile(pptx) as z:
        for name in z.namelist():
            if name.startswith("ppt/media/"):
                img_name = f"{pptx.stem}_{Path(name).name}"
                img_path = out / "images" / img_name
                img_path.write_bytes(z.read(name))
                images.append(str(img_path))

    md_path = out / f"{pptx.stem}.md"
    md_path.write_text("\n\n---\n\n".join(slides_text), encoding="utf-8")

    manifest = {
        "source": str(pptx),
        "type": "pptx",
        "markdown_file": str(md_path),
        "slides": len(prs.slides),
        "images": images
    }
    (out / f"{pptx.stem}.manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(json.dumps(manifest, indent=2))

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python3 scripts/extract_pptx.py docs/archivo.pptx [output/]", file=sys.stderr)
        sys.exit(1)
    extract(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "output")
