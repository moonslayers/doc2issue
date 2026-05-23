---
description: Analiza un documento completo (texto + imágenes) y genera un JSON estructurado para crear un issue de GitHub.
argument-hint: <ruta-al-archivo-en-docs>
---
# Comando: /analyze

Usa el agente `analyzer` para procesar el archivo indicado.

1. Si es PDF, extrae texto con `pdftotext` e imágenes con `pdfimages`
2. Por cada imagen en `output/images/`, cambia al agente `vision` para analizarla
3. Vuelve al agente `analyzer` para consolidar todo en `output/<nombre>.issue.json`
4. Muestra un resumen al usuario con:
   - Título propuesto
   - Número de imágenes analizadas
   - Priority y size sugeridos
   - Preguntas para el PM (si las hay)

Archivo a procesar: $ARGUMENTS
