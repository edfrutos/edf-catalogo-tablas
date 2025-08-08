#!/bin/bash
# Script para configurar la rotación automática de logs en macOS
# Uso: ./setup_macos_log_rotation.sh

# Verificar que estamos en macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo "Este script es solo para macOS"
    exit 1
fi

# Directorios y rutas
PROJECT_DIR="/Users/edefrutos/_Repositorios/edf_catalogotablas"
SCRIPT_PATH="$PROJECT_DIR/tools/maintenance/clean_old_logs.py"
LOG_DIR="$PROJECT_DIR/logs"
LOG_FILE="$LOG_DIR/cleanup_job.log"
PLIST_NAME="com.edf_catalogotablas.cleanlogs"
PLIST_PATH="$HOME/Library/LaunchAgents/${PLIST_NAME}.plist"

# Crear directorio de logs si no existe
mkdir -p "$LOG_DIR"
chmod 755 "$LOG_DIR"

# Crear archivo de configuración launchd
cat > "$PLIST_PATH" << EOL
<?xml version="1.0" encoding="UTF-8"
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>$PLIST_NAME</string>
    
    <key>ProgramArguments</key>
    <array>
        <string>$PROJECT_DIR/venv310/bin/python3</string>
        <string>$SCRIPT_PATH</string>
        <string>--days</string>
        <string>30</string>
    </array>
    
    <key>StandardOutPath</key>
    <string>$LOG_FILE</string>
    
    <key>StandardErrorPath</key>
    <string>$LOG_FILE</string>
    
    <key>WorkingDirectory</key>
    <string>$PROJECT_DIR</string>
    
    <key>RunAtLoad</key>
    <false/>
    
    <key>StartCalendarInterval</key>
    <dict>
        <key>Weekday</key>
        <integer>0</integer>
        <key>Hour</key>
        <integer>2</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>$PATH</string>
        <key>PYTHONPATH</key>
        <string>$PROJECT_DIR</string>
    </dict>
</dict>
</plist>
EOL

# Asegurar permisos correctos
chmod 644 "$PLIST_PATH"

# Cargar el job en launchd
launchctl unload "$PLIST_PATH" 2>/dev/null
launchctl load -w "$PLIST_PATH"

# Verificar que el job se cargó correctamente
if launchctl list | grep -q "$PLIST_NAME"; then
    echo "✅ Tarea programada configurada correctamente en launchd"
    echo "🔍 Verifica con: launchctl list | grep $PLIST_NAME"
    echo "📋 Configuración guardada en: $PLIST_PATH"
    echo "📝 Los logs se guardarán en: $LOG_FILE"
    echo "\nPara probar la tarea manualmente ejecuta:"
    echo "launchctl start $PLIST_NAME"
else
    echo "❌ Error al configurar la tarea programada"
    echo "Intenta cargarla manualmente con:"
    echo "launchctl load -w $PLIST_PATH"
    exit 1
fi
