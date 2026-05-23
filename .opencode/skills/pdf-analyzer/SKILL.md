---
name: pdf-analyzer
description: "Use when processing `.pdf` files in `docs/`. Extract text and images via Python script `scripts/extract_pdf.py` using PyMuPDF."
---
# PDF Analyzer

## Input
- **Archivo**: `docs/<archivo>.pdf`
- **Script**: `scripts/extract_pdf.py`
- **Dependencias**: `pymupdf` (instalado vía `uv sync` (ver pyproject.toml) pymupdf`)

## Extracción
```bash
uv run python3 scripts/extract_pdf.py docs/archivo.pdf
```
Esto genera `output/<archivo>.manifest.json` con estos campos:
- `text_file`: ruta al archivo .txt con el texto extraído
- `images[]`: lista de rutas a imágenes extraídas
- `pages`: número de páginas
- `char_count`: total de caracteres extraídos

## Reglas de negocio (qué buscar en el texto)

| Campo | Señales en el texto | Obligatorio |
|-------|-------------------|:-----------:|
| **title** | Primera línea en **bold**, líneas con "Título:", "Feature:", "Requerimiento:", "# " (markdown heading) | ✅ |
| **description** | Párrafos después del título, secciones "Descripción", "Resumen", "Overview", "Objetivo" | ✅ |
| **acceptance_criteria** | Líneas con "- [ ]", viñetas "1.", "2.", secciones "Criterios", "AC:", "Acceptance Criteria", "Definition of Done" | ❌ |
| **priority** | "Alta/Media/Baja", "High/Medium/Low", "P1/P2/P3", "Must/Should/Could", "Crítica/Alta/Normal" | ❌ |
| **size** | "S/M/L/XL", "Story Points: N", "Talla:", "Tamaño:", "Points:" | ❌ |
| **estimate** | "N horas", "N días", "Estimación:", "Estimated:", "Nh", "Nd" | ❌ |
| **stakeholders** | Menciones de "@usuario", "Solicitante:", "PO:", "Stakeholder:" | ❌ |
| **labels** | "Etiquetas:", "Tags:", "Labels:", "Categoría:" | ❌ |

> Si no encuentras un campo, **omítelo del JSON** (no pongas null). El campo `title` es el único realmente obligatorio; si no aparece, usa el nombre del archivo como fallback y agrega una pregunta en `questions_for_pm`.

## Output contract
```json
{
  "source": "docs/requerimiento.pdf",
  "title": "string (requerido)",
  "description": "string (requerido)",
  "acceptance_criteria": ["string"],
  "priority": "string",
  "size": "string",
  "estimate_hours": "number",
  "labels": ["string"],
  "images": [
    {
      "path": "string (ruta a la imagen)",
      "caption": "string (descripción breve)",
      "analysis": "string (ruta al JSON de vision)"
    }
  ],
  "stakeholders": ["string"],
  "questions_for_pm": ["string"]
}
```

## Edge cases
| Caso | Qué hacer |
|------|-----------|
| **PDF escaneado** (0 chars extraídos) | Preguntar al usuario si quiere OCR externo. Agregar `questions_for_pm: ["El PDF parece escaneado (sin texto extraíble). ¿Usar OCR?"]` |
| **0 imágenes extraídas** | `images: []` y saltar el paso de delegación a vision |
| **Texto ambiguo o incompleto** | Agregar pregunta en `questions_for_pm` |
| **Más de 20 imágenes** | Procesar en lotes de 5, no una por una |
| **Sin título detectable** | Usar `nombre_del_archivo` como título y agregar `questions_for_pm` |
| **Multi-idioma** | Extraer todo el texto, mantener idioma original |

## Validación del output
- `source` debe existir en disco
- `title` no puede estar vacío
- Cada `images[].path` debe existir en disco (si no, sacarlo del array)
- `char_count > 0` (si es 0, activar edge case de escaneado)

## Ejemplo concreto
```
docs/login-oauth.pdf
→ uv run python3 scripts/extract_pdf.py docs/login-oauth.pdf
→ manifest: 3 páginas, 2 imágenes
→ analyzer extrae: title="Login con Google OAuth", description="..."
→ JSON final guardado en output/login-oauth.issue.json
```
