#!/bin/bash
# Script para configurar la rotación automática de logs
# Uso: sudo ./setup_log_rotation.sh

# Verificar si se está ejecutando como root
if [ "$(id -u)" -ne 0 ]; then
    echo "Este script debe ejecutarse como root"
    exit 1
fi

# Directorio del proyecto
PROJECT_DIR="/Users/edefrutos/_Repositorios/01.IDE_Cursor/edf_catalogotablas"
LOG_CLEANER="$PROJECT_DIR/scripts/maintenance/clean_old_logs.py"
LOG_FILE="$PROJECT_DIR/logs/cleanup_job.log"

# Verificar que existe el script
if [ ! -f "$LOG_CLEANER" ]; then
    echo "Error: No se encontró el script de limpieza de logs en $LOG_CLEANER"
    exit 1
fi

# Crear archivo de configuración de logrotate para la aplicación
cat > /etc/logrotate.d/edf_catalogotablas << EOL
$PROJECT_DIR/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 $USER $USER
    sharedscripts
    postrotate
        # Reiniciar la aplicación si es necesario
        # pkill -HUP -f "gunicorn|flask"
    endscript
}
EOL

echo "Configuración de logrotate creada en /etc/logrotate.d/edf_catalogotablas"

# Configurar tarea programada para limpieza semanal
echo "Configurando tarea programada para limpieza de logs..."

# Crear un archivo de configuración para cron
CRON_JOB="0 2 * * 0 cd $PROJECT_DIR && $LOG_CLEANER --days 30 >> $LOG_FILE 2>&1"

# Agregar la tarea al crontab del usuario actual
(crontab -l 2>/dev/null | grep -v "$LOG_CLEANER"; echo "$CRON_JOB") | crontab -

# Verificar la configuración
echo "Tarea programada configurada. Tareas programadas actuales:"
crontab -l

echo "\nConfiguración completada. La limpieza de logs se ejecutará los domingos a las 2:00 AM."
echo "Los registros de la limpieza se guardarán en: $LOG_FILE"
