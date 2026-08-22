# TODO - EDF Catálogo de Tablas

## ✅ Completadas

### Divergencia entre `.env` de producción y `.env.example` del repo
- **Estado**: Completada (2026-08-22)
- **Descripción**: Comparadas solo las claves (nunca los valores) entre el `.env` real de
  producción y `.env.example`. Única diferencia: `GOOGLE_EMAIL` y `GOOGLE_APP_PASSWORD`
  (contraseña de aplicación de Gmail, no la contraseña normal de la cuenta) presentes en
  producción y ausentes del ejemplo — no las referencia nada del código de este repo, las usa
  un script de backup/notificación externo. Añadidas a `.env.example` con comentario aclaratorio.

### Documentado el destino de `requirements.txt` en la raíz de `docker-python-patched`
- **Estado**: Completada (2026-08-22)
- **Descripción**: Ese archivo (y su hermano `requirements_macOS.txt`) no lo usa el build de
  Docker (`Dockerfile`/`docker-compose.yml` ya usan `edf-catalogo-tablas/requirements.txt`
  explícitamente, con comentario propio). Es el entorno de desarrollo/empaquetado de la app
  nativa de macOS (PyInstaller, py2app, PyQt6, pywebview), pero mezcla también un volcado
  amplio de paquetes sin curar para este proyecto (fastapi/uvicorn, stack google-cloud-*,
  opentelemetry, SQLAlchemy, duckduckgo_search...). Se decidió solo documentarlo (cabecera
  añadida en ambos archivos aclarando su propósito real y la mezcla sin curar) en vez de
  limpiarlo o borrarlo, para no arriesgar el entorno local de empaquetado nativo. Esos dos
  archivos viven en la raíz de `docker-python-patched/`, que no es un repo git propio — el
  cambio no se commitea aquí.

### Eliminación del usuario fantasma felipe@catalog.com
- **Estado**: Completada (2026-08-22)
- **Descripción**: `_id` corrupto (string literal `'ObjectId("6a3ab5000ed78be860000000")'`, no un
  ObjectId real), invisible para las rutas normales de admin. Verificado con
  `tools/diagnostics/diag_delete_ghost_felipe.py` (dry-run: 0 documentos asociados en
  `catalogs`/`spreadsheets`) y borrado en producción con `--apply` (`deleted_count=1`).

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

### Servicio de producción corre como `root` — RESUELTA
- **Estado**: Completada (2026-08-21)
- **Descripción**: `catalogotablas.service` corría como `root`. Migrado al usuario propio de la
  subscription de Plesk (`ede2020:psacln`), dueño real de `edf_catalogotablas/`. Script con
  check/fix-pyenv/apply/rollback en
  `scripts/production/maintenance/migrate_service_dedicated_user.sh` (commits `596aea9`, `8c67933`).
  - El `.venv` usa un Python compilado con `pyenv` bajo `/root/.pyenv/versions/3.10.13`,
    intransitable para un usuario no-root. Se abrió paso mínimo (travesía sin lectura en
    `/root`, `/root/.pyenv`, `/root/.pyenv/versions`; lectura+ejecución recursiva solo dentro de
    `.../3.10.13`) en vez de recompilar o mover el intérprete.
  - Al reiniciar con el nuevo usuario, el servicio empezó a crashear en bucle (`Restart=always`)
    con `PermissionError: [Errno 13] Permission denied: '/logs/app.log'`, causando un 502 en
    `catalogotablas.edefrutos2020.com` (el proxy nginx de Plesk está bien configurado — el
    problema era que el backend en `127.0.0.1:5100` no llegaba a levantar). Causa real: hay
    **dos** `create_app()` en el código — el que de verdad se usa es `app/__init__.py`
    (`wsgi.py` hace `from app import create_app`), no `app/factory.py`. Ese `create_app` carga
    `app.config.from_object("config.Config")`, es decir el `config.py` de la **raíz** del
    proyecto (no `app/config.py`), y su `ProductionConfig.LOG_DIR` defaulteaba a `os.getenv(
    "LOG_DIR", "/logs")` — como el `.env` real de producción no tenía ninguna línea `LOG_DIR`,
    caía siempre en `/logs` (raíz del filesystem), invisible mientras el servicio corría como
    root. Un primer intento de arreglarlo con `sed -i "s/^LOG_DIR=.../..."` no funcionó porque
    esa sustitución solo reemplaza una línea ya existente y no había ninguna que reemplazar — el
    servicio volvió a caer minutos después. Arreglado de verdad: (1) se añadió la línea
    `LOG_DIR=.../edf_catalogotablas/logs` al `.env` real (con `grep -q ... || echo ... >> .env`
    para que inserte si falta), y (2) se corrigió el default inseguro en `config.py` a
    `os.path.join(BaseConfig.BASE_DIR, "logs")` (mismo patrón que ya usaba `BaseConfig` y
    `DevelopmentConfig`) como defensa en profundidad. Añadida advertencia en `.env.example`.
  - Efecto colateral positivo: el backup de Plesk venía fallando con `Permission denied` en
    `flask_session/*` (ficheros creados por el servicio como `root:root`, ilegibles por el
    usuario de la subscription que usa Plesk para los backups). Debería quedar resuelto — falta
    confirmarlo en el próximo backup programado.
  - Queda un directorio `/logs` huérfano en la raíz del servidor (creado por el servicio cuando
    corría como root); limpieza opcional, no bloqueante.

### Print de `MONGO_URI` completo (con contraseña) en el arranque
- **Estado**: Completada (2026-08-22)
- **Descripción**: `app/__init__.py:357` hacía `print(f"MONGO_URI usado: {...}")` en cada
  `create_app()` (cada arranque de worker), yendo directo a stdout → journal de systemd, sin pasar
  por el filtro de redacción de `logging_filters.py` (ese filtro solo actúa sobre el módulo
  `logging`, no sobre `print()`). Eliminado el print (commit `5f20e62`). Desplegado en producción
  (commit `ccdbfba`, `git pull` + `systemctl restart catalogotablas`).

### Fuga de identificador de sesión en logs (`Set-Cookie` completo)
- **Estado**: Completada (2026-08-22)
- **Descripción**: `app/__init__.py` (`after_request` / `log_set_cookie`) logueaba el header
  `Set-Cookie` completo a nivel INFO en cada request — filtraba el identificador de sesión a
  `app.log`. Cambiado a loguear solo si se envió cookie, sin exponer su valor. De paso eliminado
  un `before_request` de depuración (`log_cookie`) que no hacía nada (`pass`).


### Vulnerabilidad de seguridad — bypass de login de emergencia
- **Estado**: Completada (2026-08-19)
- **Descripción**: `app/routes/emergency_access.py` exponía `/admin_login_bypass` y
  `/user_login_bypass` sin autenticación, otorgando sesión de admin a cualquiera. Registro del
  blueprint deshabilitado (commit `b4a4a35`) y sincronizado el guard `is_development_mode()` que
  ya existía en producción pero no en el repo (commit `04ef9ba`). Sin evidencia de explotación en
  logs revisados desde sept. 2024. Contraseña de MongoDB Atlas rotada por precaución.

## 🔧 En Progreso

## 📋 Pendientes

### Directorio `/logs` huérfano en la raíz del servidor
- **Estado**: Pendiente — requiere root
- **Descripción**: Sobrante de cuando `catalogotablas.service` corría como `root` (propiedad de
  `www-data` dentro de `/`, root:root). El usuario `ede2020` no tiene permiso para borrarlo sin
  sudo. Limpieza opcional, no bloqueante:
  ```bash
  sudo rm -rf /logs
  ```

### Confirmar el próximo backup programado de Plesk
- **Estado**: Pendiente de verificación
- **Descripción**: La migración de `catalogotablas.service` a `ede2020:psacln` debería haber
  resuelto el `Permission denied` que sufría el backup de Plesk en `flask_session/*` (archivos
  antes creados como `root:root`). Falta confirmarlo en el próximo backup programado.

## 🚨 Problemas Conocidos

## 📝 Notas de Desarrollo
