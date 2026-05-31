---
name: excel-analyzer
description: "Use for `.xlsx`, `.xls`, `.csv` files in `docs/`. Convert tabular data to JSON batch via Python script `scripts/extract_xlsx.py` using pandas."
---
# Excel Analyzer

## Input
- **Archivo**: `docs/<proyecto>/<archivo>.xlsx`, `.xls`, o `.csv`
- **Script**: `scripts/extract_xlsx.py`
- **Dependencias**: `pandas`, `openpyxl` (instalado vía `uv sync` (ver pyproject.toml) pandas openpyxl`)

## Extracción
```bash
uv run python3 scripts/extract_xlsx.py "docs/<proyecto>/<archivo>.xlsx" "output/issues/<proyecto>/data"
```
Esto genera `output/issues/<proyecto>/data/<archivo>.batch.json` con:
- `rows[]`: array de objetos, cada fila del Excel es un registro
- `count`: número total de filas
- `type`: "xlsx" o "csv"

También genera `output/issues/<proyecto>/data/<archivo>.manifest.json` para consistencia con los otros formatos.

## Reglas de negocio (mapeo de columnas)

Cada fila del Excel puede representar un issue. Identifica estas columnas por nombre (case-insensitive, parcial):

| Campo del issue | Columnas a buscar en el Excel |
|----------------|------------------------------|
| **title** | "Title", "Name", "Feature", "Requerimiento", "Nombre", "Item", "Tarea", "Task" |
| **description** | "Description", "Descripción", "Detail", "Notas", "Comments", "Detalle" |
| **priority** | "Priority", "Prioridad", "P1"-"P5", "Severity", "Severidad", "Urgency", "Urgencia" |
| **size** | "Size", "Tamaño", "Story Points", "SP", "Effort", "Esfuerzo", "Complexity" |
| **estimate** | "Estimate", "Estimación", "Hours", "Horas", "Days", "Días" |
| **labels** | "Label", "Tag", "Category", "Categoría", "Type", "Tipo", "Área", "Area" |
| **stakeholder** | "Stakeholder", "Solicitante", "Owner", "Assignee", "Responsable" |
| **status** | "Status", "Estado", "Stage", "Etapa" (informacional, no se mapea a issue) |

> Si una columna no coincide con ningún campo conocido, **incluirla igual en el registro** del JSON. El analyzer decidirá después si usarla o no.



> **Importante**: Si el documento contiene múltiples requerimientos, el analyzer debe generar
> UN archivo `.issue.json` por cada uno. NO combinarlos en un solo issue.

## Output contract (por fila)
Cada fila se convierte en un objeto dentro de `rows[]`. Luego el analyzer genera un issue por fila:

```json
{
  "source": "docs/<proyecto>/backlog.xlsx",
  "title": "string (de la columna Title)",
  "description": "string (de la columna Description)",
  "priority": "string",
  "size": "string",
  "labels": ["string"],
  "project_fields": {},  // << objeto dinámico: el analyzer lo llena con los nombres reales del project
  "stakeholders": ["string"]
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
| **Header en segunda fila** | Usar primera fila como header siempre (pandas lo hace por defecto) |
| **Celdas vacías** | Se convierten a `null` en JSON, al generar issue se omiten |
| **Columnas irreconocibles** | Incluirlas igual en el registro, con su nombre original |
| **CSV con separador no estándar** | pandas detecta automáticamente `;` o `,` |
| **Muchas filas (>50)** | Sugerir al usuario que procese en lotes pequeños |
| **Sheet específico** | Si el Excel tiene múltiples sheets, procesar solo "Sheet1" o preguntar al usuario |

## Validación del output
- `count > 0` (Excel con datos)
- Cada fila debe tener al menos un campo con valor
- Si `count > 50`, advertir al usuario

## Ejemplo concreto
```
docs/mi-proyecto/backlog-sprint-24.xlsx
→ uv run python3 scripts/extract_xlsx.py "docs/mi-proyecto/backlog-sprint-24.xlsx" "output/issues/mi-proyecto/data"
→ batch.json: 15 filas con columnas Title, Description, Priority, Size (en output/issues/mi-proyecto/data/)
→ analyzer genera 15 issues, uno por fila
→ JSONs en output/issues/mi-proyecto/backlog-sprint-24_N.issue.json
```
