# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Información del Proyecto

**EDF Catálogo Tablas** es una aplicación web Flask para gestión de catálogos y tablas con integración AWS S3, desarrollada en español de España. La aplicación incluye autenticación, gestión de usuarios, subida de imágenes y herramientas administrativas.

## Estructura de Alto Nivel

Esta es una aplicación Flask modular con:

- **Backend**: Flask + MongoDB (base de datos `app_catalogojoyero`)
- **Almacenamiento**: AWS S3 para archivos + almacenamiento local como fallback
- **Arquitectura**: Factory pattern con blueprints modulares
- **Despliegue**: Soporte para aplicaciones nativas (PyInstaller) y web

### Directorios Principales

- `app/` - Aplicación Flask principal con factory pattern
- `tools/` - Herramientas de utilidad y scripts de mantenimiento
- `app/routes/` - Blueprints modulares para diferentes funcionalidades
- `tools/local/aws_utils/` - Utilidades específicas para AWS S3

## Comandos de Desarrollo

### Ejecutar la Aplicación

```bash
# Aplicación principal Flask
python3 run_server.py

# O usando wsgi directamente
python3 wsgi.py

# Script de lanzamiento shell
./run_app.sh
```

### AWS S3 Utilidades

```bash
# Acceso rápido al menú interactivo de AWS S3
python3 aws_s3_utils.py

# Acceso directo al menú
python3 tools/local/aws_utils/aws_s3_menu.py

# Scripts individuales
python3 tools/local/aws_utils/configure_s3_access.py
python3 tools/local/aws_utils/diagnose_s3_permissions.py
python3 tools/local/aws_utils/migrate_images_to_s3.py
python3 tools/local/aws_utils/monitor_s3.py
```

### Testing

```bash
# Ejecutar tests
pytest

# Tests específicos de perfil de imágenes
pytest tests/test_profile_images.py

# Testing manual exhaustivo
python3 tools/testing/testing_manual_exhaustivo.py

# Tests comprensivos
python3 tools/testing/run_comprehensive_tests.py
```

### Linting y Código

```bash
# Pylint
pylint app/

# Verificación de archivos críticos
./verify_build_files.sh

# Verificación de conectividad
./verify_connectivity.sh

# Verificación de requirements
./verify_requirements.sh
```

### Build y Distribución

```bash
# Build de aplicación nativa
./build_native_app.sh

# Build para macOS
./build_macos_app.sh

# Build de todas las versiones
./build_all_versions.sh

# Crear DMG para macOS
./create_dmg.sh

# Limpiar builds
./clean_build.sh
```

### Verificación y Mantenimiento

```bash
# Push seguro con verificaciones
./safe_push.sh

# Verificar entorno de build
./verify_build_environment.sh

# Verificar spec de PyInstaller
./verify_spec.sh

# Pre-build cleanup
./pre_build_cleanup.sh
```

## Arquitectura y Patrones

### Factory Pattern

La aplicación usa el factory pattern en `app/__init__.py`:

```python
def create_app(testing=False):
    app = Flask(__name__)
    # Configuración y inicialización
    return app
```

### Blueprints Modulares

Los blueprints están organizados por funcionalidad:

- `main_bp` - Rutas principales
- `auth_bp` - Autenticación y login
- `catalogs_bp` - Gestión de catálogos (/catalogs)
- `admin_bp` - Panel de administración (/admin)
- `usuarios_bp` - Gestión de usuarios (/usuarios)
- `images_bp` - Gestión de imágenes (/images)
- `api_bp` - API endpoints
- `emergency_bp` - Acceso de emergencia

### Base de Datos

- **MongoDB**: Base de datos principal `app_catalogojoyero`
- **Colecciones**: users, catalogos, audit_logs, login_attempts, reset_tokens
- **Conexión**: Manejo resiliente con reintentos automáticos en `app/database.py`

### Almacenamiento de Archivos

Sistema híbrido AWS S3 + Local:
- S3 como almacenamiento principal (configurable con `USE_S3=true`)
- Fallback automático a almacenamiento local
- Migración automatizada entre sistemas

### Configuración

- **Configuración unificada**: `config.py` con clases para desarrollo/producción
- **Variables de entorno**: Cargadas desde `.env`
- **Optimizaciones**: Configuración específica para reducir consumo de recursos

## Variables de Entorno Críticas

```bash
# MongoDB
MONGO_URI=mongodb://...

# AWS S3
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_REGION=...
S3_BUCKET_NAME=...
USE_S3=true

# Flask
SECRET_KEY=...
FLASK_ENV=development|production

# Directorios
UPLOAD_FOLDER=...
LOG_DIR=...
```

## Sistema de Logging

- **Logging unificado**: `app/logging_unified.py`
- **Rotación automática**: 5MB por archivo, 5 backups
- **Niveles**: INFO para producción, DEBUG para desarrollo
- **Ubicación**: Directorio `logs/` o según `LOG_DIR`

## Herramientas Especiales

### AWS S3 Menu Interactivo

Proporciona acceso centralizado a:
- Configuración de S3
- Diagnóstico de permisos
- Migración de imágenes
- Monitoreo de uso y costos
- Generación de reportes

### Sistema de Verificaciones Pre-Push

Hooks automáticos que verifican:
- Archivos críticos para build
- Sintaxis de Python
- Conectividad de servicios
- Detección de archivos sensibles

### Build Tools

Soporte completo para:
- Aplicaciones nativas con PyInstaller
- Distribución macOS con DMG
- Manejo de conflictos de dependencias
- Verificación de entorno

## Patrones de Desarrollo

### Error Handling

- **Global**: Handlers en `app/error_handlers.py`
- **API**: Respuestas JSON automáticas para endpoints `/api/`
- **Web**: Templates personalizadas para errores HTTP

### Security Middleware

- **CSRF**: Configurable por blueprint
- **Rate Limiting**: Flask-Limiter integrado
- **Session Security**: Cookies seguras en producción
- **Audit Logging**: Registro de acciones administrativas

### Cache System

- **Redis**: Para sesiones y cache (opcional)
- **Filesystem**: Fallback para sesiones
- **S3 Cache**: Metadata de archivos cacheada

## Desarrollo Local

### Setup Inicial

1. Crear entorno virtual: `python3 -m venv .venv`
2. Activar: `source .venv/bin/activate`
3. Instalar dependencias: `pip install -r requirements.txt`
4. Configurar `.env` con variables necesarias
5. Ejecutar: `python3 run_server.py`

### Debugging

- **Flask Debug**: Activado automáticamente en desarrollo
- **Logging detallado**: En `logs/flask_debug.log`
- **Routes de debug**: `/test_session`, blueprints de testing
- **MongoDB Debug**: Conexión y queries loggeadas

### Testing de Funcionalidades

```bash
# Test de sesión
curl http://localhost:5001/test_session

# Test de conectividad S3
python3 tools/local/aws_utils/diagnose_s3_permissions.py

# Test de base de datos
python3 -c "from app.database import get_mongo_db; print(get_mongo_db())"
```

## Deployment en Producción

- **Servidor**: Configurado para `/edefrutos2025.xyz/httpdocs`
- **Process Manager**: Gunicorn con configuración optimizada
- **MongoDB**: Base de datos `app_catalogojoyero`
- **Archivos**: S3 primary, local fallback
- **SSL**: HTTPS enforced en producción

