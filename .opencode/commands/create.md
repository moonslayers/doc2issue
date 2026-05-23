---
description: Crea un issue en GitHub desde un JSON estructurado generado por el agente analyzer.
argument-hint: <ruta-al-json-en-output>
---
# Comando: /create

Usa el agente `creator` para crear un issue desde el JSON indicado.

1. Lee el JSON de $ARGUMENTS
2. Muestra preview del issue (título, descripción, labels, priority, size)
3. Pide confirmación al usuario
4. Crea el issue con `gh issue create`
5. Adjunta imágenes si las hay
6. Agrega al proyecto y setea campos custom vía GraphQL
7. Muestra la URL del issue creado

Archivo JSON: $ARGUMENTS
