---
name: issue-creator
description: "Use when creating GitHub issues from structured JSON files. Uses 2-phase flow (text → images) to avoid 65KB body limit. Uploads images to repo and sets project fields."
---
# Issue Creator

## Objetivo
Crear issues en GitHub Projects desde JSONs enriquecidos, usando flujo en 2 fases para evitar el límite de 65KB.

## Pre-requisitos
- `gh` autenticado: `gh auth login && gh auth refresh -h github.com -s project`

## Fase 1: Crear issue (solo texto)
```bash
uv run python3 scripts/embed_images.py output/archivo.issue.json --text-only
gh issue create --repo <target_repo> --title "..." --body-file output/archivo.body.md --label "lab1,lab2"
```

## Fase 2: Agregar imágenes
```bash
uv run python3 scripts/gh_upload_images.py --repo <target_repo> --issue <N> --images '["img1.png"]'
uv run python3 scripts/embed_images.py output/archivo.issue.json
gh issue edit <N> --repo <target_repo> --body-file output/archivo.body.md
```

## Fase 3: Setear proyecto
```bash
uv run python3 scripts/gh_project_set_fields.py --project <N> --owner <owner> --item-number <N> --repo <target_repo> --fields '{"Status":"Todo"}'
```

## Scripts disponibles
| Script | Qué hace |
|--------|----------|
| `embed_images.py` | Genera body (--text-only o con imágenes) |
| `gh_upload_images.py` | Sube imágenes al repo vía Content API |
| `gh_project_set_fields.py` | Agrega issue a proyecto y setea campos |

## Validación
- SIEMPRE preview antes de crear
- Verificar que `target_repo` y `target_project` existen en el JSON
