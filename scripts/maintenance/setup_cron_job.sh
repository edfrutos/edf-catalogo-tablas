#!/bin/bash
# Script para configurar la tarea programada usando crontab
# Uso: ./setup_cron_job.sh

# Directorios y rutas
PROJECT_DIR="/Users/edefrutos/_Repositorios/01.IDE_Cursor/edf_catalogotablas"
SCRIPT_PATH="$PROJECT_DIR/scripts/maintenance/clean_old_logs.py"
LOG_FILE="$PROJECT_DIR/logs/cleanup_job.log"

# Crear directorio de logs si no existe
mkdir -p "$PROJECT_DIR/logs"
chmod 755 "$PROJECT_DIR/logs"

# Crear un archivo temporal con el crontab actual
TEMP_CRON=$(mktemp /tmp/cron.XXXXXXXXX)

# Obtener el crontab actual (si existe) y filtrar cualquier entrada existente de nuestro script
crontab -l 2>/dev/null | grep -v "$SCRIPT_PATH" > "$TEMP_CRON" || true

# Añadir nuestra nueva tarea al final del archivo
echo "# Limpieza automática de logs - EDF Catalogo Tablas" >> "$TEMP_CRON"
echo "0 2 * * 0 cd $PROJECT_DIR && $PROJECT_DIR/.venv310/bin/python3 $SCRIPT_PATH --days 30 >> $LOG_FILE 2>&1" >> "$TEMP_CRON"

# Instalar el nuevo crontab
crontab "$TEMP_CRON"
rm -f "$TEMP_CRON"

# Verificar que se instaló correctamente
echo "✅ Tarea programada configurada correctamente en crontab"
echo "📋 Verifica con: crontab -l"
echo "📝 Los logs se guardarán en: $LOG_FILE"
echo "\nPara probar la tarea manualmente ejecuta:"
echo "cd $PROJECT_DIR && $PROJECT_DIR/.venv310/bin/python3 $SCRIPT_PATH --days 30"
