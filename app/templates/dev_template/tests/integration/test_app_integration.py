# Script: test_app.py
# Descripción: [Explica brevemente qué hace el script]
# Uso: python3 test_app.py [opciones]
# Requiere: [librerías externas, si aplica]
# Variables de entorno: [si aplica]
# Autor: EDF Developer - 2025-05-28

import os
import tempfile
import pytest
from dotenv import load_dotenv


def test_env_variables():
    """Prueba la carga de variables de entorno desde un archivo .env."""
    # Crear un archivo .env temporal con variables de prueba
    with tempfile.NamedTemporaryFile(mode='w+', suffix='.env', delete=False) as temp_env:
        temp_env.write('PRUEBA_VARIABLE1=valor1\n')
        temp_env.write('PRUEBA_VARIABLE2=valor2\n')
        temp_env.write('PRUEBA_VARIABLE3=valor3\n')
        temp_env_path = temp_env.name
    
    try:
        # Cargar las variables de entorno desde el archivo .env temporal
        load_dotenv(temp_env_path)
        
        # Verificar que las variables están disponibles en os.environ
        assert os.environ.get('PRUEBA_VARIABLE1') == 'valor1'
        assert os.environ.get('PRUEBA_VARIABLE2') == 'valor2'
        assert os.environ.get('PRUEBA_VARIABLE3') == 'valor3'
    
    finally:
        # Limpiar el archivo temporal para no dejar residuos
        if os.path.exists(temp_env_path):
            os.unlink(temp_env_path)

