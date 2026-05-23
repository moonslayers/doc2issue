---
name: word-parser
description: "Use for `.docx` files: convert to Markdown via `pandoc`, extract embedded images using `unzip`."
---
# Word Parser

## Cuándo usar
Archivos `.docx` en `docs/`.

## Proceso

1. Extraer a markdown:
   ```bash
   pandoc docs/archivo.docx -t markdown -o output/archivo.md
   ```

2. Extraer imágenes incrustadas (si las hay):
   ```bash
   unzip -o docs/archivo.docx -d output/docx_temp/
   cp output/docx_temp/word/media/* output/images/
   rm -rf output/docx_temp/
   ```

3. Analizar el markdown resultante

4. Delegar imágenes al agente `vision`

## Output
JSON en `output/<nombre>.issue.json`
