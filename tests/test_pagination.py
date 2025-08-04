#!/usr/bin/env python3
import os
import sys
from datetime import datetime

# Simular las funciones exactas de la aplicación
def get_backup_dir():
    """Obtiene el directorio de respaldos, asegurando que exista"""
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    backup_dir = os.path.join(project_root, "backups")
    return backup_dir

def get_backup_files(backup_dir):
    """Obtiene la lista de archivos de backup disponibles"""
    try:
        if not os.path.exists(backup_dir):
            return []
        
        backup_files = []
        for file in os.listdir(backup_dir):
            if file.startswith("."):
                continue
            full_path = os.path.join(backup_dir, file)
            if not os.path.isfile(full_path):
                continue
            
            # Solo archivos de backup por extensión
            if not any(
                file.endswith(ext)
                for ext in [
                    ".bak", ".backup", ".zip", ".tar", ".gz", ".json.gz",
                    ".sql", ".dump", ".old", ".back", ".tmp", ".swp",
                    "~", ".csv", ".json",
                ]
            ):
                continue
            
            stats = os.stat(full_path)
            size_bytes = stats.st_size
            if size_bytes < 1024:
                size_str = f"{size_bytes} bytes"
            elif size_bytes < 1024 * 1024:
                size_str = f"{size_bytes / 1024:.2f} KB"
            else:
                size_str = f"{size_bytes / (1024 * 1024):.2f} MB"
            
            mod_time = datetime.fromtimestamp(stats.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
            
            backup_files.append({
                "name": file,
                "size": size_str,
                "modified": mod_time,
                "path": full_path,
            })
        
        # Ordenar y limitar a 20 más recientes
        backup_files.sort(key=lambda x: x["modified"], reverse=True)
        return backup_files[:20]
    except Exception as e:
        print(f"Error: {str(e)}")
        return []

def test_pagination():
    """Prueba la funcionalidad de paginación"""
    print("=== PRUEBA DE PAGINACIÓN ===\n")
    
    # Simular parámetros de request
    page = 1
    per_page = 5
    
    # Obtener todos los archivos
    backup_dir = get_backup_dir()
    backup_files_info = get_backup_files(backup_dir)
    total_backups = len(backup_files_info)
    
    print(f"Total de archivos: {total_backups}")
    print(f"Elementos por página: {per_page}")
    
    # Probar diferentes páginas
    for test_page in [1, 2, 3]:
        print(f"\n--- Página {test_page} ---")
        
        # Calcular paginación
        total_pages = (total_backups + per_page - 1) // per_page
        start_idx = (test_page - 1) * per_page
        end_idx = start_idx + per_page
        
        # Aplicar paginación
        backups = backup_files_info[start_idx:end_idx]
        
        print(f"  Elementos mostrados: {len(backups)}")
        print(f"  Rango: {start_idx + 1}-{min(end_idx, total_backups)} de {total_backups}")
        print(f"  Páginas totales: {total_pages}")
        
        if backups:
            print("  Primer elemento:", backups[0]['name'])
            print("  Último elemento:", backups[-1]['name'])
        else:
            print("  No hay elementos en esta página")
    
    # Probar diferentes tamaños de página
    print(f"\n--- Prueba de diferentes tamaños de página ---")
    for test_per_page in [5, 10, 20]:
        print(f"\nElementos por página: {test_per_page}")
        total_pages = (total_backups + test_per_page - 1) // test_per_page
        print(f"  Páginas totales: {total_pages}")
        
        # Mostrar primera página
        start_idx = 0
        end_idx = test_per_page
        backups = backup_files_info[start_idx:end_idx]
        print(f"  Página 1: {len(backups)} elementos")
        
        if total_pages > 1:
            # Mostrar última página
            start_idx = (total_pages - 1) * test_per_page
            end_idx = start_idx + test_per_page
            backups = backup_files_info[start_idx:end_idx]
            print(f"  Página {total_pages}: {len(backups)} elementos")

if __name__ == "__main__":
    test_pagination() 