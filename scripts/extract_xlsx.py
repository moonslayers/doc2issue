#!/usr/bin/env python3
"""Convierte Excel/CSV a JSON batch. Detecta fila real de headers.

Los XLSX reales suelen tener 1-7 filas de metadatos antes de los
encabezados. Este script detecta automáticamente la fila de headers
o acepta un flag explícito --header-row.

Uso:
    uv run python3 scripts/extract_xlsx.py docs/archivo.xlsx [output/] [--header-row N]
"""
import sys, json
from pathlib import Path
import pandas as pd


def _detect_header_row(df, min_cols: int = 5) -> int:
    """Busca la primera fila con ≥min_cols celdas no vacías (heurística)."""
    for i in range(min(20, len(df))):
        non_null = df.iloc[i].dropna()
        if len(non_null) >= min_cols:
            return i
    return 0


def _extract_metadata(df, up_to_row: int) -> dict:
    """Extrae metadatos de las filas superiores a los headers."""
    meta = {}
    for i in range(up_to_row):
        row = df.iloc[i].dropna()
        vals = row.values
        if len(vals) >= 2:
            meta[str(vals[0])] = str(vals[1])
        elif len(vals) == 1:
            meta[f"row_{i}"] = str(vals[0])
    return meta


def extract(xlsx_path: str, output_dir: str = "output",
            header_row: int | None = None):
    xlsx = Path(xlsx_path)
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    ext = xlsx.suffix.lower()
    # Leer SIN header para poder detectar la fila real
    df = pd.read_excel(xlsx, header=None) if ext != ".csv" else pd.read_csv(xlsx, header=None)

    # Detectar fila de headers
    if header_row is None:
        header_row = _detect_header_row(df)

    # Extraer metadatos de filas superiores
    metadata = _extract_metadata(df, header_row)

    # Configurar headers
    df.columns = df.iloc[header_row].astype(str).str.strip()
    df = df.iloc[header_row + 1:].reset_index(drop=True)

    # Limpiar columnas Unnamed
    df = df.rename(columns=lambda c: "" if isinstance(c, str) and c.startswith("Unnamed") else c)
    # Eliminar columnas completamente vacías
    df = df.dropna(axis=1, how='all')

    records = df.where(pd.notnull(df), None).to_dict(orient="records")
    # Limpiar NaN introducidos por pandas
    import math
    records = [
        {k: None if isinstance(v, float) and math.isnan(v) else v
         for k, v in row.items()}
        for row in records
    ]

    json_path = out / f"{xlsx.stem}.batch.json"
    output = {
        "source": str(xlsx),
        "type": "xlsx",
        "rows": records,
        "count": len(records),
        "header_row": header_row,
        "metadata": metadata,
    }
    json_path.write_text(
        json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(json.dumps(output, indent=2))

    # Manifest para consistencia
    manifest = {
        "source": str(xlsx),
        "type": "xlsx",
        "batch_file": str(json_path),
        "rows": len(records),
    }
    (out / f"{xlsx.stem}.manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )


if __name__ == "__main__":
    header_row = None
    args = sys.argv[1:]
    if "--header-row" in args:
        idx = args.index("--header-row")
        header_row = int(args[idx + 1])
        args = args[:idx] + args[idx + 2:]

    if len(args) < 1:
        print("Uso: uv run python3 scripts/extract_xlsx.py docs/archivo.xlsx [output/] [--header-row N]",
              file=sys.stderr)
        sys.exit(1)

    extract(args[0], args[1] if len(args) > 1 else "output", header_row)
