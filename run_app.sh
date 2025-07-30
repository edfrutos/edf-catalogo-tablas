#!/bin/bash
# Script para ejecutar la aplicación con el entorno virtual activado
# Uso: ./run_app.sh

# Obtener el directorio del script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Verificar que existe el entorno virtual
if [ ! -d "venv310" ]; then
    echo "Error: No se encontró el directorio venv310"
    echo "Asegúrate de que el entorno virtual esté en: $SCRIPT_DIR/venv310"
    exit 1
fi

# Verificar que existe el archivo de activación
if [ ! -f "venv310/bin/activate" ]; then
    echo "Error: No se encontró venv310/bin/activate"
    echo "El entorno virtual parece estar dañado o incompleto"
    exit 1
fi

# Verificar que existe main_app.py
if [ ! -f "main_app.py" ]; then
    echo "Error: No se encontró main_app.py"
    echo "Asegúrate de estar en el directorio correcto del proyecto"
    exit 1
fi

# Activar el entorno virtual y ejecutar la aplicación
echo "Activando entorno virtual..."
source venv310/bin/activate

echo "Ejecutando main_app.py..."
python main_app.py

# El entorno virtual se desactiva automáticamente al finalizar el script
