#!/usr/bin/env python3
"""
Script para gestionar el sistema de logging unificado.
"""

import logging
import os
import sys
from datetime import datetime

# Agregar el directorio raíz al path
script_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(os.path.dirname(script_dir))  # Subir dos niveles: utils -> app -> raíz
sys.path.insert(0, root_dir)

def setup_logging():
    """Configurar el sistema de logging unificado"""
    try:
        from app.logging_unified import setup_unified_logging

        print("🔧 Configurando sistema de logging unificado...")
        setup_unified_logging()
        print("✅ Sistema de logging configurado correctamente")

        # Mostrar información del logging
        log_dir = os.path.join(root_dir, 'logs')
        if os.path.exists(log_dir):
            log_files = [f for f in os.listdir(log_dir) if f.endswith('.log')]
            print(f"📁 Archivos de log encontrados: {len(log_files)}")
            for log_file in log_files[:5]:  # Mostrar solo los primeros 5
                print(f"   - {log_file}")

        return True

    except ImportError as e:
        print(f"❌ Error importando módulo: {e}")
        return False
    except Exception as e:
        print(f"❌ Error configurando logging: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Iniciando configuración de logging unificado...")
    success = setup_logging()
    sys.exit(0 if success else 1)
