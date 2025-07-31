#!/usr/bin/env python3
"""
Script de depuración para verificar la configuración del directorio de backups
"""

import os
import sys
from flask import Flask

# Agregar el directorio del proyecto al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main_app import create_app

def debug_backup_paths():
    """Depura las rutas de backup"""
    print("=== DEBUG: Configuración de Directorio de Backups ===")
    
    # Crear la aplicación Flask
    app = create_app()
    
    with app.app_context():
        print(f"1. current_app.root_path: {app.root_path}")
        print(f"2. __file__ (este script): {__file__}")
        print(f"3. os.path.dirname(__file__): {os.path.dirname(__file__)}")
        print(f"4. os.path.abspath(__file__): {os.path.abspath(__file__)}")
        print(f"5. os.getcwd(): {os.getcwd()}")
        
        # Calcular la ruta actual de backup según get_backup_dir()
        current_backup_dir = os.path.abspath(os.path.join(app.root_path, "..", "backups"))
        print(f"6. Directorio de backup actual (get_backup_dir): {current_backup_dir}")
        
        # Calcular la ruta correcta basada en el directorio del proyecto
        project_root = os.path.dirname(os.path.abspath(__file__))
        correct_backup_dir = os.path.join(project_root, "backups")
        print(f"7. Directorio de backup correcto: {correct_backup_dir}")
        
        # Verificar existencia de directorios
        print(f"\n=== Verificación de Existencia ===")
        print(f"¿Existe directorio actual? {os.path.exists(current_backup_dir)}")
        print(f"¿Existe directorio correcto? {os.path.exists(correct_backup_dir)}")
        
        # Listar contenido si existen
        if os.path.exists(current_backup_dir):
            try:
                files = os.listdir(current_backup_dir)
                print(f"Archivos en directorio actual: {files}")
            except PermissionError:
                print("Sin permisos para listar directorio actual")
        
        if os.path.exists(correct_backup_dir):
            try:
                files = os.listdir(correct_backup_dir)
                print(f"Archivos en directorio correcto: {files}")
            except PermissionError:
                print("Sin permisos para listar directorio correcto")

if __name__ == "__main__":
    debug_backup_paths()