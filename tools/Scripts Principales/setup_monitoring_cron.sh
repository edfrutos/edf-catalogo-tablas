#!/bin/bash
# Script para configurar el monitoreo periódico de MongoDB
# Creado: 18/05/2025

# Definir variables
SCRIPT_PATH="/tools/monitor_mongodb.py"
PYTHON_PATH="/.venv/bin/python"
LOG_DIR="/logs"
CRON_FILE="/tmp/mongodb_monitor_cron"

# Crear directorio de logs si no existe
mkdir -p "$LOG_DIR"

# Crear archivo de cron temporal
cat > "$CRON_FILE" << EOF
# Monitoreo de MongoDB - Ejecutar cada hora
0 * * * * $PYTHON_PATH $SCRIPT_PATH >> $LOG_DIR/cron_monitor.log 2>&1

# Monitoreo adicional después de reinicios del servidor
@reboot sleep 60 && $PYTHON_PATH $SCRIPT_PATH >> $LOG_DIR/cron_monitor.log 2>&1
EOF

# Determinar el usuario actual
CURRENT_USER=$(whoami)

# Instalar el cron job
echo "Instalando cron job para el usuario $CURRENT_USER..."
crontab -l > /tmp/current_cron 2>/dev/null || echo "# Nuevo crontab" > /tmp/current_cron
if grep -q "monitor_mongodb.py" /tmp/current_cron; then
    echo "El cron job ya existe. Actualizando..."
    grep -v "monitor_mongodb.py" /tmp/current_cron > /tmp/updated_cron
    cat "$CRON_FILE" >> /tmp/updated_cron
    crontab /tmp/updated_cron
else
    echo "Añadiendo nuevo cron job..."
    cat /tmp/current_cron "$CRON_FILE" > /tmp/updated_cron
    crontab /tmp/updated_cron
fi

# Limpiar archivos temporales
rm -f "$CRON_FILE" /tmp/current_cron /tmp/updated_cron

echo "Cron job instalado correctamente."
echo "El monitoreo se ejecutará cada hora y después de reinicios del servidor."

# Ejecutar el script de monitoreo por primera vez
echo "Ejecutando el script de monitoreo por primera vez..."
$PYTHON_PATH $SCRIPT_PATH

echo "Configuración completada."
