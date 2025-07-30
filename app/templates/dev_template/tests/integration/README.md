# Pruebas de Integración

Este directorio contiene los tests de integración principales del sistema EDF CatalogoTablas.

## Buenas prácticas
- Mantén aquí solo tests funcionales y relevantes para regresión y depuración.
- Si un test queda obsoleto o es de referencia histórica, muévelo a `../legacy/`.
- Usa fixtures y mocks para evitar dependencias externas reales en integración.
- Ejecuta las pruebas con:
  ```bash
  pytest tests/integration/
  ```

## Estructura recomendada
- Un archivo por área funcional o endpoint crítico.
- Usa nombres descriptivos y evita sufijos de fecha en archivos activos.

---

Para dudas o mejoras, consulta la documentación del proyecto o contacta con el responsable de QA.
