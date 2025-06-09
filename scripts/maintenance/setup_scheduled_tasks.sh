#!/bin/bash
# scripts/maintenance/setup_scheduled_tasks.sh

# Configuración
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
VENV_PYTHON="$PROJECT_DIR/.venv310/bin/python3"
MAINTENANCE_SCRIPT="$SCRIPT_DIR/run_maintenance.py"
LOG_DIR="$PROJECT_DIR/logs"

# Crear directorios necesarios
mkdir -p "$LOG_DIR"
mkdir -p "$SCRIPT_DIR/logs"

# Hacer ejecutables los scripts
chmod +x "$MAINTENANCE_SCRIPT"
chmod +x "$SCRIPT_DIR/clean_old_logs.py"

# Configurar tarea programada para limpieza semanal (domingo a las 2:00 AM)
(crontab -l 2>/dev/null | grep -v "$MAINTENANCE_SCRIPT"; \
 echo "0 2 * * 0 cd $PROJECT_DIR && $VENV_PYTHON $MAINTENANCE_SCRIPT --task logs --days 30 >> $LOG_DIR/maintenance.log 2>&1") | crontab -

# Configurar verificación diaria de MongoDB (a las 3:00 AM)
(crontab -l 2>/dev/null | grep -v "check_mongodb"; \
 echo "0 3 * * * cd $PROJECT_DIR && $VENV_PYTHON $MAINTENANCE_SCRIPT --task mongo >> $LOG_DIR/mongodb_check.log 2>&1") | crontab -

# Configurar verificación semanal de espacio en disco (domingo a las 1:00 AM)
(crontab -l 2>/dev/null | grep -v "check_disk"; \
 echo "0 1 * * 0 cd $PROJECT_DIR && $VENV_PYTHON $MAINTENANCE_SCRIPT --task disk >> $LOG_DIR/disk_check.log 2>&1") | crontab -

echo "✅ Tareas programadas configuradas correctamente"
echo "📋 Tareas programadas actuales:"
crontab -l