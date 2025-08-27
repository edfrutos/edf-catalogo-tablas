#!/usr/bin/env python3
# Script Python para cargar variables de entorno
import os
import sys
from pathlib import Path

def load_env_variables():
    """Carga variables de entorno desde .env"""
    env_path = Path("/Users/edefrutos/edefrutos2025.xyz/edf_catalogotablas/.env")
    
    if not env_path.exists():
        print(f"❌ Archivo .env no encontrado: {env_path}")
        return False
    
    try:
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value
        
        print("✅ Variables de entorno cargadas desde .env")
        return True
        
    except Exception as e:
        print(f"❌ Error cargando variables de entorno: {e}")
        return False

if __name__ == "__main__":
    if load_env_variables():
        # Verificar que MONGO_URI esté disponible
        if os.environ.get('MONGO_URI'):
            print("✅ MONGO_URI configurada correctamente")
            sys.exit(0)
        else:
            print("❌ MONGO_URI no está configurada")
            sys.exit(1)
    else:
        sys.exit(1)
