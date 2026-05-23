---
name: pdf-analyzer
description: "Use when processing `.pdf` files with `pdftotext` and `pdfimages` — extract text, extract embedded images, analyze requirements from PDFs in `docs/`."
---
# PDF Analyzer

## Cuándo usar
Archivos `.pdf` en `docs/`. Pueden ser texto puro, escaneados o mixtos (texto + imágenes).

## Proceso

1. Extraer texto:
   ```bash
   pdftotext docs/archivo.pdf output/archivo.txt
   ```

2. Extraer imágenes (si es mixto):
   ```bash
   mkdir -p output/images
   pdfimages -png docs/archivo.pdf output/images/archivo
   ```

3. Analizar el texto buscando:
   - Título del requerimiento
   - Descripción funcional
   - Criterios de aceptación
   - Prioridad mencionada
   - Estimaciones

4. Delegar imágenes al agente `vision`

## Output
JSON en `output/<nombre>.issue.json`
