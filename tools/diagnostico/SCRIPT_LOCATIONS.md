# 📁 UBICACIONES DE SCRIPTS Y FUNCIONALIDAD DEL SISTEMA

## 🎯 **Resumen del Diagnóstico**

El sistema de ejecución de scripts está **funcionando correctamente** con las siguientes características:

- ✅ **473 scripts** encontrados en el proyecto
- ✅ **script_runner.py** principal ubicado en `/tools/script_runner.py`
- ✅ **scripts_routes.py** configurado correctamente en `/app/routes/scripts_routes.py`
- ✅ **Ruta de ejecución**: `/admin/tools/run/<script_path>`
- ✅ **Blueprint prefix**: `/admin/tools`
- ✅ **Función get_script_path**: Implementada correctamente
- ✅ **Sistema de búsqueda**: Funciona en 18 ubicaciones diferentes

---

## 📂 **Ubicaciones Principales de Scripts**

### 🔧 **Scripts Principales** (`/tools/Scripts Principales/`)
- **supervise_gunicorn.sh** - Supervisión de Gunicorn (requiere root)
- **supervise_gunicorn_web.sh** - Supervisión web de Gunicorn ✅
- **script_runner.py** - Ejecutor de scripts ✅
- **03_validar_integridad.py** - Validación de integridad de BD
- **04_limpieza_automatizada.py** - Limpieza automática
- **08_backup_colecciones.py** - Backup de colecciones
- **09_backup_restore_total.py** - Backup y restauración total
- **10_backup_incremental.py** - Backup incremental

### 🏭 **Scripts de Producción** (`/tools/producción/`)
- **supervise_gunicorn.sh** - Supervisión de Gunicorn
- **supervise_gunicorn_web.sh** - Supervisión web de Gunicorn ✅
- **start_app.sh** - Inicio de aplicación
- **start_gunicorn.sh** - Inicio de Gunicorn
- **restart_server.sh** - Reinicio del servidor

### 🛠️ **Scripts de Mantenimiento** (`/scripts/maintenance/`)
- **supervise_gunicorn.sh** - Supervisión de Gunicorn
- **supervise_gunicorn_web.sh** - Supervisión web de Gunicorn ✅
- **script_runner.py** - Ejecutor de scripts
- **clean_images.py** - Limpieza de imágenes
- **monitor_mongodb.py** - Monitoreo de MongoDB

### 🔍 **Scripts de Diagnóstico** (`/tools/diagnostico/`)
- **debug_users.py** - Diagnóstico de usuarios ✅
- **diagnose_script_execution.py** - Diagnóstico de ejecución ✅
- **test_script_execution.py** - Pruebas de ejecución
- **03_validar_integridad.py** - Validación de integridad

### 👥 **Scripts de Usuarios** (`/tools/Users Tools/`)
- **check_users.py** - Verificación de usuarios
- **debug_users.py** - Depuración de usuarios
- **check_user.py** - Verificación de usuario individual
- **migrate_users.py** - Migración de usuarios

### 🔐 **Scripts de Administración** (`/tools/Admin Utils/`)
- **show_admin_user.py** - Mostrar usuario admin
- **06_eliminar_duplicados_users.py** - Eliminar duplicados
- **normalize_users.py** - Normalización de usuarios

---

## 🚀 **Funcionalidad del Sistema**

### **1. Ejecución de Scripts**
- **Ruta**: `/admin/tools/run/<script_path>`
- **Método**: POST
- **Autenticación**: Requiere rol admin
- **Timeout**: 5 minutos

### **2. script_runner.py Principal**
- **Ubicación**: `/tools/script_runner.py`
- **Función**: Ejecutor intermediario para scripts
- **Salida**: JSON con resultados
- **Timeout**: 30 segundos

### **3. Búsqueda de Scripts**
El sistema busca scripts en múltiples ubicaciones:
1. `/tools/Scripts Principales/`

3. `/tools/maintenance/`
4. `/tools/producción/`
5. `/scripts/maintenance/`
6. `/tools/db_utils/`
7. `/tools/diagnostico/`
8. `/tools/system/`
9. `/tools/Users Tools/`
10. `/tools/Admin Utils/`
11. `/tools/utils/`
12. `/tools/monitoring/`
13. `/tools/aws_utils/`
14. `/tools/Test Scripts/`
15. `/tools/app/`
16. `/tools/src/`
17. `/tools/`
18. `/scripts/`

---

## ⚠️ **Scripts que Requieren Atención**

### **Scripts que Requieren Root**
- **supervise_gunicorn.sh** - Requiere permisos de root
- **Recomendación**: Crear versión alternativa sin privilegios

### **Scripts Funcionando Correctamente**
- **supervise_gunicorn_web.sh** ✅
- **debug_users.py** ✅
- **script_runner.py** ✅
- **test_script.sh** ✅

---

## 🔧 **Configuración del Sistema**

### **Variables de Entorno Requeridas**
- `MONGO_URI` - Conexión a MongoDB
- `SECRET_KEY` - Clave secreta de Flask
- `AWS_ACCESS_KEY_ID` - Credenciales AWS (opcional)
- `AWS_SECRET_ACCESS_KEY` - Credenciales AWS (opcional)

### **Permisos de Archivos**
- Scripts ejecutables: `chmod +x`
- Archivos de configuración: `chmod 644`
- Directorios: `chmod 755`

---

## 📊 **Estadísticas del Proyecto**

- **Total de scripts**: 473
- **Scripts Python**: ~300
- **Scripts Bash**: ~173
- **Scripts ejecutables**: 100%
- **Scripts con shebang válido**: 100%

---

## 🎯 **Recomendaciones**

1. ✅ **Mantener permisos de ejecución** en todos los scripts
2. ✅ **Evitar scripts que requieran root** para ejecución web
3. ✅ **Usar rutas relativas** dentro de scripts
4. ✅ **Verificar shebang** en todos los scripts
5. ✅ **Crear versiones alternativas** para scripts que requieren root
6. ✅ **Mantener documentación** actualizada

---

## 📝 **Notas del Diagnóstico**

- **Fecha**: 2025-08-07 10:26:55
- **Sistema**: macOS-15.6-arm64-arm-64bit
- **Python**: 3.10.1
- **Usuario**: edefrutos
- **Estado**: ✅ **SISTEMA FUNCIONANDO CORRECTAMENTE**

---

*Documento generado automáticamente por el script de diagnóstico* 