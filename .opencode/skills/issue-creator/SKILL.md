---
name: issue-creator
description: "Use when creating GitHub issues from structured JSON files. Flujo en 2 fases: texto → imágenes + proyecto. Sin --upload."
---
# Issue Creator

## Objetivo
Crear issues en GitHub Projects desde JSONs enriquecidos. Flujo en 2 fases para evitar límite 65KB.

## Pre-requisitos
- `gh` autenticado: `gh auth login && gh auth refresh -h github.com -s project`

## Fase 1: Crear issue (solo texto)
```bash
uv run python3 scripts/embed_images.py output/archivo.issue.json --text-only
gh issue create --repo <target_repo> --title "..." --body-file output/archivo.body.md --label "lab1,lab2"
```

## Fase 2: Imágenes + proyecto
```bash
uv run python3 scripts/gh_upload_images.py --repo <target_repo> --issue <N> --images '["img1.png"]'
uv run python3 scripts/embed_images.py output/archivo.issue.json
gh issue edit <N> --repo <target_repo> --body-file output/archivo.body.md
# Los fields se toman DINÁMICAMENTE del project_fields en el JSON.
# El analyzer deja project_fields con los nombres EXACTOS del project.
# NO hardcodees nombres de campos aquí.
FIELDS=$(python3 -c "import json; print(json.dumps(json.load(open('archivo.issue.json')).get('project_fields', {})))")
uv run python3 scripts/gh_project_set_fields.py --project <N> --owner <owner> --item-number <N> --repo <target_repo> --fields "$FIELDS"
```

## Scripts disponibles
| Script | Qué hace |
|--------|----------|
| `embed_images.py` | Genera body (`--text-only` o con imágenes desde el JSON) |
| `gh_upload_images.py` | Sube imágenes al repo vía Content API. Flags: `--branch` (default: detectar), `--update-json` (parchea .issue.json automáticamente) |
| `gh_project_set_fields.py` | Agrega issue a proyecto y setea campos (idempotente) |

## Formato de URLs de imágenes
```
https://github.com/{owner}/{repo}/blob/main/.issue-assets/{number}/{file}?raw=true
```
Los espacios se URL-encodean automáticamente. Si la imagen no se ve, esperar CDN.

## Verificación post-creación
1. ✅ Abrir URL del issue y verificar imágenes
2. ✅ Verificar labels asignados
3. ✅ Verificar campos del project (los que vienen en project_fields del JSON)

## Troubleshooting

| Síntoma | Causa | Solución |
|---------|-------|----------|
| `gh_upload_images.py` falla con error SHA | Múltiples uploads paralelos al mismo branch | El script ya sube secuencialmente. Si persiste, esperar 1s entre intentos |
| `gh_project_set_fields.py` retorna item_id vacío | Proyecto con >100 items, paginación incompleta | Verificar que el script use paginación (debe iterar hasta encontrar el issue) |
| `gh issue create` falla: "could not add label" | Label no existe en el repo | Verificar `labels_resolved` en el JSON — el analyzer debió listar labels existentes |
| URLs de imágenes no se ven en el issue | CDN de GitHub tarda en propagarse | Esperar 2-3 minutos y recargar la página del issue |
| `gh` command fails: "unknown flag" | Versión de `gh` desactualizada o flags cambiaron | Ejecutar `gh <comando> --help` para ver flags actuales |
| Body del issue truncado o >65KB | Se incluyeron imágenes sin usar `--text-only` primero | Recrear el issue: Fase 1 con `--text-only`, Fase 2 con URLs |

## Validación
- SIEMPRE preview antes de Fase 1
- NO usar `--upload` en embed_images.py (no existe)
- gh_upload_images.py SIEMPRE antes que embed_images.py en Fase 2
