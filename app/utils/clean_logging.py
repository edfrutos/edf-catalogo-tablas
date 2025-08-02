#!/usr/bin/env python3
"""
Script para limpiar logs verbosos del sistema.
"""

import os
import sys
import glob
from datetime import datetime, timedelta

# Agregar el directorio raíz al path
script_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(script_dir)
sys.path.insert(0, root_dir)

def clean_logs():
    """Limpiar logs verbosos del sistema"""
    try:
        print("🧹 Iniciando limpieza de logs...")
        
        # Directorio de logs
        log_dir = os.path.join(root_dir, 'logs')
        if not os.path.exists(log_dir):
            print("📁 Directorio de logs no encontrado")
            return True
        
        # Buscar archivos de log
        log_files = glob.glob(os.path.join(log_dir, '*.log'))
        print(f"📁 Encontrados {len(log_files)} archivos de log")
        
        cleaned_count = 0
        total_size_before = 0
        total_size_after = 0
        
        for log_file in log_files:
            try:
                # Obtener tamaño antes
                size_before = os.path.getsize(log_file)
                total_size_before += size_before
                
                # Leer archivo y filtrar líneas verbosas
                with open(log_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                # Filtrar líneas (mantener solo errores y warnings importantes)
                filtered_lines = []
                for line in lines:
                    # Mantener líneas importantes
                    if any(keyword in line.lower() for keyword in ['error', 'warning', 'critical', 'exception']):
                        filtered_lines.append(line)
                    # Mantener líneas de inicio/fin de sesión
                    elif any(keyword in line.lower() for keyword in ['login', 'logout', 'session']):
                        filtered_lines.append(line)
                    # Mantener líneas de configuración
                    elif any(keyword in line.lower() for keyword in ['config', 'setup', 'init']):
                        filtered_lines.append(line)
                
                # Escribir archivo filtrado
                with open(log_file, 'w', encoding='utf-8') as f:
                    f.writelines(filtered_lines)
                
                # Obtener tamaño después
                size_after = os.path.getsize(log_file)
                total_size_after += size_after
                
                if size_before != size_after:
                    cleaned_count += 1
                    print(f"   ✅ {os.path.basename(log_file)}: {size_before/1024:.1f}KB → {size_after/1024:.1f}KB")
                
            except Exception as e:
                print(f"   ❌ Error procesando {os.path.basename(log_file)}: {e}")
        
        # Resumen
        size_saved = total_size_before - total_size_after
        print(f"\n📊 Resumen de limpieza:")
        print(f"   Archivos procesados: {len(log_files)}")
        print(f"   Archivos limpiados: {cleaned_count}")
        print(f"   Espacio liberado: {size_saved/1024:.1f}KB")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en limpieza de logs: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Iniciando limpieza de logs...")
    success = clean_logs()
    sys.exit(0 if success else 1) 