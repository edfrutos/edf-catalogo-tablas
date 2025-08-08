#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script: restore_damaged_files.py
Descripción: Restaura archivos dañados por correcciones automáticas
Uso: python3 restore_damaged_files.py
Requiere: os, shutil, pathlib
Variables de entorno: Ninguna
Autor: EDF Developer - 2025-01-27
"""

import os
import shutil
from pathlib import Path


def restore_damaged_files():
    """Restaura archivos dañados desde Git."""
    root_dir = Path(__file__).parent.parent.parent.parent

    # Lista de archivos críticos a restaurar
    critical_files = [
        # Scripts de mantenimiento
        "scripts/maintenance/09_backup_restore_total.py",
        "scripts/maintenance/run_maintenance.py",
        "scripts/maintenance/08_backup_colecciones.py",
        "scripts/maintenance/10_backup_incremental.py",
        "scripts/maintenance/clean_old_logs.py",
        "scripts/maintenance/clean_images.py",
        "scripts/maintenance/clean_images_improved.py",
        "scripts/maintenance/clean_images_scheduled.py",
        "scripts/maintenance/cleanup_duplicates.py",
        "scripts/maintenance/cleanup_deps.py",
        "scripts/maintenance/clean_caches.py",
        "scripts/maintenance/monitor_mongodb.py",
        "scripts/maintenance/advanced_monitor.py",
        "scripts/maintenance/check_logs.py",
        # Scripts principales de tools
        "tools/Scripts Principales/conexion_MongoDB.py",
        "tools/Scripts Principales/09_backup_restore_total.py",
        "tools/Scripts Principales/08_backup_colecciones.py",
        "tools/Scripts Principales/10_backup_incremental.py",
        "tools/Scripts Principales/03_validar_integridad.py",
        "tools/Scripts Principales/04_limpieza_automatizada.py",
        "tools/Scripts Principales/05_reasignar_owners_huerfanos.py",
        "tools/Scripts Principales/06_eliminar_duplicados_users.py",
        "tools/Scripts Principales/07_eliminar_huerfanos.py",
        "tools/Scripts Principales/admin_shell.py",
        "tools/Scripts Principales/admin_utils.py",
        "tools/Scripts Principales/advanced_monitor.py",
        "tools/Scripts Principales/arreglar_catalogos.py",
        "tools/Scripts Principales/check_admin_role.py",
        "tools/Scripts Principales/check_catalog.py",
        "tools/Scripts Principales/check_collections.py",
        "tools/Scripts Principales/check_db.py",
        "tools/Scripts Principales/check_logs.py",
        "tools/Scripts Principales/check_mongodb.py",
        "tools/Scripts Principales/check_mongodb_compat.py",
        "tools/Scripts Principales/check_role_admin.py",
        "tools/Scripts Principales/check_users.py",
        "tools/Scripts Principales/clean_images_scheduled.py",
        "tools/Scripts Principales/diagnose_scripts.py",
        "tools/Scripts Principales/insert_admin_and_minimum_data.py",
        "tools/Scripts Principales/migracion_catalogos.py",
        "tools/Scripts Principales/normalize_users.py",
        # Scripts de mantenimiento en tools
        "tools/maintenance/09_backup_restore_total.py",
        "tools/maintenance/08_backup_colecciones.py",
        "tools/maintenance/10_backup_incremental.py",
        "tools/maintenance/03_validar_integridad.py",
        "tools/maintenance/04_limpieza_automatizada.py",
        "tools/maintenance/05_reasignar_owners_huerfanos.py",
        "tools/maintenance/06_eliminar_duplicados_users.py",
        "tools/maintenance/07_eliminar_huerfanos.py",
        "tools/maintenance/advanced_monitor.py",
        "tools/maintenance/check_logs.py",
        "tools/maintenance/clean_images_scheduled.py",
        "tools/maintenance/diagnose_scripts.py",
        "tools/maintenance/monitor_mongodb.py",
        # Scripts de utilidades
        "tools/utils/fix_script_paths.py",
        "tools/utils/google_drive_utils.py",
        "tools/utils/insertar_cabecera.py",
        "tools/utils/organize_root_directory.py",
        "tools/utils/plantilla_cabecera_script.py",
        "tools/utils/iniciar_app_directo.sh",
        "tools/utils/iniciar_app_local.sh",
        "tools/utils/iniciar_produccion.sh",
        # Scripts de AWS y DB
        "tools/aws_utils/diagnose_s3_permissions.py",
        "tools/db_utils/google_drive_utils.py",
        "tools/db_utils/google_drive_utils.py_back",
        "tools/db_utils/settings.yaml",
        "tools/db_utils/setup_google_drive.py",
        # Scripts de diagnóstico
        "tools/diagnostico/diagnose_scripts.py",
        "tools/diagnostico/test_script_execution.py",
        # Scripts de producción
        "tools/producción/restart_server.sh",
        "tools/producción/start_app.sh",
        "tools/producción/start_gunicorn.sh",
        "tools/producción/supervise_gunicorn.sh",
        "tools/producción/supervise_gunicorn_web.sh",
        "tools/producción/update.sh",
        # Scripts de Admin Utils
        "tools/Admin Utils/fix_script_permissions.sh",
        "tools/Admin Utils/normalize_users.py",
        # Scripts de Db Utils
        "tools/Db Utils/03_validar_integridad.py",
        "tools/Db Utils/08_backup_colecciones.py",
        "tools/Db Utils/google_drive_utils.py",
        "tools/Db Utils/google_drive_utils.py_back",
        "tools/Db Utils/settings.yaml",
        "tools/Db Utils/setup_google_drive.py",
        # Scripts de tests
        "tests/conftest.py",
        "tests/check_test_user.py",
        "tests/check_test_user_ssl_fix.py",
        "tests/create_test_user.py",
        "tests/test_pagination.py",
        "tests/app/routes/test_admin_routes_func.py",
        "tests/app/routes/test_auth_routes_func.py",
        "tests/app/routes/test_auth_user_flow_func.py",
        "tests/app/routes/test_catalogs_crud_func.py",
        "tests/app/routes/test_catalogs_routes_func.py",
        "tests/app/routes/test_emergency_routes_func.py",
        "tests/app/routes/test_errors_routes_func.py",
        "tests/app/routes/test_flash_func.py",
        "tests/app/routes/test_image_routes_func.py",
        "tests/app/routes/test_main_routes_func.py",
        "tests/app/routes/test_session_routes.py",
        "tests/app/routes/test_session_routes_test.py",
        "tests/app/routes/test_usuarios_routes_func.py",
        "tests/integration/test_admin_api.py",
        "tests/integration/test_admin_dashboard.py",
        "tests/integration/test_admin_panel.py",
        "tests/integration/test_admin_panel_actions.py",
        "tests/integration/test_admin_panel_actions_full.py",
        "tests/integration/test_app_integration.py",
        "tests/integration/test_auth.py",
        "tests/integration/test_auth_20250515_124406.py",
        "tests/integration/test_auth_routes.py",
        "tests/integration/test_blueprints_smoke.py",
        "tests/integration/test_catalogs_crud.py",
        "tests/integration/test_catalogs_routes.py",
        "tests/integration/test_catalogs_rows.py",
        "tests/integration/test_gdrive.py",
        "tests/integration/test_gdrive_upload.py",
        "tests/integration/test_gdrive_v2.py",
        "tests/integration/test_login_direct.py",
        "tests/integration/test_login_produccion.py",
        "tests/integration/test_main_routes.py",
        "tests/integration/test_maintenance_dashboard.py",
        "tests/integration/test_mongo.py",
        "tests/integration/test_mongo_connection.py",
        "tests/integration/test_mongodb_integration.py",
        "tests/integration/test_s3_cors.py",
        "tests/integration/test_session_direct.py",
        "tests/integration/test_session_integration.py",
        "tests/integration/test_session_simple.py",
        "tests/integration/test_upload_simple.py",
        "tests/legacy/debug_rutas_catalogs.py",
        "tests/legacy/diagnostico_acceso.py",
        "tests/legacy/diagnostico_catalogs.py",
        "tests/legacy/diagnostico_completo.py",
        "tests/legacy/diagnostico_sesion.py",
        "tests/legacy/diagnostico_sesion_completo.py",
        "tests/legacy/listar_rutas.py",
        # Scripts adicionales
        "scripts/migrate_maintenance_routes.py",
        "scripts/capturar-chat.sh",
        "tools/add_words_to_config.py",
        "tools/fix_script_paths.py",
        "tools/git_commit_reorganization.sh",
        "tools/organize_root_scripts.py",
        "tools/test_script_execution.py",
        "tools/tools/test_script.sh",
    ]

    restored_files = []
    failed_files = []

    print("🔄 Restaurando archivos dañados desde Git...")
    print("=" * 60)

    for file_path in critical_files:
        source_path = root_dir / file_path

        if source_path.exists():
            try:
                # Restaurar desde Git
                os.system(f"git restore '{file_path}'")

                # Verificar que el archivo se restauró correctamente
                if (
                    source_path.exists() and source_path.stat().st_size > 100
                ):  # Más de 100 bytes
                    restored_files.append(file_path)
                    print(f"  ✅ Restaurado: {file_path}")
                else:
                    failed_files.append(file_path)
                    print(f"  ❌ Falló restauración: {file_path}")
            except Exception as e:
                failed_files.append(file_path)
                print(f"  ❌ Error restaurando {file_path}: {e}")
        else:
            print(f"  ⚠️  Archivo no existe en Git: {file_path}")

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
    restore_damaged_files()
