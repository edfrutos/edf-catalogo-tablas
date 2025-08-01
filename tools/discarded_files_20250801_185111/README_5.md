# Scripts de Mantenimiento

Este directorio contiene scripts útiles para el mantenimiento y limpieza del proyecto.

## Scripts Disponibles

### `cleanup.sh`

Limpia archivos temporales y compilados del proyecto.

**Uso:**

```bash
./cleanup.sh
```

### `organize_files.sh`

Organiza archivos duplicados y temporales en carpetas de respaldo.

**Uso:**

```bash
./organize_files.sh
```

### `cleanup_dependencies.sh`

Limpia las dependencias del proyecto y genera un archivo `requirements.txt` actualizado.

**Uso:**

```bash
./cleanup_dependencies.sh
```

## Estructura de Carpetas

- `backup_tmp/`: Carpeta temporal para almacenar archivos antes de su eliminación definitiva.
  - `duplicate_scripts/`: Copias de scripts duplicados.
  - `temp_files/`: Archivos temporales.
  - `logs/`: Archivos de registro antiguos.

## Buenas Prácticas

1. **Siempre haz una copia de seguridad** antes de ejecutar los scripts de limpieza.
2. **Revisa los cambios** con `git status` antes de hacer commit.
3. **Ejecuta los scripts en orden** para una limpieza efectiva.
4. **Verifica las dependencias** después de limpiar el entorno virtual.

## Notas Importantes

- Los scripts están diseñados para ser seguros y no eliminarán archivos sin confirmación.
- Se recomienda revisar los scripts antes de ejecutarlos en producción.
- Los archivos movidos a `backup_tmp/` pueden ser eliminados manualmente después de verificar que no son necesarios.
