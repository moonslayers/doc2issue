---
name: excel-analyzer
description: "Use for `.xlsx`, `.xls`, `.csv` files in `docs/`. Convert tabular data to JSON batch via Python script `scripts/extract_xlsx.py` using pandas."
---
# Excel Analyzer

## Input
- **Archivo**: `docs/<archivo>.xlsx`, `.xls`, o `.csv`
- **Script**: `scripts/extract_xlsx.py`
- **Dependencias**: `pandas`, `openpyxl` (instalado vía `uv tool install pandas openpyxl`)

## Extracción
```bash
python3 scripts/extract_xlsx.py docs/archivo.xlsx
```
Esto genera `output/<archivo>.batch.json` con:
- `rows[]`: array de objetos, cada fila del Excel es un registro
- `count`: número total de filas
- `type`: "xlsx" o "csv"

También genera `output/<archivo>.manifest.json` para consistencia con los otros formatos.

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

## Output contract (por fila)
Cada fila se convierte en un objeto dentro de `rows[]`. Luego el analyzer genera un issue por fila:

```json
{
  "source": "docs/backlog.xlsx",
  "title": "string (de la columna Title)",
  "description": "string (de la columna Description)",
  "priority": "string",
  "size": "string",
  "labels": ["string"],
  "stakeholders": ["string"]
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
docs/backlog-sprint-24.xlsx
→ python3 scripts/extract_xlsx.py docs/backlog-sprint-24.xlsx
→ batch.json: 15 filas con columnas Title, Description, Priority, Size
→ analyzer genera 15 issues, uno por fila
→ JSON batch en output/backlog-sprint-24.batch.json
```
