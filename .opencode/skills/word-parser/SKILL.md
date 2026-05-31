---
name: word-parser
description: "Use for `.docx` files in `docs/`. Convert to Markdown and extract images via Python script `scripts/extract_docx.py` using mammoth."
---
# Word Parser

## Input
- **Archivo**: `docs/<proyecto>/<archivo>.docx`
- **Script**: `scripts/extract_docx.py`
- **Dependencias**: `mammoth`, `python-docx` (instalado vía `uv sync` (ver pyproject.toml) mammoth python-docx`)

## Extracción
```bash
uv run python3 scripts/extract_docx.py "docs/<proyecto>/<archivo>.docx" "output/issues/<proyecto>/data"
```
Esto genera `output/issues/<proyecto>/data/<archivo>.manifest.json` con estos campos:
- `markdown_file`: ruta al archivo .md convertido (`output/issues/<proyecto>/data/<archivo>.md`)
- `images[]`: lista de rutas a imágenes extraídas (`output/issues/<proyecto>/data/images/...`)
- `warnings[]`: advertencias de conversión

## Reglas de negocio (qué buscar en el texto)

| Campo | Señales en el texto (markdown) | Obligatorio |
|-------|-------------------------------|:-----------:|
| **title** | Primer `# Heading 1`, texto de portada, "Título:", "Proyecto:", "Feature:" | ✅ |
| **description** | Párrafos después del H1, secciones "Descripción", "Objetivo", "Scope", "Alcance" | ✅ |
| **acceptance_criteria** | Listas con `- [ ]`, listas numeradas (`1.`), "Criterios de aceptación", "Definition of Done", "DoD" | ❌ |
| **priority** | "Alta/Media/Baja", "High/Medium/Low", "P1/P2/P3", "Must/Should/Could" | ❌ |
| **size** | "S/M/L/XL", "Story Points: N", "Puntos:" | ❌ |
| **estimate** | "N horas", "N días", "Estimación:", "Duración:" | ❌ |
| **stakeholders** | "@usuario", "Responsable:", "Solicitante:", "Área:" | ❌ |

> Si no encuentras un campo, **omítelo del JSON**. Usa el nombre del archivo como fallback para `title`.



> **Importante**: Si el documento contiene múltiples requerimientos, el analyzer debe generar
> UN archivo `.issue.json` por cada uno. NO combinarlos en un solo issue.

## Output contract
```json
{
  "source": "docs/<proyecto>/requerimiento.docx",
  "title": "string (requerido)",
  "description": "string (requerido)",
  "acceptance_criteria": ["string"],
  "priority": "string",
  "size": "string",
  "estimate_hours": "number",
  "labels": ["string"],
  "images": [
    {
      "path": "string",
      "caption": "string",
      "analysis": "string"
    }
  ],
  "stakeholders": ["string"],
  "project_fields": {},  // << objeto dinámico: el analyzer lo llena con los nombres reales del project
  "questions_for_pm": ["string"]
}
```

## Edge cases

## References (opcional)
Vincular este documento con otros archivos relacionados:
```json
{
  "references": [
    {"type": "data", "path": "output/issues/<proyecto>/data/archivo.batch.json", "description": "Datos relacionados"}
  ]
}
```
## Edge cases
| Caso | Qué hacer |
|------|-----------|
| **DOCX sin imágenes** | `images: []`, saltar vision |
| **Markdown vacío** | Preguntar al usuario si el documento está protegido |
| **Warnings de mammoth** | Incluirlos en `questions_for_pm` si son relevantes |
| **Solo tablas (sin texto)** | Extraer tablas como descripción |

## Validación del output
- `source` debe existir en disco
- `title` no puede estar vacío
- `markdown_file` debe existir en `output/issues/<proyecto>/data/` (según manifest)

## Ejemplo concreto
```
docs/mi-proyecto/especificacion-pagos.docx
→ uv run python3 scripts/extract_docx.py "docs/mi-proyecto/especificacion-pagos.docx" "output/issues/mi-proyecto/data"
→ manifest: markdown_file, 0 imágenes (en output/issues/mi-proyecto/data/)
→ title="Especificación Módulo de Pagos", description="..."
→ JSON en output/issues/mi-proyecto/especificacion-pagos.issue.json
```
