"""Tests para scripts/extract_xlsx.py (con detección de headers)."""
import sys, json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from extract_xlsx import extract, _detect_header_row, _extract_metadata


def test_detect_header_row_normal(tmp_path):
    """Data sin metadatos: headers deben estar en fila 0."""
    import pandas as pd
    df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
    path = tmp_path / "test.xlsx"
    df.to_excel(str(path), index=False)
    df_raw = pd.read_excel(path, header=None)
    assert _detect_header_row(df_raw) == 0


def test_detect_header_row_with_metadata(tmp_path):
    """Data con metadatos arriba: headers deben detectarse después."""
    import pandas as pd
    # Simular filas de metadata + headers
    rows = [
        ["Reporte:", "Mensual", "", "", ""],
        ["Fecha:", "2025-01", "", "", ""],
        ["", "", "", "", ""],
        ["Nombre", "Edad", "Ciudad", "Depto", "Cargo"],
        ["Ana", 30, "MX", "IT", "Dev"],
        ["Bob", 25, "CO", "RH", "Analyst"],
    ]
    df = pd.DataFrame(rows)
    path = tmp_path / "metadata.xlsx"
    df.to_excel(str(path), index=False, header=False)
    df_raw = pd.read_excel(path, header=None)
    assert _detect_header_row(df_raw) == 3


def test_extract_with_metadata(tmp_path):
    """Integración: extraer XLSX con metadatos debe ignorarlos y poner headers bien."""
    import pandas as pd
    rows = [
        ["Fideicomiso:", "Fondo BC-1", "", "", ""],
        ["Fecha:", "2025-05-23", "", "", ""],
        ["", "", "", "", ""],
        ["Title", "Description", "Priority", "Status", "Owner"],
        ["Feature A", "Desc A", "High", "Todo", "Ana"],
        ["Feature B", "Desc B", "Medium", "Done", "Bob"],
    ]
    df = pd.DataFrame(rows)
    path = tmp_path / "test_meta.xlsx"
    df.to_excel(str(path), index=False, header=False)
    extract(str(path), str(tmp_path))
    with open(tmp_path / "test_meta.batch.json") as f:
        data = json.load(f)
    assert data["count"] == 2
    assert data["rows"][0]["Title"] == "Feature A"
    assert data["metadata"]["Fideicomiso:"] == "Fondo BC-1"
    assert data["header_row"] == 3


def test_extract_header_row_explicit(tmp_path):
    """Flag --header-row debe funcionar."""
    import pandas as pd
    df = pd.DataFrame({"X": [1], "Y": [2]})
    path = tmp_path / "explicit.xlsx"
    df.to_excel(str(path), index=False)
    extract(str(path), str(tmp_path), header_row=1)
    with open(tmp_path / "explicit.batch.json") as f:
        data = json.load(f)
    assert data["header_row"] == 1


def test_detect_header_row_fallback(tmp_path):
    """Data sin suficientes columnas debe fallback a fila 0."""
    import pandas as pd
    df = pd.DataFrame({"a": [1]})  # 1 columna
    path = tmp_path / "single.xlsx"
    df.to_excel(str(path), index=False)
    df_raw = pd.read_excel(path, header=None)
    assert _detect_header_row(df_raw, min_cols=5) == 0


def test_extract_no_metadata(tmp_path):
    """XLSX sin metadatos ni header_row debe ser compatible con el comportamiento anterior."""
    import pandas as pd
    df = pd.DataFrame({"Title": ["A"], "Priority": ["High"]})
    path = tmp_path / "simple.xlsx"
    df.to_excel(str(path), index=False)
    extract(str(path), str(tmp_path))
    with open(tmp_path / "simple.batch.json") as f:
        data = json.load(f)
    assert data["count"] == 1
    assert data["rows"][0]["Title"] == "A"
