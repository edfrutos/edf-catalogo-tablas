#!/usr/bin/env python3
# Script: migrate_discarded_files.py
# Descripción: Migra archivos descartados a un directorio separado para limpiar el espacio de trabajo
# Uso: python3 migrate_discarded_files.py [--dry-run] [--force]
# Requiere: os, shutil, argparse
# Variables de entorno: No aplica
# Autor: EDF Developer - 2025-01-27

import os
import shutil
import argparse
from datetime import datetime

def get_discarded_patterns():
    """Define patrones de archivos y directorios a descartar"""
    return {
        'files': [
            '*.md',           # Archivos de documentación
            '*.ipynb',        # Notebooks de Jupyter
            '*.txt',          # Archivos de texto
            '*.log',          # Archivos de log
            '*.tmp',          # Archivos temporales
            '*.bak',          # Archivos de respaldo
            '*.old',          # Archivos antiguos
            '*.orig',         # Archivos originales
            '*.pyc',          # Archivos compilados de Python
            '*.pyo',          # Archivos optimizados de Python
            '__pycache__',    # Directorios de caché de Python
            '.DS_Store',      # Archivos del sistema macOS
            'Thumbs.db',      # Archivos del sistema Windows
        ],
        'directories': [
            '_sincontenido',
            '_para colocar',
            'exportados',
            'backup',
            'temp',
            'tmp',
            'old',
            'deprecated',
            'obsolete',
        ],
        'name_patterns': [
            '🔍',             # Emojis en nombres
            '**',             # Asteriscos dobles
            'README',         # Archivos README
            'CHANGELOG',      # Archivos de cambios
            'LICENSE',        # Archivos de licencia
        ]
    }

def should_discard_file(filename, filepath):
    """Determina si un archivo debe ser descartado"""
    patterns = get_discarded_patterns()
    
    # Verificar extensiones de archivo
    for pattern in patterns['files']:
        if pattern.startswith('*.'):
            ext = pattern[1:]  # Obtener la extensión
            if filename.endswith(ext):
                return True, f"Extensión descartada: {ext}"
        elif pattern == filename:
            return True, f"Archivo descartado: {pattern}"
    
    # Verificar patrones en nombres
    for pattern in patterns['name_patterns']:
        if pattern in filename:
            return True, f"Patrón en nombre: {pattern}"
    
    # Verificar si es un directorio de caché
    if os.path.isdir(filepath) and filename in patterns['directories']:
        return True, f"Directorio descartado: {filename}"
    
    return False, ""

def scan_directory(directory_path):
    """Escanea un directorio y encuentra archivos a descartar"""
    discarded_files = []
    
    if not os.path.exists(directory_path):
        print(f"ERROR: El directorio {directory_path} no existe.")
        return discarded_files
    
    print(f"Escaneando directorio: {directory_path}")
    
    for root, dirs, files in os.walk(directory_path):
        # Procesar archivos
        for filename in files:
            filepath = os.path.join(root, filename)
            should_discard, reason = should_discard_file(filename, filepath)
            
            if should_discard:
                rel_path = os.path.relpath(filepath, directory_path)
                discarded_files.append({
                    'path': filepath,
                    'rel_path': rel_path,
                    'reason': reason,
                    'size': os.path.getsize(filepath) if os.path.exists(filepath) else 0
                })
        
        # Procesar directorios
        for dirname in dirs[:]:  # Copia para poder modificar durante la iteración
            dirpath = os.path.join(root, dirname)
            should_discard, reason = should_discard_file(dirname, dirpath)
            
            if should_discard:
                rel_path = os.path.relpath(dirpath, directory_path)
                discarded_files.append({
                    'path': dirpath,
                    'rel_path': rel_path,
                    'reason': reason,
                    'size': 0  # Los directorios no tienen tamaño directo
                })
                # Remover del listado para no procesar su contenido
                dirs.remove(dirname)
    
    return discarded_files

def create_discarded_directory(base_path):
    """Crea el directorio para archivos descartados"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    discarded_dir = os.path.join(base_path, f"discarded_files_{timestamp}")
    
    if not os.path.exists(discarded_dir):
        os.makedirs(discarded_dir)
        print(f"Directorio creado: {discarded_dir}")
    
    return discarded_dir

def move_discarded_files(discarded_files, target_dir, dry_run=False):
    """Mueve los archivos descartados al directorio objetivo"""
    moved_files = []
    errors = []
    
    for item in discarded_files:
        source_path = item['path']
        filename = os.path.basename(source_path)
        
        # Crear nombre único si hay conflictos
        target_path = os.path.join(target_dir, filename)
        counter = 1
        while os.path.exists(target_path):
            name, ext = os.path.splitext(filename)
            target_path = os.path.join(target_dir, f"{name}_{counter}{ext}")
            counter += 1
        
        if dry_run:
            print(f"[DRY RUN] Mover: {item['rel_path']} -> {os.path.relpath(target_path, target_dir)}")
            moved_files.append(item)
        else:
            try:
                if os.path.isdir(source_path):
                    shutil.move(source_path, target_path)
                else:
                    shutil.move(source_path, target_path)
                print(f"Movido: {item['rel_path']} -> {os.path.relpath(target_path, target_dir)}")
                moved_files.append(item)
            except Exception as e:
                error_msg = f"Error moviendo {item['rel_path']}: {str(e)}"
                print(f"ERROR: {error_msg}")
                errors.append(error_msg)
    
    return moved_files, errors

def main():
    parser = argparse.ArgumentParser(description='Migra archivos descartados a un directorio separado')
    parser.add_argument('--dry-run', action='store_true', help='Mostrar qué se haría sin ejecutar')
    parser.add_argument('--force', action='store_true', help='Forzar la migración sin confirmación')
    parser.add_argument('--directory', default='tools', help='Directorio a escanear (default: tools)')
    
    args = parser.parse_args()
    
    print("=== Migración de Archivos Descartados ===")
    print(f"Directorio a escanear: {args.directory}")
    print(f"Modo dry-run: {'Sí' if args.dry_run else 'No'}")
    
    # Escanear archivos descartados
    discarded_files = scan_directory(args.directory)
    
    if not discarded_files:
        print("No se encontraron archivos para descartar.")
        return
    
    # Mostrar resumen
    print(f"\nArchivos encontrados para descartar: {len(discarded_files)}")
    total_size = sum(item['size'] for item in discarded_files)
    print(f"Tamaño total: {total_size / 1024:.2f} KB")
    
    print("\nArchivos a descartar:")
    for item in discarded_files:
        print(f"  - {item['rel_path']} ({item['reason']})")
    
    # Confirmar si no es dry-run y no se fuerza
    if not args.dry_run and not args.force:
        confirm = input(f"\n¿Desea mover {len(discarded_files)} archivos? (s/N): ").strip().lower()
        if confirm != 's':
            print("Operación cancelada.")
            return
    
    # Crear directorio objetivo
    target_dir = create_discarded_directory(args.directory)
    
    # Mover archivos
    moved_files, errors = move_discarded_files(discarded_files, target_dir, args.dry_run)
    
    # Resumen final
    print(f"\n=== Resumen ===")
    print(f"Archivos procesados: {len(moved_files)}")
    if errors:
        print(f"Errores: {len(errors)}")
        for error in errors:
            print(f"  - {error}")
    
    if not args.dry_run:
        print(f"Archivos movidos a: {target_dir}")
        print("Migración completada.")

if __name__ == "__main__":
    main() 