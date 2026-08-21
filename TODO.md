# TODO - EDF Catálogo de Tablas

## ✅ Completadas

### Funcionalidad de Miniatura de Catálogo
- **Estado**: Completada
- **Descripción**: Añadida funcionalidad completa para editar miniatura de catálogo con 3 opciones:
  - URL de imagen externa
  - Subida de archivo local
  - Selección automática de imágenes del catálogo
- **Archivos modificados**:
  - `app/templates/editar_catalogo.html` - Template principal con pestañas
  - `app/templates/admin/editar_catalogo.html` - Template de administrador con botón
  - `app/routes/catalogs_routes.py` - Lógica de backend para usuarios normales
  - `app/routes/admin_routes.py` - Lógica de backend para administradores
  - `app/utils/image_utils.py` - Función `upload_image_to_s3`

### Corrección de Errores en Miniatura
- **Estado**: Completada
- **Descripción**: Corregidos errores críticos en la funcionalidad de miniatura:
  - Error de ruta conflictiva en `/admin/catalogo/<catalog_id>/images`
  - Error de importación `url_for` no disponible
  - Error de indentación en el código de subida de archivos
- **Archivos modificados**:
  - `app/routes/admin_routes.py` - Corregida ruta y lógica de subida
  - `app/templates/admin/editar_catalogo.html` - Actualizada ruta en JavaScript

### Backup Completo del Proyecto
- **Estado**: Completada
- **Descripción**: Creado backup completo del proyecto en `.01_Proyecto_backup/`
- **Tamaño**: 680MB
- **Archivos creados**:
  - `.01_Proyecto_backup/` - Directorio de backup
  - `.01_Proyecto_backup/README_BACKUP.md` - Documentación del backup
  - `.gitignore` - Actualizado para excluir el directorio de backup

### Corrección de Vulnerabilidad de Seguridad
- **Estado**: Completada
- **Descripción**: Eliminado archivo sensible `server_logs.txt` del repositorio
- **Acciones realizadas**:
  - Eliminado del historial de Git usando BFG Repo-Cleaner
  - Añadido al .gitignore para prevenir futuras exposiciones
  - Forzado push al repositorio remoto
  - Creado archivo de alerta de seguridad
- **Archivos modificados**:
  - `.gitignore` - Añadidos filtros para archivos sensibles
  - `SECURITY_ALERT.md` - Documentación de la vulnerabilidad

### Corrección de Errores de Linting
- **Estado**: Completada
- **Descripción**: Corregidos errores críticos de linting en `admin_routes.py`:
  - Errores de acceso a objetos `None` (líneas 2442, 5635, 5636)
  - Error de tipo en `write()` con archivos temporales (línea 4147)
  - Error de subíndice en diccionarios (línea 2880)
  - Imports no utilizados y redefiniciones
  - **Correcciones automáticas con Ruff**: 54 errores corregidos automáticamente
  - **Correcciones manuales**: 2 errores restantes corregidos manualmente
- **Archivos modificados**:
  - `app/routes/admin_routes.py` - Corregidos errores de tipo y acceso
  - `pyrightconfig.json` - Configuración optimizada para Pyright
  - `pyproject.toml` - Configuración actualizada para Ruff v0.3+
  - `cspell.json` - Configuración para cSpell con palabras técnicas

### Corrección de Problema de Build en GitHub Actions
- **Estado**: Completada
- **Descripción**: Solucionado error "Could not open requirements file: requirements_python310.txt"
- **Problema**: El archivo `requirements_python310.txt` no existía en el repositorio
- **Solución**: 
  - Creado archivo `requirements_python310.txt` con todas las dependencias compatibles con Python 3.10
  - Mejorado workflow de GitHub Actions para mayor robustez
- **Archivos creados**:
  - `requirements_python310.txt` - Archivo de dependencias específico para Python 3.10 (283 líneas)
- **Workflow mejorado**: `.github/workflows/mac_build.yml` con verificaciones adicionales
- **Mejoras del workflow**:
  - Verificación de checkout del código
  - Verificación de existencia del archivo requirements
  - Mejores mensajes de log para debugging
  - Detección temprana de errores
- **Resultado**: El build de GitHub Actions debería funcionar correctamente ahora

### Migración/sincronización completa de producción
- **Estado**: Completada (2026-08-19/20)
- **Descripción**: Producción llevaba meses desactualizada (nunca recibió el refactor de
  `admin_routes.py` en 14 módulos ni ~38 commits de fixes posteriores). Convertida en clon git real
  y sincronizada con `origin/main`; Python actualizado de 3.8.10 a 3.10.13.

### Vulnerabilidad de seguridad — bypass de login de emergencia
- **Estado**: Completada (2026-08-19)
- **Descripción**: `app/routes/emergency_access.py` exponía `/admin_login_bypass` y
  `/user_login_bypass` sin autenticación, otorgando sesión de admin a cualquiera. Registro del
  blueprint deshabilitado (commit `b4a4a35`) y sincronizado el guard `is_development_mode()` que
  ya existía en producción pero no en el repo (commit `04ef9ba`). Sin evidencia de explotación en
  logs revisados desde sept. 2024. Contraseña de MongoDB Atlas rotada por precaución.

## 🔧 En Progreso

## 📋 Pendientes

### Quitar el log de arranque que imprime `MONGO_URI` con contraseña en texto plano
- **Estado**: Pendiente
- **Descripción**: `app/database.py` (o similar) imprime la URI completa de MongoDB, incluida la
  contraseña, en el log cada vez que arranca el servicio. La contraseña expuesta ya fue rotada, pero
  el `print` sigue en el código.

### Decidir el destino de `requirements.txt` en la raíz de `docker-python-patched`
- **Estado**: Pendiente
- **Descripción**: Ese archivo (distinto del `requirements.txt` de `edf-catalogo-tablas/`) parece ser
  para el empaquetado de la app nativa de macOS (incluye `pyinstaller`, `py2app`, `pyqt6`). No se ha
  decidido si conservarlo, limpiarlo o documentarlo mejor.

### Servicio de producción corre como `root`
- **Estado**: Pendiente (mejora de seguridad)
- **Descripción**: `catalogotablas.service` corre como usuario `root` en vez de `www-data` o un
  usuario dedicado. Preexistente, no se ha tocado.

### Divergencia entre `.env` de producción y `.env.example` del repo
- **Estado**: Pendiente
- **Descripción**: Hay variables opcionales en el `.env` real de producción que no están reflejadas
  en `.env.example`. No es crítico, pero conviene alinear.

## 🚨 Problemas Conocidos

## 📝 Notas de Desarrollo
