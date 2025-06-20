# Estructura de /tools

Este directorio agrupa todas las utilidades y scripts de administración, diagnóstico, mantenimiento y gestión de base de datos del proyecto.

## Subdirectorios

- `admin_utils/`: Gestión de usuarios y roles.
- `db_utils/`: Backups, restauración y limpieza de base de datos.
- `diagnostico/`: Diagnóstico y verificación de integridad.
- `maintenance/`: Mantenimiento, automatización y housekeeping.

Cada subdirectorio incluye un README con ejemplos y propósito.

<!-- TESTS-AUTO-START -->
| Ruta | Descripción |
|------|-------------|
| `conftest.py` | Script: conftest.py |
| `legacy copy/debug_rutas_catalogs.py` | !/usr/bin/env python3 |
| `legacy copy/diagnostico_acceso.py` | !/usr/bin/env python3 |
| `legacy copy/diagnostico_catalogs.py` | !/usr/bin/env python3 |
| `legacy copy/diagnostico_completo.py` | !/usr/bin/env python3 |
| `legacy copy/diagnostico_sesion.py` | !/usr/bin/env python3 |
| `legacy copy/diagnostico_sesion_completo.py` | !/usr/bin/env python3 |
| `legacy copy/listar_rutas.py` | !/usr/bin/env python3 |
| `app/routes/test_admin_routes_func.py` | Script: test_admin_routes_func.py |
| `app/routes/test_auth_routes_func.py` | Script: test_auth_routes_func.py |
| `app/routes/test_auth_user_flow_func.py` | Utilidad para generar email aleatorio |
| `app/routes/test_catalogs_crud_func.py` | Script: test_catalogs_crud_func.py |
| `app/routes/test_catalogs_routes_func.py` | Script: test_catalogs_routes_func.py |
| `app/routes/test_emergency_routes_func.py` | 1. Acceder a la ruta de bypass sin seguir redirecciones |
| `app/routes/test_errors_routes_func.py` | Debe devolver 404 y mostrar mensaje de error personalizado |
| `app/routes/test_flash_func.py` | Script: test_flash_func.py |
| `app/routes/test_image_routes_func.py` | Puede devolver 200 si existe, 404 si no, o 302 si redirige |
| `app/routes/test_main_routes_func.py` | Script: test_main_routes_func.py |
| `app/routes/test_session_routes.py` | app/routes/test_session.py |
| `app/routes/test_session_routes_test.py` | Archivo movido a tests/legacy/. Conservar solo si es necesario. |
| `app/routes/test_usuarios_routes_func.py` | Debe responder 200 y mostrar el formulario de registro |
| `integration/test_admin_api.py` | Utilidad para simular sesión admin (si no existe ya en los fixtures) |
| `integration/test_admin_dashboard.py` | Asume que hay un fixture 'client' y 'app' disponible (como en otros tests) |
| `integration/test_admin_panel.py` | --- Helpers --- |
| `integration/test_admin_panel_actions.py` | --- Fixtures --- |
| `integration/test_admin_panel_actions_full.py` | --- Fixtures --- |
| `integration/test_app_integration.py` | Script: test_app.py |
| `integration/test_auth.py` | !/usr/bin/env python3 |
| `integration/test_auth_20250515_124406.py` | Script: test_auth_20250515_124406.py |
| `integration/test_auth_routes.py` | Script: test_auth_routes.py |
| `integration/test_blueprints_smoke.py` | Blueprints principales y rutas mínimas a testear |
| `integration/test_catalogs_crud.py` | Script: test_catalogs_crud.py |
| `integration/test_catalogs_routes.py` | Script: test_catalogs_routes.py |
| `integration/test_catalogs_rows.py` | Script: test_catalogs_rows.py |
| `integration/test_gdrive.py` | !/usr/bin/env python3 |
| `integration/test_gdrive_upload.py` | !/usr/bin/env python3 |
| `integration/test_gdrive_v2.py` | !/usr/bin/env python3 |
| `integration/test_login_direct.py` | !/usr/bin/env python |
| `integration/test_login_produccion.py` | Configura aquí los datos de acceso |
| `integration/test_main_routes.py` | Script: test_main_routes.py |
| `integration/test_maintenance_dashboard.py` | Script: test_maintenance_dashboard.py |
| `integration/test_mongo.py` | Script: test_mongo.py |
| `integration/test_mongo_connection.py` | Script: test_mongo_connection.py |
| `integration/test_mongodb_integration.py` | Script: test_mongodb.py |
| `integration/test_plantilla_avanzada.py` | Crea un usuario de prueba en la colección users y lo elimina al final. |
| `integration/test_s3_cors.py` | !/usr/bin/env python3 |
| `integration/test_session_direct.py` | !/usr/bin/env python3 |
| `integration/test_session_integration.py` | Script: test_session.py |
| `integration/test_session_simple.py` | !/usr/bin/env python3 |
| `integration/test_template.py` | Test plantilla: verifica que el endpoint raíz responde y contiene texto esperado. |
| `integration/test_upload_simple.py` | !/usr/bin/env python3 |
| `legacy/debug_rutas_catalogs.py` | !/usr/bin/env python3 |
| `legacy/diagnostico_acceso.py` | !/usr/bin/env python3 |
| `legacy/diagnostico_catalogs.py` | !/usr/bin/env python3 |
| `legacy/diagnostico_completo.py` | !/usr/bin/env python3 |
| `legacy/diagnostico_sesion.py` | !/usr/bin/env python3 |
| `legacy/diagnostico_sesion_completo.py` | !/usr/bin/env python3 |
| `legacy/listar_rutas.py` | !/usr/bin/env python3 |
| `scripts/01_test_connection copy.py` | Script: 01_test_connection.py |
| `scripts/01_test_connection.py` | Script: 01_test_connection.py |
| `scripts/test copy.py` | Configuración de registro |
| `scripts/test.py` | Configuración de registro |
| `scripts/test_app_scripts copy.py` | Script: test_app.py |
| `scripts/test_app_scripts.py` | Script: test_app.py |
| `scripts/test_clean_old_logs_range copy.py` | Script: test_clean_old_logs_range.py |
| `scripts/test_clean_old_logs_range.py` | Script: test_clean_old_logs_range.py |
| `scripts/test_login copy.py` | Script: test_login.py |
| `scripts/test_login.py` | Script: test_login.py |
| `scripts/test_mongodb_scripts copy.py` | Script: test_mongodb.py |
| `scripts/test_mongodb_scripts.py` | Script: test_mongodb.py |
| `scripts/test_openpyxl copy.py` | Crear un nuevo libro de trabajo y una hoja |
| `scripts/test_openpyxl.py` | Crear un nuevo libro de trabajo y una hoja |
| `scripts/test_password copy.py` | Script: test_password.py |
| `scripts/test_password.py` | Script: test_password.py |
| `scripts/test_password_verify copy.py` | Script: test_password_verify.py |
| `scripts/test_password_verify.py` | Script: test_password_verify.py |
| `scripts/test_python copy.py` | !/usr/bin/env python |
| `scripts/test_python.py` | !/usr/bin/env python |
<!-- TESTS-AUTO-END -->
