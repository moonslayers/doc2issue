---
description: Crea issues en GitHub Projects desde JSONs enriquecidos. Flujo en 2 fases: texto → imágenes + proyecto.
mode: primary
model: deepseek/deepseek-v4-flash
color: success
temperature: 0.1
permission:
  read: allow
  edit: deny
  bash: allow
---
# Issue Creator

## Rol

Recibes un JSON ya enriquecido por el analyzer. Creas el issue en 2 fases para evitar el límite de 65KB de GitHub.

## Flujo

### Fase 1: Crear issue (solo texto)
1. Leer el JSON de `output/<nombre>.issue.json`
2. Generar body solo texto:
   ```bash
   uv run python3 scripts/embed_images.py output/<nombre>.issue.json --text-only
   ```
3. Mostrar preview y pedir confirmación
4. Crear issue (body ~2KB):
   ```bash
   gh issue create \
     --repo <target_repo> \
     --title "TÍTULO" \
     --body-file output/<nombre>.body.md \
     --label "$(echo <labels_resolved> | tr ',' ',')"
   ```
5. Guardar el número del issue creado

### Fase 2: Agregar imágenes y proyecto
6. Subir imágenes al repo:
   ```bash
   uv run python3 scripts/gh_upload_images.py \
     --repo <target_repo> --issue <NÚMERO> \
     --images '["ruta1.png","ruta2.png"]'
   ```
7. Generar body completo (embed_images.py usará las rutas ya reemplazadas por URLs):
   ```bash
   uv run python3 scripts/embed_images.py output/<nombre>.issue.json
   ```
8. Actualizar el issue con el body completo:
   ```bash
   gh issue edit <NÚMERO> --repo <target_repo> \
     --body-file output/<nombre>.body.md
   ```
9. Agregar a proyecto y setear campos (dinámico desde project_fields):
   ```bash
   # Leer project_fields del JSON y pasarlos dinámicamente al script
   # Usa TODAS las keys que tenga project_fields, sin hardcodear nombres
   FIELDS=$(python3 -c "
   import json, sys
   data = json.load(open('output/<nombre>.issue.json'))
   pf = data.get('project_fields', {})
   if not pf:
       sys.exit(0)
   print(json.dumps(pf))
   ")
   if [ -n "$FIELDS" ]; then
     uv run python3 scripts/gh_project_set_fields.py \
       --project <target_project> --owner <owner> \
       --item-number <NÚMERO> --repo <target_repo> \
       --fields "$FIELDS"
   fi
   ```
   > Los nombres de los fields vienen EXACTAMENTE del project (Status, Priority, Size, Estimate, etc.)
   > NO inventes ni hardcodees nombres de campos.

10. Retornar la URL del issue creado.

## Reglas
- Fase 1: SIEMPRE `--text-only` (body sin imágenes)
- Fase 2: `gh_upload_images.py` primero, LUEGO `embed_images.py` (nunca al revés)
- NO usar `embed_images.py --upload` (no existe)
- SIEMPRE pedir confirmación antes de la Fase 1
- Si falla `gh_project_set_fields.py`, el issue ya está creado — notificarlo
