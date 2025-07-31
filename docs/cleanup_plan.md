# Plan de Limpieza y Reorganización del Proyecto

## 1. Archivos a Eliminar (Temporales/Duplicados)

### Scripts de acceso temporal y pruebas
- acceder.py
- acceso_admin_directo.py
- acceso_admin_fix.py
- acceso_admin.php
- acceso_directo_admin.py
- acceso_directo_catalogs.py
- acceso_directo_catalogs_session.py
- acceso_directo_catalogs_sin_password.py
- acceso_directo_completo.py
- acceso_directo.html
- acceso_directo_html.py
- acceso_directo.py
- acceso_directo_simple.py
- acceso_directo_usuario.py
- acceso_emergencia.html
- admin_direct.html
- admin_direct.php
- admin-emergency.html
- admin.html
- bypass_login.html
- emergency_login.php
- panel_emergencia.php

### Archivos de corrección temporal
- corregir_acceso_catalogs.py
- corregir_apache.py
- corregir_cambio_password.py
- corregir_enlaces.py
- corregir_final_catalogs.py
- corregir_funcionalidad.py
- corregir_permisos_catalogs_simple.py
- corregir_servicio.py
- corregir_usuario_normal.py
- fix_503_error.py
- fix_access_absolute.py
- fix_access.py
- fix_admin_password.py
- fix_auth_final.py
- fix_aws_credentials.py
- fix_catalogs_session.py
- fix_cleanup_tables.py
- fix_mongo_connection.py
- fix_passwords.py
- fix_prod_access.py
- fix_roles.py
- final_fix_passwords.py
- html2pdf770086-0.html

### Archivos de solución temporal
- solucion_acceso.py
- solucionar_acceso_completo.py
- solucionar_acceso_directo_catalogs.py
- solucionar_acceso.py
- solucionar_catalogs_completo.py
- solucionar_permisos_catalogs.py
- solucion_completa_acceso.py
- solucion_definitiva.py
- solucion_errores_rutas.py
- solucion_final_acceso.py
- solucion_final_catalogs.py
- solucion_usuarios_normales.py
- universal_solution.py

### Archivos de verificación temporal
- verificar_acceso_catalogs.py
- verificar_acceso_completo.py
- verificar_acceso_final.py
- verificar_configuracion.py
- verificar_final_catalogs.py

## 2. Archivos a Mover a /scripts/password_utils
- reset_admin_completo.py
- reset_admin_password.py
- reset_admin.py
- reset_password_bcrypt.py
- reset_password_edefrutos.py
- reset_passwords.py
- update_password.py
- update_passwords.py
- migrate_passwords.py
- unlock_user.py
- desbloquear_usuario.py

## 3. Archivos a Mover a /scripts/db_utils
- check_catalog.py
- check_collections.py
- check_db.py
- conexion_MongoDB.py
- init_db.py
- list_users.py
- migracion_catalogos.py
- migrate_tables.py
- playground-1.mongodb.js

## 4. Archivos a Mover a /scripts/aws_utils
- configure_s3_access.py
- list_buckets.py
- migrate_images_to_s3.py

## 5. Archivos a Mover a /scripts/maintenance
- daily_report.sh
- maintenance.sh
- manage_app.sh
- monitor_socket.sh
- run_gunicorn.sh
- start_app.sh
- start_gunicorn.sh
- supervise_gunicorn.sh
- update.sh
- iniciar_app_directo.sh
- iniciar_app_local.sh
- iniciar_produccion.sh

## 6. Archivos a Mover a /tests/legacy
- test.xlsx
- diagnostico_acceso.py
- diagnostico_catalogs.py
- diagnostico_completo.py
- diagnostico_completo_resultados.json
- diagnostico_sesion_completo.py
- diagnostico_sesion.py
- listar_rutas.py
- debug_rutas_catalogs.py

## 7. Directorios Duplicados a Eliminar
- app/app_catalogo_completo_final (duplicado de la estructura principal)
- app/routes/app_catalogo_completo_final (duplicado de la estructura principal)

## 8. Archivos de Configuración a Mantener
- config.py
- gunicorn_config.py
- gunicorn.conf.py
- requirements.txt
- wsgi.py
- passenger_wsgi.py
- Procfile
- .env.example
- .gitignore
- run.py

## 9. Documentación a Mantener
- CHANGELOG.md
- LICENSE
- EXPERIENCIA_ROBUSTA.md
- robots.txt
