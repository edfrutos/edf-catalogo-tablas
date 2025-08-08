#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script: restore_missing_files.py
Descripción: Restaura archivos específicos que existen en ubicaciones originales
Uso: python3 restore_missing_files.py
Requiere: os, shutil, pathlib
Variables de entorno: Ninguna
Autor: EDF Developer - 2025-01-27
"""

import os
import shutil
from pathlib import Path


def restore_missing_files():
    """Restaura archivos específicos que existen en ubicaciones originales."""
    root_dir = Path(__file__).parent.parent.parent.parent

    # Mapeo específico de archivos que sabemos que existen
    file_mapping = {
        # Scripts de tools/Scripts Principales
        "tools/local/admin_utils/check_users.py": "tools/Scripts Principales/check_users.py",
        "tools/local/admin_utils/insert_admin_and_minimum_data.py": "tools/Scripts Principales/insert_admin_and_minimum_data.py",
        "tools/local/admin_utils/admin_shell.py": "tools/Scripts Principales/admin_shell.py",
        "tools/local/admin_utils/check_admin_role.py": "tools/Scripts Principales/check_admin_role.py",
        "tools/local/admin_utils/05_reasignar_owners_huerfanos.py": "tools/Scripts Principales/05_reasignar_owners_huerfanos.py",
        "tools/local/admin_utils/06_eliminar_duplicados_users.py": "tools/Scripts Principales/06_eliminar_duplicados_users.py",
        "tools/local/admin_utils/admin_utils.py": "tools/Scripts Principales/admin_utils.py",
        "tools/local/admin_utils/07_eliminar_huerfanos.py": "tools/Scripts Principales/07_eliminar_huerfanos.py",
        # Scripts de tools/maintenance
        "tools/local/maintenance/03_validar_integridad.py": "tools/maintenance/03_validar_integridad.py",
        "tools/local/maintenance/04_limpieza_automatizada.py": "tools/maintenance/04_limpieza_automatizada.py",
        "tools/local/maintenance/08_backup_colecciones.py": "tools/maintenance/08_backup_colecciones.py",
        "tools/local/maintenance/09_backup_restore_total.py": "tools/maintenance/09_backup_restore_total.py",
        "tools/local/maintenance/clean_images_scheduled.py": "tools/maintenance/clean_images_scheduled.py",
        # Scripts de tools/utils
        "tools/local/utils/fix_script_paths.py": "tools/utils/fix_script_paths.py",
        "tools/local/utils/organize_root_scripts.py": "tools/organize_root_scripts.py",
        "tools/local/utils/organize_root_directory.py": "tools/organize_root_directory.py",
        "tools/local/utils/add_words_to_config.py": "tools/add_words_to_config.py",
        # Scripts de tests
        "tests/local/unit/check_test_user.py": "tests/check_test_user.py",
        "tests/local/unit/check_test_user_ssl_fix.py": "tests/check_test_user_ssl_fix.py",
        "tests/local/unit/test_pagination.py": "tests/test_pagination.py",
        "tests/local/unit/conftest.py": "tests/conftest.py",
        "tests/local/unit/create_test_user.py": "tests/create_test_user.py",
        # Scripts de tests/legacy
        "tests/local/unit/listar_rutas.py": "tests/legacy/listar_rutas.py",
        "tests/local/unit/diagnostico_sesion.py": "tests/legacy/diagnostico_sesion.py",
        "tests/local/unit/diagnostico_catalogs.py": "tests/legacy/diagnostico_catalogs.py",
        "tests/local/unit/diagnostico_sesion_completo.py": "tests/legacy/diagnostico_sesion_completo.py",
        "tests/local/unit/debug_rutas_catalogs.py": "tests/legacy/debug_rutas_catalogs.py",
        "tests/local/unit/diagnostico_completo.py": "tests/legacy/diagnostico_completo.py",
        "tests/local/unit/diagnostico_acceso.py": "tests/legacy/diagnostico_acceso.py",
        # Scripts de tests/integration
        "tests/local/integration/test_session_direct.py": "tests/integration/test_session_direct.py",
        "tests/local/integration/test_gdrive.py": "tests/integration/test_gdrive.py",
        "tests/local/integration/test_session_simple.py": "tests/integration/test_session_simple.py",
        "tests/local/integration/test_auth.py": "tests/integration/test_auth.py",
        "tests/local/integration/test_admin_panel_actions_full.py": "tests/integration/test_admin_panel_actions_full.py",
        "tests/local/integration/test_gdrive_v2.py": "tests/integration/test_gdrive_v2.py",
        "tests/local/integration/test_maintenance_dashboard.py": "tests/integration/test_maintenance_dashboard.py",
        "tests/local/integration/test_catalogs_crud.py": "tests/integration/test_catalogs_crud.py",
        "tests/local/integration/test_catalogs_routes.py": "tests/integration/test_catalogs_routes.py",
        "tests/local/integration/test_catalogs_rows.py": "tests/integration/test_catalogs_rows.py",
        "tests/local/integration/test_admin_panel_actions.py": "tests/integration/test_admin_panel_actions.py",
        "tests/local/integration/test_main_routes.py": "tests/integration/test_main_routes.py",
        "tests/local/integration/test_login_produccion.py": "tests/integration/test_login_produccion.py",
        "tests/local/integration/test_upload_simple.py": "tests/integration/test_upload_simple.py",
        "tests/local/integration/test_mongo_connection.py": "tests/integration/test_mongo_connection.py",
        "tests/local/integration/test_login_direct.py": "tests/integration/test_login_direct.py",
        "tests/local/integration/test_mongodb_integration.py": "tests/integration/test_mongodb_integration.py",
        "tests/local/integration/test_blueprints_smoke.py": "tests/integration/test_blueprints_smoke.py",
        "tests/local/integration/test_mongo.py": "tests/integration/test_mongo.py",
        "tests/local/integration/test_session_integration.py": "tests/integration/test_session_integration.py",
        "tests/local/integration/test_s3_cors.py": "tests/integration/test_s3_cors.py",
        "tests/local/integration/test_admin_dashboard.py": "tests/integration/test_admin_dashboard.py",
        "tests/local/integration/test_auth_routes.py": "tests/integration/test_auth_routes.py",
        "tests/local/integration/test_admin_api.py": "tests/integration/test_admin_api.py",
        "tests/local/integration/test_gdrive_upload.py": "tests/integration/test_gdrive_upload.py",
        "tests/local/integration/test_admin_panel.py": "tests/integration/test_admin_panel.py",
        "tests/local/integration/test_auth_20250515_124406.py": "tests/integration/test_auth_20250515_124406.py",
        "tests/local/integration/test_app_integration.py": "tests/integration/test_app_integration.py",
        # Scripts de tests/app/routes
        "tests/local/functional/test_catalogs_routes_func.py": "tests/app/routes/test_catalogs_routes_func.py",
        "tests/local/functional/test_errors_routes_func.py": "tests/app/routes/test_errors_routes_func.py",
        "tests/local/functional/test_catalogs_crud_func.py": "tests/app/routes/test_catalogs_crud_func.py",
        "tests/local/functional/test_session_routes.py": "tests/app/routes/test_session_routes.py",
        "tests/local/functional/test_auth_routes_func.py": "tests/app/routes/test_auth_routes_func.py",
        "tests/local/functional/test_auth_user_flow_func.py": "tests/app/routes/test_auth_user_flow_func.py",
        "tests/local/functional/test_session_routes_test.py": "tests/app/routes/test_session_routes_test.py",
        "tests/local/functional/test_emergency_routes_func.py": "tests/app/routes/test_emergency_routes_func.py",
        "tests/local/functional/test_image_routes_func.py": "tests/app/routes/test_image_routes_func.py",
        "tests/local/functional/test_usuarios_routes_func.py": "tests/app/routes/test_usuarios_routes_func.py",
        "tests/local/functional/test_flash_func.py": "tests/app/routes/test_flash_func.py",
        "tests/local/functional/test_admin_routes_func.py": "tests/app/routes/test_admin_routes_func.py",
        "tests/local/functional/test_main_routes_func.py": "tests/app/routes/test_main_routes_func.py",
    }

    restored_files = []
    failed_files = []

    print("🔄 Restaurando archivos faltantes desde ubicaciones originales...")
    print("=" * 60)

    for damaged_file, original_file in file_mapping.items():
        damaged_path = root_dir / damaged_file
        original_path = root_dir / original_file

        if original_path.exists():
            try:
                # Crear directorio de destino si no existe
                damaged_path.parent.mkdir(parents=True, exist_ok=True)

                # Copiar archivo original
                shutil.copy2(original_path, damaged_path)

                # Verificar que se copió correctamente
                if damaged_path.exists() and damaged_path.stat().st_size > 100:
                    restored_files.append(damaged_file)
                    print(f"  ✅ Restaurado: {damaged_file}")
                else:
                    failed_files.append(damaged_file)
                    print(f"  ❌ Falló restauración: {damaged_file}")
            except Exception as e:
                failed_files.append(damaged_file)
                print(f"  ❌ Error restaurando {damaged_file}: {e}")
        else:
            print(f"  ⚠️  Archivo original no existe: {original_file}")

    print("\n" + "=" * 60)
    print(f"📊 Resumen de restauración:")
    print(f"  ✅ Archivos restaurados: {len(restored_files)}")
    print(f"  ❌ Archivos fallidos: {len(failed_files)}")

    if failed_files:
        print(f"\n❌ Archivos que fallaron:")
        for file in failed_files:
            print(f"  - {file}")

    print("\n🎉 Proceso de restauración completado.")


if __name__ == "__main__":
    restore_missing_files()
