#!/usr/bin/env python3
"""Utilidades compartidas para los scripts de doc2issue."""
import os
from pathlib import Path


def load_env():
    """Carga variables desde .env en el project root.

    Busca un archivo .env en el directorio raíz del proyecto.
    Las variables se cargan en os.environ sin sobrescribir
    variables ya existentes (las env del sistema tienen prioridad).

    Formato soportado:
        KEY=VALUE
        # comentarios
        líneas vacías se ignoran
    """
    env_path = Path(__file__).resolve().parent.parent / '.env'
    if not env_path.exists():
        return

    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        key, _, value = line.partition('=')
        os.environ.setdefault(key.strip(), value.strip())
