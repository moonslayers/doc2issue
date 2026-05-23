# doc2issue — Agentes

## Pipeline

```
docs/archivo.pdf
    ↓
[analyzer] → extrae texto + imágenes
    ↓
[vision] → analiza cada imagen
    ↓
[analyzer] → consolida en JSON
    ↓
[creator] → crea GitHub Issue
```

## Agentes

| Agente | Modelo | Rol | Entrada → Salida |
|--------|--------|-----|-----------------|
| analyzer | DeepSeek Chat | Orquesta y extrae texto | `docs/*` → `output/*.txt` + `images/` |
| vision | Qwen 3.5 Flash | Analiza imágenes | `images/*.png` → `images/*.json` |
| creator | DeepSeek Chat | Crea issues | `*.issue.json` → GitHub Issue |

## Skills disponibles

Cada formato tiene su skill en `.opencode/skills/`:
`pdf-analyzer` · `word-parser` · `ppt-analyzer` · `excel-analyzer` · `issue-creator`

## Pipeline Rápido

1. `/agent analyzer` → "Analiza docs/midoc.pdf"
2. El analyzer invoca vision automáticamente
3. `/agent creator` → "Crea issue desde output/midoc.issue.json"

## Dependencias

```bash
# Sistema (solo github-cli)
sudo pacman -S github-cli

# Python (vía uv)
uv tool install pymupdf mammoth python-docx python-pptx pandas openpyxl

# Autenticación
gh auth login
```
