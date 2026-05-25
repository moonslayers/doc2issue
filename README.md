# doc2issue

> Automatiza la conversión de documentos de requerimientos en issues de GitHub Projects.

## 🎯 ¿Qué es?

doc2issue toma documentos de requerimientos (PDF, Word, PPT, Excel) y los convierte en issues estructurados de GitHub Projects. Usa 3 agentes OpenCode con modelos de OpenRouter para extraer texto, analizar imágenes/mockups, y crear issues directamente desde tu terminal.

Diseñada para equipos que reciben requerimientos en documentos y necesitan volcarlos a GitHub de forma rápida y consistente.

## 🚀 Quick Start

```bash
# 1. Coloca tu documento en docs/
cp ~/documento.pdf docs/

# 2. En OpenCode, invoca al analyzer
/agent analyzer
> Analiza docs/documento.pdf

# 3. Revisa el JSON generado en output/
# 4. Crea el issue
/agent creator
> Crea issue desde output/documento.issue.json
```

## 🔄 Pipeline

```
docs/archivo.pdf → [analyzer] → output/*.issue.json → [creator] → GitHub Issue
```

Cada formato tiene una skill dedicada en `.opencode/skills/` que contiene las reglas de extracción, análisis y generación del JSON.

## ⚙️ Setup

```bash
# Sistema (solo github-cli)
sudo pacman -S github-cli

# Python (vía uv)
uv tool install pymupdf mammoth python-docx python-pptx pandas openpyxl

# Autenticación
gh auth login
```

### Dependencias opcionales (para PPTX)

Si procesas presentaciones PPTX, instala LibreOffice para renderizar slides completos como imágenes (con texto, diagramas y flechas):

```bash
sudo pacman -S libreoffice-fresh
```

Sin LibreOffice, el script `extract_pptx.py` usa un fallback que extrae imágenes incrustadas sin el contexto del slide completo.

## 🤖 Agentes

| Agente | Modelo | Rol |
|--------|--------|-----|
| analyzer | DeepSeek Chat | Orquesta extracción y genera JSON |
| vision | Qwen 3.5 Flash | Analiza imágenes y mockups |
| creator | DeepSeek Chat | Crea issues en GitHub |

Para más detalles, ver [`AGENTS.md`](AGENTS.md) y las skills en `.opencode/skills/`.

## 📁 Estructura

```
doc2issue/
├── .opencode/    → Agentes, comandos y skills
├── scripts/      → Scripts Python de extracción
├── templates/    → Plantillas de issues
├── docs/         → Documentos de entrada
├── output/       → JSONs generados
├── tests/        → Suite de pruebas
└── plans/        → Planes de implementación
```

## 📄 Licencia

Ver [`LICENSE`](LICENSE).
