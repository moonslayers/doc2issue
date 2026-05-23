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

## Pipeline Rápido

1. `/agent analyzer` → "Analiza docs/midoc.pdf"
2. El analyzer invoca vision automáticamente
3. `/agent creator` → "Crea issue desde output/midoc.issue.json"

## Dependencias

```bash
sudo pacman -S github-cli poppler pandoc jq
gh auth login
```
