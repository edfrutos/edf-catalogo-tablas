#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de migración para reemplazar maintenance_routes.py con la versión refactorizada.
Este script realiza una migración segura manteniendo un backup del archivo original.
"""

import os
import shutil
import sys
from datetime import datetime
from pathlib import Path

# Agregar el directorio raíz al path para importar módulos
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.logging_unified import get_logger

# Configurar logger
logger = get_logger(__name__)

def log_info(msg):
    logger.info(msg)
    print(f"INFO: {msg}")

def log_error(msg):
    logger.error(msg)
    print(f"ERROR: {msg}")

def log_warning(msg):
    logger.warning(msg)
    print(f"WARNING: {msg}")

def backup_original_file(original_path: Path, backup_dir: Path) -> Path:
    """Crea un backup del archivo original."""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_filename = f"maintenance_routes_backup_{timestamp}.py"
    backup_path = backup_dir / backup_filename
    
    try:
        # Crear directorio de backup si no existe
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Copiar archivo original
        shutil.copy2(original_path, backup_path)
        log_info(f"Backup creado: {backup_path}")
        return backup_path
    except Exception as e:
        log_error(f"Error creando backup: {str(e)}")
        raise

def validate_refactored_file(refactored_path: Path) -> bool:
    """Valida que el archivo refactorizado sea sintácticamente correcto."""
    try:
        # Intentar compilar el archivo
        with open(refactored_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        compile(content, str(refactored_path), 'exec')
        log_info("Archivo refactorizado validado sintácticamente")
        return True
    except SyntaxError as e:
        log_error(f"Error de sintaxis en archivo refactorizado: {str(e)}")
        return False
    except Exception as e:
        log_error(f"Error validando archivo refactorizado: {str(e)}")
        return False

def update_imports_in_main_app(main_app_path: Path) -> bool:
    """Actualiza las importaciones en main_app.py si es necesario."""
    try:
        with open(main_app_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Verificar si necesita actualización
        if 'from app.routes.maintenance_routes_refactored import register_maintenance_routes' in content:
            log_info("Las importaciones ya están actualizadas")
            return True
        
        # Actualizar importaciones
        updated_content = content.replace(
            'from app.routes.maintenance_routes import',
            'from app.routes.maintenance_routes_refactored import'
        )
        
        # Si no se encontró la importación específica, buscar patrones más generales
        if updated_content == content:
            # Buscar importaciones de maintenance_routes
            lines = content.split('\n')
            updated_lines = []
            
            for line in lines:
                if 'maintenance_routes' in line and 'import' in line and not line.strip().startswith('#'):
                    updated_line = line.replace('maintenance_routes', 'maintenance_routes_refactored')
                    updated_lines.append(updated_line)
                    log_info(f"Línea actualizada: {line.strip()} -> {updated_line.strip()}")
                else:
                    updated_lines.append(line)
            
            updated_content = '\n'.join(updated_lines)
        
        # Escribir archivo actualizado
        with open(main_app_path, 'w', encoding='utf-8') as f:
            f.write(updated_content)
        
        log_info("Importaciones actualizadas en main_app.py")
        return True
    except Exception as e:
        log_error(f"Error actualizando importaciones: {str(e)}")
        return False

def migrate_maintenance_routes():
    """Función principal de migración."""
    try:
        # Rutas de archivos
        project_root = Path(__file__).parent.parent
        routes_dir = project_root / 'app' / 'routes'
        original_path = routes_dir / 'maintenance_routes.py'
        refactored_path = routes_dir / 'maintenance_routes_refactored.py'
        backup_dir = project_root / 'backups' / 'migration'
        main_app_path = project_root / 'main_app.py'
        
        log_info("Iniciando migración de maintenance_routes.py")
        
        # Verificar que existan los archivos necesarios
        if not original_path.exists():
            log_error(f"Archivo original no encontrado: {original_path}")
            return False
        
        if not refactored_path.exists():
            log_error(f"Archivo refactorizado no encontrado: {refactored_path}")
            return False
        
        # Validar archivo refactorizado
        if not validate_refactored_file(refactored_path):
            log_error("El archivo refactorizado no es válido")
            return False
        
        # Crear backup del archivo original
        backup_path = backup_original_file(original_path, backup_dir)
        
        # Reemplazar archivo original con versión refactorizada
        try:
            shutil.copy2(refactored_path, original_path)
            log_info(f"Archivo reemplazado: {original_path}")
        except Exception as e:
            log_error(f"Error reemplazando archivo: {str(e)}")
            # Restaurar backup
            shutil.copy2(backup_path, original_path)
            log_info("Backup restaurado debido al error")
            return False
        
        # Actualizar importaciones en main_app.py si existe
        if main_app_path.exists():
            if not update_imports_in_main_app(main_app_path):
                log_warning("No se pudieron actualizar las importaciones automáticamente")
                log_info("Revisa manualmente las importaciones en main_app.py")
        
        # Crear archivo de información sobre la migración
        migration_info = {
            'timestamp': datetime.now().isoformat(),
            'original_backup': str(backup_path),
            'refactored_source': str(refactored_path),
            'target': str(original_path),
            'status': 'completed'
        }
        
        info_path = backup_dir / 'migration_info.json'
        import json
        with open(info_path, 'w', encoding='utf-8') as f:
            json.dump(migration_info, f, indent=2, ensure_ascii=False)
        
        log_info("Migración completada exitosamente")
        log_info(f"Backup disponible en: {backup_path}")
        log_info(f"Información de migración en: {info_path}")
        
        return True
        
    except Exception as e:
        log_error(f"Error durante la migración: {str(e)}")
        return False

def rollback_migration():
    """Revierte la migración usando el backup más reciente."""
    try:
        project_root = Path(__file__).parent.parent
        backup_dir = project_root / 'backups' / 'migration'
        routes_dir = project_root / 'app' / 'routes'
        original_path = routes_dir / 'maintenance_routes.py'
        
        log_info("Iniciando rollback de migración")
        
        # Buscar el backup más reciente
        backup_files = list(backup_dir.glob('maintenance_routes_backup_*.py'))
        if not backup_files:
            log_error("No se encontraron archivos de backup")
            return False
        
        # Ordenar por fecha de modificación (más reciente primero)
        backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        latest_backup = backup_files[0]
        
        log_info(f"Usando backup: {latest_backup}")
        
        # Restaurar backup
        shutil.copy2(latest_backup, original_path)
        log_info(f"Archivo restaurado: {original_path}")
        
        log_info("Rollback completado exitosamente")
        return True
        
    except Exception as e:
        log_error(f"Error durante el rollback: {str(e)}")
        return False

def show_migration_status():
    """Muestra el estado actual de la migración."""
    try:
        project_root = Path(__file__).parent.parent
        backup_dir = project_root / 'backups' / 'migration'
        info_path = backup_dir / 'migration_info.json'
        
        if info_path.exists():
            import json
            with open(info_path, 'r', encoding='utf-8') as f:
                info = json.load(f)
            
            print("\n=== Estado de Migración ===")
            print(f"Fecha: {info.get('timestamp')}")
            print(f"Estado: {info.get('status')}")
            print(f"Backup: {info.get('original_backup')}")
            print(f"Archivo objetivo: {info.get('target')}")
            print("============================\n")
        else:
            print("No se encontró información de migración")
            
        # Mostrar backups disponibles
        backup_files = list(backup_dir.glob('maintenance_routes_backup_*.py'))
        if backup_files:
            print(f"\nBackups disponibles ({len(backup_files)}):")
            for backup in sorted(backup_files, key=lambda x: x.stat().st_mtime, reverse=True):
                mtime = datetime.fromtimestamp(backup.stat().st_mtime)
                print(f"  - {backup.name} ({mtime.strftime('%Y-%m-%d %H:%M:%S')})")
        else:
            print("\nNo hay backups disponibles")
            
    except Exception as e:
        log_error(f"Error mostrando estado: {str(e)}")

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Migración de maintenance_routes.py')
    parser.add_argument('action', choices=['migrate', 'rollback', 'status'], 
                       help='Acción a realizar')
    
    args = parser.parse_args()
    
    if args.action == 'migrate':
        success = migrate_maintenance_routes()
        sys.exit(0 if success else 1)
    elif args.action == 'rollback':
        success = rollback_migration()
        sys.exit(0 if success else 1)
    elif args.action == 'status':
        show_migration_status()
        sys.exit(0)