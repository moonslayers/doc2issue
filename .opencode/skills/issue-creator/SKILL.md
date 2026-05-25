---
name: issue-creator
description: "Use when creating GitHub issues from structured JSON files. Covers `gh issue create`, embedding images as data URIs, listing repos/projects, project metrics. Uses Python scripts in `scripts/` (tested with 49 tests)."
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

## Scripts disponibles (usar SIEMPRE estos)

Todos los scripts están en , validados con **49 tests unitarios**.
Úsalos en vez de escribir comandos Work seamlessly with GitHub from the command line.

USAGE
  gh <command> <subcommand> [flags]

CORE COMMANDS
  auth:          Authenticate gh and git with GitHub
  browse:        Open repositories, issues, pull requests, and more in the browser
  codespace:     Connect to and manage codespaces
  gist:          Manage gists
  issue:         Manage issues
  org:           Manage organizations
  pr:            Manage pull requests
  project:       Work with GitHub Projects.
  release:       Manage releases
  repo:          Manage repositories
  skill:         Install and manage agent skills (preview)

GITHUB ACTIONS COMMANDS
  cache:         Manage GitHub Actions caches
  run:           View details about workflow runs
  workflow:      View details about GitHub Actions workflows

ALIAS COMMANDS
  co:            Alias for "pr checkout"

ADDITIONAL COMMANDS
  agent-task:    Work with agent tasks (preview)
  alias:         Create command shortcuts
  api:           Make an authenticated GitHub API request
  attestation:   Work with artifact attestations
  completion:    Generate shell completion scripts
  config:        Manage configuration for gh
  copilot:       Run the GitHub Copilot CLI (preview)
  extension:     Manage gh extensions
  gpg-key:       Manage GPG keys
  label:         Manage labels
  licenses:      View third-party license information
  preview:       Execute previews for gh features
  ruleset:       View info about repo rulesets
  search:        Search for repositories, issues, and pull requests
  secret:        Manage GitHub secrets
  ssh-key:       Manage SSH keys
  status:        Print information about relevant issues, pull requests, and notifications across repositories
  variable:      Manage GitHub Actions variables

HELP TOPICS
  accessibility: Learn about GitHub CLI's accessibility experiences
  actions:       Learn about working with GitHub Actions
  environment:   Environment variables that can be used with gh
  exit-codes:    Exit codes used by gh
  formatting:    Formatting options for JSON data exported from gh
  mintty:        Information about using gh with MinTTY
  reference:     A comprehensive reference of all gh commands
  telemetry:     Information about telemetry in gh

FLAGS
  --help      Show help for command
  --version   Show gh version

EXAMPLES
  $ gh issue create
  $ gh repo clone cli/cli
  $ gh pr checkout 321

LEARN MORE
  Use `gh <command> <subcommand> --help` for more information about a command.
  Read the manual at https://cli.github.com/manual
  Learn about exit codes using `gh help exit-codes`
  Learn about accessibility experiences using `gh help accessibility` manuales — garantizan consistencia,
manejo de errores y cargan configuración desde .

| Script | Qué hace | En vez de |
|--------|----------|-----------|
| `gh_list_repos.py` | Lista repositorios del owner | `gh repo list` manual |
| `gh_list_projects.py` | Lista proyectos del owner/repo | `gh project list` manual |
| `gh_project_metrics.py` | Métricas de un project (status, priority, size, recent) | `gh project view` + GraphQL manual |
| `gh_project_repos.py` | Repositorios vinculados a un project (con paginación) | GraphQL manual sin paginación |
| `embed_images.py` | Convierte imágenes a data URIs en el body del issue | `base64` manual + template |

Uso general:
```bash
uv run python3 scripts/<script>.py [argumentos] [--owner @me]
```

- Todos cargan  automáticamente (GITHUB_OWNER, GITHUB_REPO)
- Todos retornan JSON estructurado
- `--owner` es opcional (default:  → `gh api user`)

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
