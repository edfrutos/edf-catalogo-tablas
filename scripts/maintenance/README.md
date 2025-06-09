# Sistema de Mantenimiento de Logs

Este directorio contiene scripts para la gestión y mantenimiento de los archivos de registro (logs) de la aplicación.

## Scripts Disponibles

### 1. `clean_old_logs.py`

Elimina archivos de logs antiguos según los días de retención especificados.

**Uso:**
```bash
python3 clean_old_logs.py [--days N] [--dry-run] [--log-dir RUTA]
```

**Opciones:**
- `--days N`: Número de días de retención (por defecto: 30)
- `--dry-run`: Solo muestra qué archivos se eliminarían sin borrarlos
- `--log-dir`: Directorio donde se encuentran los logs (por defecto: `../../logs`)

**Ejemplo:**
```bash
# Mostrar qué archivos se eliminarían (sin borrar)
python3 clean_old_logs.py --days 30 --dry-run

# Eliminar archivos con más de 60 días
python3 clean_old_logs.py --days 60
```

### 2. `setup_log_rotation.sh`

Configura la rotación automática de logs usando logrotate y una tarea programada para limpieza semanal.

**Uso (requiere permisos de administrador):**
```bash
sudo ./setup_log_rotation.sh
```

**Qué hace este script:**
1. Crea una configuración de logrotate para los logs de la aplicación
2. Programa una tarea cron para limpieza semanal de logs
3. Configura la retención por 30 días por defecto

## Configuración Automatizada

### Rotación Diaria con Logrotate

Se ha configurado logrotate para gestionar la rotación diaria de logs con las siguientes características:
- Retención: 30 días
- Compresión de logs rotados
- Permisos adecuados (0640)

### Limpieza Semanal Programada

Se ha programado una tarea que se ejecuta todos los domingos a las 2:00 AM para:
1. Eliminar archivos de logs con más de 30 días
2. Registrar la operación en `logs/cleanup_job.log`

## Verificación

Para verificar la configuración:

1. Verificar la tarea programada:
   ```bash
   crontab -l
   ```

2. Verificar la configuración de logrotate:
   ```bash
   sudo logrotate -d /etc/logrotate.d/edf_catalogotablas
   ```

3. Verificar los logs de limpieza:
   ```bash
   tail -f logs/cleanup_job.log
   ```

## Solución de Problemas

### Los logs no se están rotando
1. Verificar que el servicio cron esté en ejecución:
   ```bash
   systemctl status cron
   ```

2. Verificar los logs del sistema para errores de logrotate:
   ```bash
   grep logrotate /var/log/syslog
   ```

### Permisos insuficientes
Asegúrate de que el usuario que ejecuta el script tenga permisos de escritura en el directorio de logs.

## Personalización

### Cambiar la frecuencia de limpieza
Edita el archivo de configuración de cron:
```bash
crontab -e
```

### Cambiar la retención de logs
Modifica el parámetro `--days` en el script de configuración o en la tarea cron.

## Notas de Seguridad

- Los archivos de log contienen información sensible. Asegúrate de que los permisos estén configurados correctamente.
- Revisa periódicamente los logs de limpieza para detectar posibles problemas.
- Considera implementar una estrategia de backup para logs importantes antes de su eliminación.
