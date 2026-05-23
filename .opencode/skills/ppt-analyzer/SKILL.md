---
name: ppt-analyzer
description: "Use for `.pptx` files: extract slides and presenter notes, export slides as images for analysis."
---
# PPT Analyzer

## Cuándo usar
Archivos `.pptx` en `docs/`. Típicamente presentaciones de proyectos o features.

## Proceso

1. Extraer slide por slide usando python-pptx:
   ```python
   from pptx import Presentation
   prs = Presentation('docs/archivo.pptx')
   for i, slide in enumerate(prs.slides):
       for shape in slide.shapes:
           if hasattr(shape, 'text'):
               print(f'Slide {i+1}: {shape.text}')
   ```

2. Guardar cada slide como imagen en `output/images/slide_<n>.png`

3. Extraer notas del presentador (suelen tener detalles adicionales)

4. Delegar imágenes al agente `vision`

## Output
JSON en `output/<nombre>.issue.json`
