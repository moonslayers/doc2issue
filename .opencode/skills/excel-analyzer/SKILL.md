---
name: excel-analyzer
description: "Use for `.xlsx`, `.xls`, `.csv` files: read with `pandas`, map columns to issue fields, generate one JSON per row."
---
# Excel Analyzer

## Cuándo usar
Archivos `.xlsx`, `.xls`, `.csv` en `docs/`. Típicamente backlogs o matrices de requerimientos.

## Proceso

1. Detectar formato y leer con pandas:
   ```python
   import pandas as pd
   df = pd.read_excel('docs/archivo.xlsx')
   # o pd.read_csv() si es CSV
   ```

2. Identificar columnas comunes:
   - "Title", "Name", "Feature" → title
   - "Description" → description
   - "Priority" → priority
   - "Story Points", "Size" → size
   - "Estimate", "Hours" → estimate

3. Generar UN JSON por cada fila (un issue por fila)

## Output
Array de JSONs en `output/<nombre>.batch.json`
