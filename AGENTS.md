# doc2issue — Agentes

## Pipeline

```
docs/<proyecto>/archivo.pdf
    ↓
[analyzer] → extrae texto + imágenes → output/issues/<proyecto>/data/
    ↓
[vision] → analiza cada imagen → output/issues/<proyecto>/data/images/*.vision.json
    ↓
[analyzer] → consolida en output/issues/<proyecto>/archivo_N.issue.json
    ↓
[creator] → crea GitHub Issue desde output/issues/<proyecto>/archivo_N.issue.json
```

## Agentes

| Agente | Modelo | Rol | Entrada → Salida |
|--------|--------|-----|-----------------|
| analyzer | DeepSeek Chat | Orquesta y extrae texto | `docs/*` → `output/issues/<proyecto>/data/*` + `output/issues/<proyecto>/*.issue.json` |
| vision | Qwen 3.5 Flash | Analiza imágenes | `output/issues/<proyecto>/data/images/*.png` → `*.vision.json` |
| creator | DeepSeek Chat | Crea issues | `output/issues/<proyecto>/*.issue.json` → GitHub Issue |

## Skills disponibles

Cada formato tiene su skill en `.opencode/skills/`:
`pdf-analyzer` · `word-parser` · `ppt-analyzer` · `excel-analyzer` · `issue-creator`

## Pipeline Rápido

1. `/agent analyzer` → "Analiza docs/mi-proyecto/midoc.pdf"
2. El analyzer invoca vision automáticamente
3. `/agent creator` → "Crea issue desde output/issues/mi-proyecto/midoc_1.issue.json"

## Dependencias

```bash
# Sistema (solo github-cli)
sudo pacman -S github-cli

# Python (vía uv)
uv tool install pymupdf mammoth python-docx python-pptx pandas openpyxl

# Autenticación
gh auth login
```
