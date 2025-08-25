# 📋 DOSSIER ANÁLISIS DEPENDENCIAS - EDF CATÁLOGO TABLAS

**Fecha de análisis**: 25 de agosto, 2025  
**Versión del proyecto**: 1.0  
**Python objetivo**: 3.8-3.10  

---

## 🔍 RESUMEN EJECUTIVO

El proyecto tiene **dos archivos de requirements** que presentan inconsistencias y posibles problemas de compatibilidad. Se han detectado **dependencias faltantes críticas** y **versiones incompatibles** entre librerías.

### ⚠️ PROBLEMAS CRÍTICOS IDENTIFICADOS

1. **Duplicación de dotenv**: `dotenv==0.9.9` y `python-dotenv==1.0.1`
2. **Versiones desactualizadas de seguridad**: `urllib3==2.0.7` (vulnerabilidad conocida)
3. **Dependencias de desarrollo en producción**: PyQt6, py2app (innecesarias para servidor)
4. **Falta Flask-CSRF**: Critical para seguridad
5. **Incompatibilidades PyInstaller**: Versiones de dependencias incompatibles

---

## 📦 DEPENDENCIAS CRÍTICAS FALTANTES

### 🚨 SEGURIDAD
- **Flask-CSRF**: No está presente, pero el código usa `WTF_CSRF_ENABLED`
- **Flask-Talisman**: Para headers de seguridad HTTPS
- **cryptography**: Versión correcta pero falta `pyotp` para 2FA

### 🌐 WEB FRAMEWORK
- **Flask-Compress**: Referenciado en config.py pero no en requirements
- **Flask-Caching**: Para sistema de cache mencionado
- **Gunicorn[gevent]**: Para concurrencia mejorada

### 🗄️ BASE DE DATOS
- **pymongo[srv]**: Para conexiones MongoDB Atlas
- **motor**: Para operaciones asíncronas MongoDB (si se necesita)

---

## ⚡ INCOMPATIBILIDADES DETECTADAS

### 🔴 CRÍTICAS

1. **dotenv conflicto**:
   ```
   dotenv==0.9.9              # ❌ Obsoleta
   python-dotenv==1.0.1       # ✅ Correcta
   ```
   **Solución**: Eliminar `dotenv==0.9.9`

2. **urllib3 vulnerabilidad**:
   ```
   urllib3==2.0.7             # ❌ CVE-2024-37891
   ```
   **Solución**: Actualizar a `urllib3>=2.2.2`

3. **Flask-Session filesystem**:
   ```python
   # En extensions.py línea 33
   app.config["SESSION_TYPE"] = "filesystem"
   ```
   **Problema**: Incompatible con PyInstaller empaquetado

### 🟡 MODERADAS

1. **Pillow versión**:
   ```
   Pillow==10.4.0             # Compatible pero no latest
   ```
   **Recomendación**: Actualizar a `Pillow>=10.4.0,<11.0.0`

2. **pytest outdated**:
   ```
   pytest==8.2.0              # Versión de abril 2024
   ```
   **Recomendación**: Actualizar a `pytest>=8.3.0`

---

## 🏗️ DEPENDENCIAS INNECESARIAS

### 📱 APLICACIONES NATIVAS (Eliminar para servidor web)
```
PyQt6==6.9.1                  # ❌ Solo para GUI nativa
PyQt6-Qt6==6.9.1              # ❌ Solo para GUI nativa  
PyQt6_sip==13.10.2            # ❌ Solo para GUI nativa
py2app==0.28.8                # ❌ Solo para macOS packaging
pyobjc-*                       # ❌ Solo para macOS nativo
pywebview==5.4                 # ❌ Solo para aplicación híbrida
```

### 🧪 DESARROLLO/TESTING (Mover a requirements-dev.txt)
```
black==24.8.0                 # Formateo código
isort==6.0.1                  # Ordenar imports
pylint==3.3.7                 # Linting
pylint-pytest==1.1.8         # Plugin pytest
pytest==8.2.0                # Testing framework
pytest-html==4.1.1           # Reportes HTML
debugpy==1.8.13              # Debug remoto
```

### 🔄 DUPLICADAS/REDUNDANTES
```
bottle==0.13.4                # ❌ No se usa (Flask project)
fastapi==0.116.1              # ❌ No se usa (Flask project)
starlette==0.47.1             # ❌ Dependencia de FastAPI
uvicorn==0.34.3               # ❌ Servidor ASGI innecesario
SQLAlchemy==2.0.41            # ❌ No se usa (proyecto MongoDB)
```

---

## 🚀 OPTIMIZACIONES RECOMENDADAS

### 1. **Separar Requirements**

**requirements-production.txt**:
```
# Core Flask
Flask==3.1.1
Flask-Login==0.6.3
Flask-Session==0.8.0
Flask-WTF==1.2.2
Flask-Mail==0.9.1
Flask-PyMongo==2.3.0
Flask-Limiter==3.12
Flask-CSRF>=1.0.0
Flask-Compress>=1.13

# Database
pymongo[srv]==4.10.1
dnspython==2.6.1

# Security
cryptography>=43.0.3
bcrypt==4.1.2
pyotp==2.9.0

# AWS
boto3==1.34.34
botocore==1.34.34

# Production Server
gunicorn[gevent]>=23.0.0

# Environment
python-dotenv==1.0.1

# Utils
requests>=2.32.4
urllib3>=2.2.2
Pillow>=10.4.0,<11.0.0
```

**requirements-dev.txt**:
```
-r requirements-production.txt

# Development Tools
black>=24.8.0
isort>=6.0.1
pylint>=3.3.7
mypy>=1.11.0

# Testing
pytest>=8.3.0
pytest-html>=4.1.1
pytest-cov>=5.0.0
coverage>=7.6.0

# Debug
debugpy>=1.8.13
```

### 2. **Versiones Específicas Críticas**

```bash
# Corregir vulnerabilidades
pip install urllib3>=2.2.2

# Corregir conflictos dotenv
pip uninstall dotenv
pip install python-dotenv>=1.0.1

# Añadir seguridad faltante
pip install Flask-CSRF>=1.0.0
pip install Flask-Talisman>=1.1.0
```

---

## 🐍 COMPATIBILIDAD PYTHON

### ✅ COMPATIBLE (Python 3.8-3.10)
- Flask 3.1.1: ✅
- pymongo 4.10.1: ✅  
- boto3 1.34.34: ✅
- Most dependencies: ✅

### ⚠️ VERIFICAR
```
google-genai==1.26.0           # Requiere Python >=3.9
msgspec==0.18.6                # Mejor rendimiento Python >=3.9
```

### 🚫 PROBLEMAS PYTHON 3.8
```
pandas==2.0.3                  # Último soporte Python 3.8
numpy==1.24.4                  # Último soporte Python 3.8
```

---

## 🔧 COMANDOS DE REPARACIÓN

### 1. **Limpieza Inmediata**
```bash
# Eliminar conflictos
pip uninstall dotenv -y

# Corregir vulnerabilidades
pip install urllib3>=2.2.2

# Añadir dependencias críticas faltantes
pip install Flask-CSRF Flask-Compress Flask-Talisman
```

### 2. **Optimización Completa**
```bash
# Backup current environment
pip freeze > requirements-backup.txt

# Crear requirements limpio
pip-compile requirements-production.in

# Reinstalar entorno limpio
pip install -r requirements-production.txt
```

### 3. **Verificación Post-Instalación**
```bash
# Verificar dependencias
pip check

# Audit seguridad
pip-audit

# Test aplicación
python -m pytest tests/
```

---

## 📊 MÉTRICAS ACTUALES

| Categoría | Cantidad | Estado |
|-----------|----------|---------|
| **Total Dependencies** | 207 | 🔴 Excesivo |
| **Críticas Faltantes** | 3 | 🚨 Urgente |
| **Vulnerabilidades** | 1 | ⚠️ Media |
| **Incompatibilidades** | 3 | 🔴 Crítica |
| **Innecesarias** | 25+ | 🟡 Optimizable |

---

## 🎯 PLAN DE ACCIÓN RECOMENDADO

### **FASE 1 - CRÍTICO (1-2 días)**
1. ✅ Corregir conflicto dotenv
2. ✅ Actualizar urllib3 (vulnerabilidad)
3. ✅ Añadir Flask-CSRF

### **FASE 2 - IMPORTANTE (3-5 días)**
1. 🔄 Separar requirements prod/dev
2. 🗑️ Eliminar dependencias innecesarias
3. 📦 Optimizar para deployment

### **FASE 3 - OPTIMIZACIÓN (1 semana)**
1. 🧪 Implementar pip-tools
2. 📋 Crear requirements.in files
3. 🚀 Automatizar dependency updates

---

## ⚠️ ADVERTENCIAS IMPORTANTES

1. **NO actualizar** todas las dependencias de una vez
2. **HACER backup** del entorno actual antes de cambios
3. **PROBAR** exhaustivamente después de cada cambio
4. **DOCUMENTAR** cambios para rollback si es necesario

---

## 🔗 RECURSOS ADICIONALES

- [Flask Security Best Practices](https://flask.palletsprojects.com/en/3.0.x/security/)
- [Python Package Vulnerability Database](https://pypa.io/en/latest/data/)
- [Dependency Management with pip-tools](https://pip-tools.readthedocs.io/)

---

**📝 Nota**: Este análisis es válido para la fecha indicada. Las versiones de dependencias cambian frecuentemente, por lo que se recomienda revisar periódicamente.
