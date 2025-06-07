# Catálogo de Tablas

## Scripts de Mantenimiento

El proyecto incluye varios scripts para facilitar el mantenimiento y la limpieza del código. Estos scripts se encuentran en el directorio `scripts/`.

### Scripts Disponibles

- **`cleanup.sh`**: Limpia archivos temporales y compilados del proyecto.
- **`organize_files.sh`**: Organiza archivos duplicados y temporales en carpetas de respaldo.
- **`cleanup_dependencies.sh`**: Limpia las dependencias y genera un archivo `requirements.txt` actualizado.

Para más detalles, consulta la documentación completa en [scripts/README.md](scripts/README.md).

## Advertencia sobre limpieza de scripts en /tools

Antes de eliminar o mover scripts de `/tools` y sus subdirectorios, **ejecuta siempre**:

```bash
./tools/check_tools_imports.sh
```

Esto te mostrará qué scripts son requeridos por la aplicación y no deben eliminarse. Si usas el script de limpieza `backup_and_clean_tools.sh` o haces un commit, este chequeo se realiza automáticamente.

Así evitarás romper dependencias internas y errores en la aplicación.

## Estándar de cabeceras en scripts Python

Para mantener la calidad y la trazabilidad en el proyecto, todos los scripts Python deben llevar una cabecera estándar con información básica (nombre, descripción, uso, autor, etc.).

- Consulta la guía rápida en español: [tools/README_cabeceras.md](tools/README_cabeceras.md)
- Quick guide in English: [tools/README_headers_EN.md](tools/README_headers_EN.md)

El proceso está automatizado mediante un script y un hook de pre-commit. ¡No olvides revisar la documentación y seguir el flujo recomendado!

