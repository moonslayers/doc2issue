#!/usr/bin/env python3
"""Convierte Excel/CSV a JSON batch. Una fila = un issue potencial."""
import sys, json
from pathlib import Path
import pandas as pd

def extract(xlsx_path: str, output_dir: str = "output"):
    xlsx = Path(xlsx_path)
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    ext = xlsx.suffix.lower()
    df = pd.read_csv(xlsx) if ext == ".csv" else pd.read_excel(xlsx)

    import math, datetime
    def safe_val(v):
        if isinstance(v, float) and math.isnan(v):
            return None
        if isinstance(v, datetime.datetime) or isinstance(v, datetime.date):
            return v.isoformat()
        if isinstance(v, datetime.time):
            return v.strftime("%H:%M:%S")
        return v

    records = df.where(pd.notnull(df), None).to_dict(orient="records")
    records = [
        {k: safe_val(v) for k, v in row.items()}
        for row in records
    ]

    json_path = out / f"{xlsx.stem}.batch.json"
    json_path.write_text(
        json.dumps({"source": str(xlsx), "type": "xlsx", "rows": records, "count": len(records)},
                   indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"✅ {len(records)} filas extraídas → {json_path}")

    # También generar manifest para consistencia
    manifest = {
        "source": str(xlsx),
        "type": "xlsx",
        "batch_file": str(json_path),
        "rows": len(records)
    }
    (out / f"{xlsx.stem}.manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python3 scripts/extract_xlsx.py docs/archivo.xlsx [output/]", file=sys.stderr)
        sys.exit(1)
    extract(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "output")
