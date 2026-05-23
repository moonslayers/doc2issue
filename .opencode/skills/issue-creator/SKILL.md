---
name: issue-creator
description: "Use when creating GitHub issues from structured JSON files. Covers `gh issue create`, embedding images as base64 data URIs via script, setting project fields via GraphQL."
---
# Issue Creator

## Objetivo
Crear issues en GitHub Projects desde JSONs estructurados generados por el agente `analyzer`, incluyendo imágenes embebidas directamente en el body del issue.

## Pre-requisitos
- `gh` autenticado: `gh auth login`
- Dependencias: solo `uv sync` (no requiere librerías adicionales)

## Pasos

1. **Leer el JSON de `output/`**:
   ```bash
   cat output/<nombre>.issue.json
   ```
   Identificar: `title`, `description`, `images[]`, etc.

2. **Generar body markdown** usando el script `scripts/embed_images.py`:
   ```bash
   uv run python3 scripts/embed_images.py output/<nombre>.issue.json
   ```
   El script:
   - Lee el JSON y la plantilla `templates/issue-body.md`
   - Convierte cada imagen a data URI base64 (`data:image/png;base64,...`)
   - Renderiza el template reemplazando las variables Mustache
   - Guarda el resultado en `output/<nombre>.body.md`

3. **Mostrar preview y pedir confirmación**:
   ```
   📋 Resumen del issue:
   Título: Login con Google OAuth
   Labels: auth, oauth
   Prioridad: high | Tamaño: M | Estimación: 8h
   Imágenes: 2 (embebidas como data URIs)
   Tamaño del body: ~150KB

   ¿Crear issue? [y/N]
   ```

4. **Crear issue** (con imágenes ya embebidas en el body):
   ```bash
   gh issue create \
     --title "TÍTULO" \
     --body-file output/<nombre>.body.md \
     --label "label1,label2"
   ```

5. **Agregar a proyecto y setear campos custom vía GraphQL**:
   ```bash
   gh api graphql -f query='
     mutation($project:ID!, $item:ID!, $field:ID!, $value:String!) {
       updateProjectV2ItemFieldValue(
         projectId: $project
         itemId: $item
         fieldId: $field
         value: { text: $value }
       ) { clientMutationId }
     }'
   ```

6. **Retornar la URL del issue creado**.

## Edge cases
| Caso | Qué hacer |
|------|-----------|
| **Imagen > 1MB** | Advertir al usuario que el body será pesado |
| **Imagen no existe en disco** | El script la omite (path vacío) |
| **Sin imágenes** | El script genera el body sin sección de imágenes |
| **Imagen corrupta** | El script la omite silenciosamente |

## Validación
- SIEMPRE mostrar preview antes de crear
- Pedir confirmación explícita: "¿Crear issue? [y/N]"
- Verificar que `output/<nombre>.body.md` se generó correctamente

## Manejo de errores
- Si falla `scripts/embed_images.py`: mostrar el error y abortar
- Si falla GraphQL: loguear el error y dejar el issue creado sin campos custom
- Si falla `gh issue create`: mostrar el error al usuario y abortar
