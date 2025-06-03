#!/usr/bin/env python3
# Script para verificar la comunicación entre la interfaz web y el sistema de ejecución de scripts
# Creado: 17/05/2025

import os
import sys
import json
import datetime
import platform

def main():
    """Función principal que verifica la comunicación con la interfaz web"""
    result = {
        "success": True,
        "timestamp": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "mensaje": "¡La comunicación entre la interfaz web y el sistema de ejecución de scripts funciona correctamente!",
        "entorno": {
            "python_version": sys.version,
            "platform": platform.platform(),
            "directorio_actual": os.getcwd(),
            "ruta_script": os.path.abspath(__file__),
            "usuario": os.getenv('USER', os.popen('whoami').read().strip())
        }
    }
    
    # Imprimir el resultado como JSON para que lo capture script_runner.py
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0

if __name__ == "__main__":
    sys.exit(main())
