# 📚 Catálogo de Scripts por Funcionalidades

## 📋 Descripción

Este documento cataloga todos los scripts del proyecto organizados por funcionalidades y ubicaciones.

## 🏗️ **Scripts de Configuración Principal (Raíz)**

### **Ubicación**: `/` (directorio raíz)

#### **config.py**
- **Función**: Configuración principal de la aplicación
- **Descripción**: Variables de entorno, configuración de base de datos, AWS, etc.
- **Estado**: ✅ **NECESARIO** - No mover

#### **launcher.py**
- **Función**: Punto de entrada principal de la aplicación macOS
- **Descripción**: Inicia Flask y PyWebView para la aplicación de escritorio
- **Estado**: ✅ **NECESARIO** - No mover

#### **main_app.py**
- **Función**: Aplicación Flask principal
- **Descripción**: Configuración de Flask, blueprints, extensiones
- **Estado**: ✅ **NECESARIO** - No mover

#### **wsgi.py**
- **Función**: Configuración WSGI para servidores web
- **Descripción**: Punto de entrada para servidores como Gunicorn
- **Estado**: ✅ **NECESARIO** - No mover

#### **passenger_wsgi.py**
- **Función**: Configuración WSGI para Passenger
- **Descripción**: Configuración específica para servidores Passenger
- **Estado**: ✅ **NECESARIO** - No mover

#### **gunicorn_config.py**
- **Función**: Configuración de Gunicorn
- **Descripción**: Configuración del servidor WSGI Gunicorn
- **Estado**: ✅ **NECESARIO** - No mover

#### **gunicorn.conf.py**
- **Función**: Configuración alternativa de Gunicorn
- **Descripción**: Archivo de configuración adicional para Gunicorn
- **Estado**: ✅ **NECESARIO** - No mover

## 🛠️ **Scripts de Utilidades (tools/utils/)**

### **Ubicación**: `tools/utils/`

#### **cleanup_cspell.py**
- **Función**: Limpieza de archivos de configuración cspell
- **Descripción**: Elimina archivos temporales de cspell
- **Categoría**: 🔧 **Mantenimiento**

#### **listar_catalogos.py**
- **Función**: Listar catálogos de la base de datos
- **Descripción**: Utilidad para mostrar catálogos existentes
- **Categoría**: 📊 **Base de Datos**

#### **md_to_pdf.py**
- **Función**: Convertir archivos Markdown a PDF
- **Descripción**: Utilidad de conversión de documentación
- **Categoría**: 📄 **Documentación**

#### **migrate_md_files.py**
- **Función**: Migrar archivos Markdown
- **Descripción**: Utilidad para reorganizar archivos MD
- **Categoría**: 📄 **Documentación**

#### **verificar_s3_completo.py**
- **Función**: Verificación completa de AWS S3
- **Descripción**: Diagnóstico de configuración y permisos de S3
- **Categoría**: ☁️ **AWS/S3**

#### **verify_testing_fix.py**
- **Función**: Verificar correcciones de testing
- **Descripción**: Validación de fixes en el sistema de testing
- **Categoría**: 🧪 **Testing**

#### **aws_s3_utils.py**
- **Función**: Utilidades para AWS S3
- **Descripción**: Funciones auxiliares para manejo de S3
- **Categoría**: ☁️ **AWS/S3**

#### **buscar_catalogo_ayer.py**
- **Función**: Buscar catálogos del día anterior
- **Descripción**: Utilidad de búsqueda temporal
- **Categoría**: 📊 **Base de Datos**

#### **buscar_catalogos_recientes.py**
- **Función**: Buscar catálogos recientes
- **Descripción**: Utilidad de búsqueda temporal
- **Categoría**: 📊 **Base de Datos**

#### **catalogo_tablas.py**
- **Función**: Gestión de catálogos de tablas
- **Descripción**: Utilidad para manejo de catálogos
- **Categoría**: 📊 **Base de Datos**

#### **catalogo_tablas_updated.py**
- **Función**: Gestión actualizada de catálogos
- **Descripción**: Versión actualizada de gestión de catálogos
- **Categoría**: 📊 **Base de Datos**

#### **check_session.py**
- **Función**: Verificar sesiones de usuario
- **Descripción**: Utilidad de diagnóstico de sesiones
- **Categoría**: 🔐 **Autenticación**

#### **check_user.py**
- **Función**: Verificar usuarios
- **Descripción**: Utilidad de gestión de usuarios
- **Categoría**: 👤 **Usuarios**

#### **check_user_local.py**
- **Función**: Verificar usuarios locales
- **Descripción**: Utilidad de gestión de usuarios locales
- **Categoría**: 👤 **Usuarios**

#### **descarga_msanual_de_google.py**
- **Función**: Descarga manual de Google Drive
- **Descripción**: Utilidad para descargas manuales
- **Categoría**: ☁️ **Google Drive**

#### **generate_final_summary.py**
- **Función**: Generar resumen final
- **Descripción**: Utilidad para generar reportes
- **Categoría**: 📊 **Reportes**

#### **gestionar_nuevos_scripts.py**
- **Función**: Gestionar nuevos scripts
- **Descripción**: Utilidad para organización de scripts
- **Categoría**: 🔧 **Mantenimiento**

#### **investigate_image_sync.py**
- **Función**: Investigar sincronización de imágenes
- **Descripción**: Utilidad de diagnóstico de imágenes
- **Categoría**: 🖼️ **Imágenes**

#### **list_all_users.py**
- **Función**: Listar todos los usuarios
- **Descripción**: Utilidad de gestión de usuarios
- **Categoría**: 👤 **Usuarios**

## 🧪 **Scripts de Testing (tools/Test Scripts/)**

### **Ubicación**: `tools/Test Scripts/`

#### **pruebas_rendimiento.py**
- **Función**: Pruebas de rendimiento
- **Descripción**: Tests de performance de la aplicación
- **Categoría**: ⚡ **Performance**

#### **test_script_execution.py**
- **Función**: Testing de ejecución de scripts
- **Descripción**: Validación de ejecución de scripts
- **Categoría**: 🧪 **Testing**

#### **test_simple.py**
- **Función**: Tests simples
- **Descripción**: Tests básicos de funcionalidad
- **Categoría**: 🧪 **Testing**

#### **test_drive_restore.py**
- **Función**: Testing de restauración de Google Drive
- **Descripción**: Validación de funcionalidad de backup
- **Categoría**: ☁️ **Google Drive**

#### **test_gdrive_endpoint.py**
- **Función**: Testing de endpoints de Google Drive
- **Descripción**: Validación de API de Google Drive
- **Categoría**: ☁️ **Google Drive**

#### **test_restore_endpoint.py**
- **Función**: Testing de endpoints de restauración
- **Descripción**: Validación de funcionalidad de restore
- **Categoría**: 🔄 **Backup/Restore**

#### **test_google_drive_console.js**
- **Función**: Testing de consola de Google Drive
- **Descripción**: Validación de interfaz de Google Drive
- **Categoría**: ☁️ **Google Drive**

#### **test_web_script_execution.py**
- **Función**: Testing de ejecución de scripts web
- **Descripción**: Validación de scripts web
- **Categoría**: 🌐 **Web**

#### **test_script_execution_fix.py**
- **Función**: Testing de corrección de ejecución
- **Descripción**: Validación de fixes de ejecución
- **Categoría**: 🧪 **Testing**

#### **test_authenticated_script_execution.py**
- **Función**: Testing de ejecución autenticada
- **Descripción**: Validación de scripts con autenticación
- **Categoría**: 🔐 **Autenticación**

#### **test_admin_access.py**
- **Función**: Testing de acceso de administrador
- **Descripción**: Validación de permisos de admin
- **Categoría**: 🔐 **Autenticación**

#### **test_user_admin.py**
- **Función**: Testing de administración de usuarios
- **Descripción**: Validación de gestión de usuarios
- **Categoría**: 👤 **Usuarios**

#### **test_markdown_detection.py**
- **Función**: Testing de detección de Markdown
- **Descripción**: Validación de procesamiento de MD
- **Categoría**: 📄 **Documentación**

#### **test_dashboard_complete.js**
- **Función**: Testing completo del dashboard
- **Descripción**: Validación de funcionalidad del dashboard
- **Categoría**: 📊 **Dashboard**

#### **test_dashboard_final.js**
- **Función**: Testing final del dashboard
- **Descripción**: Validación final del dashboard
- **Categoría**: 📊 **Dashboard**

#### **tests_blueprint.py**
- **Función**: Testing de blueprints
- **Descripción**: Validación de estructura de blueprints
- **Categoría**: 🧪 **Testing**

## 🔍 **Scripts de Diagnóstico (tools/diagnostico/)**

### **Ubicación**: `tools/diagnostico/`

#### **diagnose_production.py**
- **Función**: Diagnóstico de producción
- **Descripción**: Análisis del entorno de producción
- **Categoría**: 🔍 **Diagnóstico**

#### **diagnose_script_execution.py**
- **Función**: Diagnóstico de ejecución de scripts
- **Descripción**: Análisis de problemas de ejecución
- **Categoría**: 🔍 **Diagnóstico**

#### **diagnose_script_paths.py**
- **Función**: Diagnóstico de rutas de scripts
- **Descripción**: Análisis de rutas y permisos
- **Categoría**: 🔍 **Diagnóstico**

#### **test_mongo_connection.py**
- **Función**: Testing de conexión MongoDB
- **Descripción**: Validación de conectividad a MongoDB
- **Categoría**: 🗄️ **Base de Datos**

#### **test_mongo_ssl.py**
- **Función**: Testing de SSL en MongoDB
- **Descripción**: Validación de conexión SSL
- **Categoría**: 🗄️ **Base de Datos**

#### **verificar_configuracion.py**
- **Función**: Verificar configuración
- **Descripción**: Validación de archivos de configuración
- **Categoría**: ⚙️ **Configuración**

#### **verify_app_catalogojoyero.py**
- **Función**: Verificar aplicación de catálogo
- **Descripción**: Validación de funcionalidad principal
- **Categoría**: 🔍 **Diagnóstico**

#### **03_validar_integridad.py**
- **Función**: Validar integridad de datos
- **Descripción**: Verificación de consistencia de datos
- **Categoría**: 🔍 **Diagnóstico**

#### **04_depurar_huérfanos.py**
- **Función**: Depurar registros huérfanos
- **Descripción**: Limpieza de datos inconsistentes
- **Categoría**: 🧹 **Limpieza**

#### **04_limpieza_automatizada.py**
- **Función**: Limpieza automatizada
- **Descripción**: Proceso automático de limpieza
- **Categoría**: 🧹 **Limpieza**

#### **SCRIPT_LOCATIONS.md**
- **Función**: Documentación de ubicaciones
- **Descripción**: Guía de ubicaciones de scripts
- **Categoría**: 📚 **Documentación**

#### **check_python_intellicode.py**
- **Función**: Verificar IntelliCode de Python
- **Descripción**: Validación de configuración de IDE
- **Categoría**: 🔧 **Desarrollo**

#### **clear_python_cache.py**
- **Función**: Limpiar caché de Python
- **Descripción**: Limpieza de archivos temporales
- **Categoría**: 🧹 **Limpieza**

#### **debug_users.py**
- **Función**: Debug de usuarios
- **Descripción**: Diagnóstico de problemas de usuarios
- **Categoría**: 👤 **Usuarios**

#### **debug_password_verification.py**
- **Función**: Debug de verificación de contraseñas
- **Descripción**: Diagnóstico de autenticación
- **Categoría**: 🔐 **Autenticación**

#### **debug_catalog_error.py**
- **Función**: Debug de errores de catálogo
- **Descripción**: Diagnóstico de problemas de catálogos
- **Categoría**: 📊 **Base de Datos**

#### **debug_login_reset.py**
- **Función**: Debug de reset de login
- **Descripción**: Diagnóstico de problemas de login
- **Categoría**: 🔐 **Autenticación**

#### **diagnose_script_categories.py**
- **Función**: Diagnóstico de categorías de scripts
- **Descripción**: Análisis de organización de scripts
- **Categoría**: 🔍 **Diagnóstico**

#### **diagnosticar_imagenes_catalogo.py**
- **Función**: Diagnosticar imágenes de catálogo
- **Descripción**: Análisis de imágenes en catálogos
- **Categoría**: 🖼️ **Imágenes**

#### **diagnosticar_imagenes_simple.py**
- **Función**: Diagnosticar imágenes simples
- **Descripción**: Análisis básico de imágenes
- **Categoría**: 🖼️ **Imágenes**

#### **debug_backup_buttons.js**
- **Función**: Debug de botones de backup
- **Descripción**: Diagnóstico de interfaz de backup
- **Categoría**: 🔄 **Backup/Restore**

#### **debug_backup_dir.py**
- **Función**: Debug de directorio de backup
- **Descripción**: Diagnóstico de estructura de backups
- **Categoría**: 🔄 **Backup/Restore**

## 🔧 **Scripts de Mantenimiento (tools/maintenance/)**

### **Ubicación**: `tools/maintenance/`

#### **organize_files.sh**
- **Función**: Organizar archivos
- **Descripción**: Script de organización de archivos
- **Categoría**: 📁 **Organización**

#### **setup_cron_job.sh**
- **Función**: Configurar tareas cron
- **Descripción**: Automatización de tareas programadas
- **Categoría**: ⏰ **Automatización**

#### **setup_scheduled_tasks.sh**
- **Función**: Configurar tareas programadas
- **Descripción**: Configuración de tareas automáticas
- **Categoría**: ⏰ **Automatización**

#### **09_backup_restore_total.py**
- **Función**: Backup y restauración total
- **Descripción**: Proceso completo de backup/restore
- **Categoría**: 🔄 **Backup/Restore**

#### **10_backup_incremental.py**
- **Función**: Backup incremental
- **Descripción**: Proceso de backup incremental
- **Categoría**: 🔄 **Backup/Restore**

#### **cleanup_tools_directory.py**
- **Función**: Limpiar directorio de herramientas
- **Descripción**: Limpieza de archivos temporales
- **Categoría**: 🧹 **Limpieza**

#### **monitor_rendimiento.py**
- **Función**: Monitorear rendimiento
- **Descripción**: Supervisión de performance
- **Categoría**: 📊 **Monitoreo**

#### **fix_catalog_images.py**
- **Función**: Corregir imágenes de catálogo
- **Descripción**: Reparación de imágenes
- **Categoría**: 🖼️ **Imágenes**

#### **fix_macos_app_complete_02.py**
- **Función**: Corregir aplicación macOS
- **Descripción**: Reparación de app macOS
- **Categoría**: 🍎 **macOS**

#### **fix_mypy_config.py**
- **Función**: Corregir configuración de mypy
- **Descripción**: Reparación de configuración de type checking
- **Categoría**: 🔧 **Desarrollo**

#### **fix_port_configuration.py**
- **Función**: Corregir configuración de puertos
- **Descripción**: Reparación de configuración de red
- **Categoría**: 🌐 **Red**

#### **fix_profile_image.py**
- **Función**: Corregir imagen de perfil
- **Descripción**: Reparación de imágenes de usuario
- **Categoría**: 🖼️ **Imágenes**

#### **fix_python38_compatibility.py**
- **Función**: Corregir compatibilidad Python 3.8
- **Descripción**: Reparación de compatibilidad
- **Categoría**: 🐍 **Python**

#### **fix_remaining_imports.py**
- **Función**: Corregir imports restantes
- **Descripción**: Reparación de imports faltantes
- **Categoría**: 🔧 **Desarrollo**

#### **fix_s3_images.py**
- **Función**: Corregir imágenes en S3
- **Descripción**: Reparación de imágenes en AWS
- **Categoría**: ☁️ **AWS/S3**

#### **fix_script_execution.py**
- **Función**: Corregir ejecución de scripts
- **Descripción**: Reparación de problemas de ejecución
- **Categoría**: 🔧 **Desarrollo**

#### **fix_script_routes.py**
- **Función**: Corregir rutas de scripts
- **Descripción**: Reparación de rutas de API
- **Categoría**: 🌐 **API**

#### **fix_supervision_script.py**
- **Función**: Corregir script de supervisión
- **Descripción**: Reparación de monitoreo
- **Categoría**: 📊 **Monitoreo**

#### **fix_testing_system.py**
- **Función**: Corregir sistema de testing
- **Descripción**: Reparación de tests
- **Categoría**: 🧪 **Testing**

#### **recover_image_catalog_relations.py**
- **Función**: Recuperar relaciones de imágenes
- **Descripción**: Restauración de relaciones de BD
- **Categoría**: 🗄️ **Base de Datos**

#### **restore_images_with_fallback.py**
- **Función**: Restaurar imágenes con fallback
- **Descripción**: Restauración robusta de imágenes
- **Categoría**: 🖼️ **Imágenes**

#### **reset_passwords_final.py**
- **Función**: Reset final de contraseñas
- **Descripción**: Restablecimiento masivo de contraseñas
- **Categoría**: 🔐 **Autenticación**

#### **reset_all_users_passwords.py**
- **Función**: Reset de todas las contraseñas
- **Descripción**: Restablecimiento completo de contraseñas
- **Categoría**: 🔐 **Autenticación**

#### **clean_cache.sh**
- **Función**: Limpiar caché
- **Descripción**: Limpieza de archivos temporales
- **Categoría**: 🧹 **Limpieza**

#### **clean_cache_logged.sh**
- **Función**: Limpiar caché con logging
- **Descripción**: Limpieza con registro de actividad
- **Categoría**: 🧹 **Limpieza**

#### **clean_cache_simple.sh**
- **Función**: Limpiar caché simple
- **Descripción**: Limpieza básica de archivos temporales
- **Categoría**: 🧹 **Limpieza**

## 🍎 **Scripts de macOS (tools/macOS/)**

### **Ubicación**: `tools/macOS/`

#### **build_macos_app.sh**
- **Función**: Construir aplicación macOS
- **Descripción**: Script de construcción de app macOS
- **Categoría**: 🍎 **macOS**

#### **crear_dmg_macos.sh**
- **Función**: Crear DMG para macOS
- **Descripción**: Generación de paquete de distribución
- **Categoría**: 🍎 **macOS**

#### **instalador_automatico.sh**
- **Función**: Instalador automático
- **Descripción**: Script de instalación automática
- **Categoría**: 🍎 **macOS**

#### **verificacion_final_macos.py**
- **Función**: Verificación final de macOS
- **Descripción**: Validación completa de app macOS
- **Categoría**: 🍎 **macOS**

#### **diagnostico_app_macos.py**
- **Función**: Diagnóstico de app macOS
- **Descripción**: Análisis de problemas de app macOS
- **Categoría**: 🍎 **macOS**

#### **test_macos_app.py**
- **Función**: Testing de app macOS
- **Descripción**: Validación de funcionalidad de app macOS
- **Categoría**: 🍎 **macOS**

#### **configuracion_tamaño_ventana.py**
- **Función**: Configurar tamaño de ventana
- **Descripción**: Ajuste de dimensiones de ventana
- **Categoría**: 🍎 **macOS**

#### **configurador_ventana_pywebview.py**
- **Función**: Configurar ventana PyWebView
- **Descripción**: Configuración de interfaz de ventana
- **Categoría**: 🍎 **macOS**

## 🚀 **Scripts de Ejecución (tools/execution/)**

### **Ubicación**: `tools/execution/`

#### **logcmd.sh**
- **Función**: Comando de logging
- **Descripción**: Script para logging de comandos
- **Categoría**: 📝 **Logging**

#### **logcmdpy.sh**
- **Función**: Comando de logging Python
- **Descripción**: Script para logging de Python
- **Categoría**: 📝 **Logging**

#### **run_app_service.sh**
- **Función**: Ejecutar app como servicio
- **Descripción**: Script para ejecutar como servicio
- **Categoría**: 🚀 **Ejecución**

#### **run_app_with_log.sh**
- **Función**: Ejecutar app con logs
- **Descripción**: Script con logging detallado
- **Categoría**: 🚀 **Ejecución**

#### **run_app.sh**
- **Función**: Ejecutar app
- **Descripción**: Script básico de ejecución
- **Categoría**: 🚀 **Ejecución**

## 📊 **Resumen por Categorías**

### **🔧 Mantenimiento**: 25 scripts
### **🔍 Diagnóstico**: 15 scripts
### **🧪 Testing**: 15 scripts
### **🛠️ Utilidades**: 20 scripts
### **🍎 macOS**: 8 scripts
### **🚀 Ejecución**: 5 scripts
### **⚙️ Configuración**: 7 scripts (raíz)

## 📈 **Estadísticas Totales**

- **Total de Scripts**: 95
- **Scripts Migrados**: 88
- **Scripts en Raíz**: 7 (necesarios)
- **Directorios Creados**: 2 nuevos

---

**© 2025 EDFrutos. Catálogo de Scripts organizado por funcionalidades.**
