#!/usr/bin/env python3
"""
Script para corregir todos los imports restantes de run_db_script
"""

import os
import re


def fix_remaining_imports():
    """Corrige todos los imports restantes de run_db_script"""

    print("🔧 CORRECCIÓN DE IMPORTS RESTANTES")
    print("=" * 60)

    # Archivos que necesitan corrección
    files_to_fix = [
        "app/routes/admin_routes.py",
        "app/routes/admin/admin_backups.py",
        "app/routes/maintenance_routes.py",
        "app/routes/maintenance_routes_refactored.py",
        "app/utils/storage_utils.py",
        "app/utils/backup_utils.py",
        "scripts/maintenance/10_backup_incremental.py",
        "descarga_msanual_de_google.py"
    ]

    # Patrones de búsqueda y reemplazo
    patterns = [
        # Imports de run_db_script
        (r'from app\.utils\.script_manager import run_db_script upload_to_drive', 'from app.utils.google_drive_wrapper import upload_to_drive'),
        (r'from app\.utils\.script_manager import run_db_script download_file', 'from app.utils.google_drive_wrapper import download_file'),
        (r'from app\.utils\.script_manager import run_db_script list_files_in_folder', 'from app.utils.google_drive_wrapper import list_files_in_folder'),
        (r'from app\.utils\.script_manager import run_db_script delete_file', 'from app.utils.google_drive_wrapper import delete_file'),
        (r'from app\.utils\.script_manager import run_db_script get_drive', 'from app.utils.google_drive_wrapper import get_drive'),
        (r'from app\.utils\.script_manager import run_db_script get_or_create_folder, list_files_in_folder', 'from app.utils.google_drive_wrapper import get_or_create_folder, list_files_in_folder'),

        # Llamadas a run_db_script que necesitan ser reemplazadas
        (r'run_db_script\("google_drive_utils\.py", "upload_to_drive", ([^)]+)\)', r'upload_to_drive(\1)'),
        (r'run_db_script\("google_drive_utils\.py", "download_file", ([^)]+)\)', r'download_file(\1)'),
        (r'run_db_script\("google_drive_utils\.py", "list_files_in_folder", ([^)]+)\)', r'list_files_in_folder(\1)'),
        (r'run_db_script\("google_drive_utils\.py", "delete_file", ([^)]+)\)', r'delete_file(\1)'),
        (r'run_db_script\("google_drive_utils\.py", "get_drive"\)', r'get_drive()'),
        (r'run_db_script\("google_drive_utils\.py", "get_or_create_folder", ([^)]+)\)', r'get_or_create_folder(\1)'),
    ]

    total_fixes = 0

    for file_path in files_to_fix:
        if not os.path.exists(file_path):
            print(f"⚠️  Archivo no encontrado: {file_path}")
            continue

        print(f"\n📁 Procesando: {file_path}")

        try:
            # Leer el archivo
            with open(file_path, encoding='utf-8') as f:
                content = f.read()

            original_content = content
            file_fixes = 0

            # Aplicar todas las correcciones
            for pattern, replacement in patterns:
                matches = re.findall(pattern, content)
                if matches:
                    content = re.sub(pattern, replacement, content)
                    file_fixes += len(matches)
                    print(f"   ✅ {len(matches)} correcciones: {pattern[:50]}...")

            # Si hubo cambios, escribir el archivo
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"   💾 Archivo actualizado con {file_fixes} correcciones")
                total_fixes += file_fixes
            else:
                print("   ℹ️  No se encontraron correcciones necesarias")

        except Exception as e:
            print(f"   ❌ Error procesando archivo: {e}")

    print("\n" + "=" * 60)
    print("✅ CORRECCIÓN COMPLETADA")
    print(f"📊 Total de correcciones: {total_fixes}")
    print(f"🎯 Archivos procesados: {len(files_to_fix)}")

    return total_fixes

if __name__ == "__main__":
    fix_remaining_imports()
