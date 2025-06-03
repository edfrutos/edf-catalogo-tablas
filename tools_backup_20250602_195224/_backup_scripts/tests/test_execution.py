#!/usr/bin/env python3
# Script de prueba para verificar la ejecución de scripts
# Creado: 18/05/2025

import os
import sys
import datetime
import json

def main():
    """Función principal del script de prueba"""
    print("Script de prueba ejecutado correctamente")
    print(f"Fecha y hora: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Directorio actual: {os.getcwd()}")
    print(f"Python: {sys.version}")
    print(f"Argumentos: {sys.argv}")
    
    # Devolver un resultado en formato JSON para facilitar la lectura
    result = {
        "status": "success",
        "message": "Script de prueba ejecutado correctamente",
        "timestamp": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "environment": {
            "cwd": os.getcwd(),
            "python_version": sys.version,
            "user": os.getenv('USER', 'unknown'),
            "path": os.getenv('PATH', 'unknown')
        }
    }
    
    print(json.dumps(result, indent=2))
    return 0

if __name__ == "__main__":
    sys.exit(main())
