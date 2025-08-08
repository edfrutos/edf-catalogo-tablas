#!/bin/bash
# Script para reiniciar el servidor Gunicorn de forma segura
# Creado: 17/05/2025

echo "=== REINICIANDO SERVIDOR GUNICORN ==="
echo "Fecha y hora: $(date)"

# Obtener el PID del proceso Gunicorn principal
GUNICORN_PID=$(pgrep -f "gunicorn.*app:app")

if [ -z "$GUNICORN_PID" ]; then
    echo "No se encontró ningún proceso Gunicorn en ejecución."
    echo "Iniciando nuevo servidor Gunicorn..."
    
    # Iniciar Gunicorn (ajustar según la configuración de tu servidor)
    cd "$(dirname "$0")/../.."  # Navegar al directorio raíz del proyecto
    gunicorn --bind 127.0.0.1:8001 --workers 4 app:app --daemon
    
    echo "Servidor Gunicorn iniciado."
else
    echo "Proceso Gunicorn encontrado con PID: $GUNICORN_PID"
    echo "Enviando señal de reinicio (HUP)..."
    
    # Enviar señal HUP para reiniciar workers sin tiempo de inactividad
    kill -HUP $GUNICORN_PID
    
    echo "Señal enviada. El servidor debería reiniciarse sin tiempo de inactividad."
fi

echo "=== REINICIO COMPLETADO ==="
echo "Verificando procesos Gunicorn activos:"
ps aux | grep gunicorn | grep -v grep

exit 0
