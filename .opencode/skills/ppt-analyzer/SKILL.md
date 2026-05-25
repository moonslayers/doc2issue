---
name: ppt-analyzer
description: "Use for `.pptx` files in `docs/`. Extract slides, presenter notes and images via Python script `scripts/extract_pptx.py` using python-pptx."
---
# PPT Analyzer

## Input
- **Archivo**: `docs/<archivo>.pptx`
- **Script**: `scripts/extract_pptx.py`
- **Dependencias**: `python-pptx` (instalado vía `uv sync` (ver pyproject.toml) python-pptx`)

## Extracción
```bash
uv run python3 scripts/extract_pptx.py docs/archivo.pptx
```
Esto genera `output/<archivo>.manifest.json` con estos campos:
- `markdown_file`: ruta al .md con texto de slides + notas del presentador
- `slides`: número total de slides
- `images[]`: lista de rutas a imágenes extraídas

## Reglas de negocio (qué buscar en el texto)

| Campo | Señales en el texto (slides + notas) | Obligatorio |
|-------|-------------------------------------|:-----------:|
| **title** | Título del primer slide, texto del slide principal, "Proyecto:", "Feature:" | ✅ |
| **description** | Contenido de los slides de detalle, **notas del presentador** (¡muy importantes!) | ✅ |
| **acceptance_criteria** | Slides con viñetas numeradas, secciones "Requerimientos", "Requirements", "AC" | ❌ |
| **priority** | "Alta/Media/Baja" en slides o notas, colores en diagramas (rojo=alta, verde=baja) | ❌ |
| **size** | "S/M/L/XL" mencionado | ❌ |
| **stakeholders** | Nombres en notas del presentador, "PO:", "Cliente:" | ❌ |

> Las **notas del presentador** suelen contener la información más valiosa: detalles técnicos, decisiones de diseño, y requirements que no están en los slides. No las ignores.



> **Importante**: Si el documento contiene múltiples requerimientos, el analyzer debe generar
> UN archivo `.issue.json` por cada uno. NO combinarlos en un solo issue.

## Output contract
```json
{
  "source": "docs/presentacion.pptx",
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
  "questions_for_pm": ["string"]
}
```

## Edge cases

## References (opcional)
Vincular este documento con otros archivos relacionados:
```json
{
  "references": [
    {"type": "data", "path": "output/archivo.batch.json", "description": "Datos relacionados"}
  ]
}
```
## Edge cases
| Caso | Qué hacer |
|------|-----------|
| **PPTX sin notas** | Analizar solo slides, no generar advertencia |
| **Solo imágenes (sin texto)** | `images` tendrá las imágenes, delegar a vision |
| **Muchos slides (>30)** | Priorizar los primeros 5 y el último (suelen tener resumen) |
| **Slide master vs contenido** | Ignorar texto repetitivo de layouts/navegación |

## Validación del output
- `source` debe existir en disco
- `title` no puede estar vacío
- Verificar que slides del manifest coinciden con el markdown generado

## Ejemplo concreto
```
docs/dashboard-feature.pptx
→ uv run python3 scripts/extract_pptx.py docs/dashboard-feature.pptx
→ manifest: 12 slides, 5 imágenes, notas del slide 8 tienen detalles técnicos
→ title="Nuevo Dashboard", description incluye notas del presentador
→ JSON en output/dashboard-feature.issue.json
```
