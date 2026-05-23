---
name: issue-creator
description: "Use when creating GitHub issues from structured JSON files. Covers `gh issue create`, attaching images via API, setting project fields via GraphQL."
---
# Issue Creator

## Objetivo
Crear issues en GitHub Projects desde JSONs estructurados generados por el agente `analyzer`.

## Pre-requisitos
- `gh` autenticado: `gh auth login`

## Pasos

1. **Leer el JSON de `output/`**:
   ```bash
   cat output/<nombre>.issue.json
   ```

2. **Generar body markdown** usando la plantilla `templates/issue-body.md`:
   Reemplazar las variables Mustache (`{{title}}`, `{{description}}`, etc.) con los valores del JSON.

3. **Mostrar preview y pedir confirmación**:
   ```
   ¿Crear issue?
   Título: Login con Google OAuth
   Labels: auth, oauth
   Prioridad: high | Tamaño: M | Estimación: 8h
   ¿Confirmar? [y/N]
   ```

4. **Crear issue**:
   ```bash
   gh issue create \
     --title "TÍTULO" \
     --body-file output/<nombre>.body.md \
     --label "label1,label2"
   ```

5. **Adjuntar imágenes** (si las hay):
   ```bash
   gh api repos/{owner}/{repo}/issues/{number}/comments \
     -f body="![{{caption}}]({{url}})"
   ```

6. **Agregar a proyecto y setear campos custom vía GraphQL**:
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

## Validación
- SIEMPRE mostrar preview antes de crear
- Pedir confirmación explícita: "¿Crear issue? [y/N]"

## Manejo de errores
- Si falla GraphQL: loguear el error y dejar el issue creado sin campos custom
- Si falla `gh issue create`: mostrar el error al usuario y abortar
