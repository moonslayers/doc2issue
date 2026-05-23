# doc2issue

> Automatiza la conversión de documentos de requerimientos en issues de GitHub Projects.

## 🎯 ¿Qué es doc2issue?

doc2issue es una herramienta que toma documentos de requerimientos (PDF, Word, PPT, Excel) y los convierte en issues estructurados de GitHub Projects. Usa una pipeline de 3 agentes OpenCode con modelos de OpenRouter para extraer texto, analizar imágenes/mockups, y crear issues directamente desde tu terminal.

Está diseñada para equipos que reciben requerimientos en formatos de documento y necesitan volcarlos a GitHub de forma rápida y consistente, sin copiar y pegar manualmente.

## 🚀 Quick Start

1. Coloca tu documento en `docs/`:
   ```bash
   cp ~/documento.pdf docs/
   ```
2. En OpenCode: `/agent analyzer` → `Analiza docs/documento.pdf`
3. En OpenCode: `/agent creator` → `Crea issue desde output/documento.issue.json`
4. ¡Issue creado en GitHub!

## 🔄 Flujo de Conversión

```
docs/requerimiento.pdf
    ↓ [analyzer] DeepSeek extrae texto + imágenes
output/requerimiento.txt + output/images/*.png
    ↓ [vision] Qwen 3.5 Flash analiza imágenes
output/images/*.json
    ↓ [analyzer] consolida todo
output/requerimiento.issue.json
    ↓ [creator] previa confirmación
GitHub Issue con imágenes adjuntas
```

## ⚙️ Setup & Configuración

### Dependencias (CachyOS)

```bash
sudo pacman -S github-cli poppler pandoc jq
```

### Autenticación

```bash
gh auth login
```

### API Key OpenRouter

Agrega tu API key en `~/.config/opencode/config.json` o como variable de entorno `OPENROUTER_API_KEY`.

## 🤖 Agentes

| Agente | Modelo | Rol |
|--------|--------|-----|
| analyzer | DeepSeek Chat | Analiza texto y orquesta el flujo |
| vision | Qwen 3.5 Flash | Analiza imágenes y mockups |
| creator | DeepSeek Chat | Crea issues en GitHub |

## 📁 Estructura del Proyecto

```
doc2issue/
├── .opencode/
│   ├── agents/          → Configuración de agentes
│   └── commands/        → Comandos rápidos
├── skills/              → Skills por tipo de documento
├── templates/           → Plantillas de issues
├── docs/                → Documentos de entrada (gitignored)
├── output/              → JSONs generados (gitignored)
├── plans/               → Planes de implementación
├── .gitignore
├── AGENTS.md
└── README.md
```

## 📝 Ejemplos de Uso

### Analizar un PDF

```bash
cp ~/Downloads/requerimiento.pdf docs/
# En OpenCode: /agent analyzer > "Analiza docs/requerimiento.pdf"
```

### Analizar un Excel (backlog)

```bash
cp ~/Downloads/backlog.xlsx docs/
# Genera un issue por cada fila
```

## 📄 Licencia

Ver archivo `LICENSE`.

> **🚧 Nota**: Este proyecto está en fase de construcción. Los agentes se configuran en etapas posteriores. Para ver el diseño completo, revisa [`plans/`](plans/).
