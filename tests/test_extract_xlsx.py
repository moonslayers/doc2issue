"""Tests para scripts/extract_xlsx.py."""
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from extract_xlsx import extract


def test_extract_xlsx_creates_batch_json(test_xlsx, tmp_path):
    """Debe crear un archivo batch.json con los datos."""
    extract(str(test_xlsx), str(tmp_path))
    batch_path = tmp_path / f"{test_xlsx.stem}.batch.json"
    assert batch_path.exists(), "batch.json no fue creado"

    data = json.loads(batch_path.read_text())
    assert data["source"] == str(test_xlsx)
    assert data["type"] == "xlsx"
    assert data["count"] > 0
    assert len(data["rows"]) == data["count"]


def test_extract_xlsx_row_count(test_xlsx, tmp_path):
    """Debe extraer todas las filas del Excel."""
    extract(str(test_xlsx), str(tmp_path))
    batch_path = tmp_path / f"{test_xlsx.stem}.batch.json"
    data = json.loads(batch_path.read_text())
    assert data["count"] == 3, "El Excel de prueba tiene 3 filas de datos"


def test_extract_xlsx_column_mapping(test_xlsx, tmp_path):
    """Las columnas conocidas deben estar presentes en los registros."""
    extract(str(test_xlsx), str(tmp_path))
    batch_path = tmp_path / f"{test_xlsx.stem}.batch.json"
    data = json.loads(batch_path.read_text())

    first_row = data["rows"][0]
    assert "Title" in first_row, "Columna Title debe estar presente"
    assert "Description" in first_row, "Columna Description debe estar presente"
    assert "Priority" in first_row, "Columna Priority debe estar presente"


def test_extract_xlsx_creates_manifest(test_xlsx, tmp_path):
    """Debe crear también un manifest.json para consistencia."""
    extract(str(test_xlsx), str(tmp_path))
    manifest_path = tmp_path / f"{test_xlsx.stem}.manifest.json"
    assert manifest_path.exists(), "manifest.json no fue creado"

    manifest = json.loads(manifest_path.read_text())
    assert manifest["type"] == "xlsx"
    assert manifest["rows"] == 3


def test_extract_xlsx_handles_null_values(test_xlsx, tmp_path):
    """Los valores nulos deben convertirse a None/null."""
    import pandas as pd

    # Crear un Excel con valores nulos
    df = pd.DataFrame({
        "Title": ["Feature A", None],
        "Description": ["Desc A", "Desc B"],
    })
    null_xlsx = tmp_path / "null_test.xlsx"
    df.to_excel(str(null_xlsx), index=False)

    extract(str(null_xlsx), str(tmp_path))
    batch_path = tmp_path / "null_test.batch.json"
    data = json.loads(batch_path.read_text())
    import math; assert data["rows"][1]["Title"] is None or (isinstance(data["rows"][1]["Title"], float) and math.isnan(data["rows"][1]["Title"])), "Valor nulo debe ser None o NaN"
