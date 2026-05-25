---
name: issue-creator
description: "Use when creating GitHub issues from structured JSON files. The analyzer already enriched the JSON with resolved labels, metrics, and repo/project info. This skill just creates the issue and adds it to the project."
---
# Issue Creator

## Objetivo
Crear issues en GitHub Projects desde JSONs **ya enriquecidos** por el analyzer.

## Pre-requisitos
- `gh auth login`
- `gh auth refresh -h github.com -s project`

## Pasos

1. **Leer JSON**: `cat output/<nombre>.issue.json`
2. **Generar body**: `uv run python3 scripts/embed_images.py output/<nombre>.issue.json` → `output/<nombre>.body.md`
3. **Preview y confirmación**
4. **Crear issue**:
   ```bash
   gh issue create --repo <target_repo> --title "TÍTULO" --body-file output/<nombre>.body.md --label "<labels>"
   ```
5. **Agregar a proyecto**:
   ```bash
   uv run python3 scripts/gh_project_set_fields.py --project <project> --owner <owner> --item-url "<URL>" --fields '{"Status":"<status>","Priority":"<priority>","Size":"<size>"}'
   ```
6. **Retornar la URL**

## Scripts
- `embed_images.py` → body markdown con imágenes
- `gh_project_set_fields.py` → agrega issue a proyecto y setea campos
