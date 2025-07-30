#!/bin/bash

# Script para limpiar dependencias y generar un requirements.txt limpio

echo "=== Iniciando limpieza de dependencias ==="

# 1. Crear un entorno virtual limpio
echo "Creando entorno virtual limpio..."
python3 -m venv .venv_clean
source .venv_clean/bin/activate

# 2. Instalar las dependencias principales
echo "Instalando dependencias principales..."
pip install --upgrade pip
pip install flask pymongo gunicorn python-dotenv

# 3. Instalar dependencias opcionales (comentadas por defecto)
echo "Instalando dependencias opcionales..."
# pip install pydrive2 google-auth-oauthlib Pillow boto3

# 4. Generar requirements.txt
echo "Generando requirements.txt..."
pip freeze > requirements_clean.txt

# 5. Reemplazar el requirements.txt original
mv requirements_clean.txt requirements.txt

echo "=== Limpieza de dependencias completada ==="
echo "Se ha generado un archivo requirements.txt limpio"
echo "Puedes revisar los cambios con 'git diff requirements.txt'"

# 6. Desactivar el entorno virtual
deactivate
