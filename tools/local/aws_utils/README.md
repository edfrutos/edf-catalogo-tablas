# AWS Utils - Utilidades para AWS S3

Este directorio contiene scripts y utilidades para gestionar AWS S3 en el proyecto EDF Catálogo Tablas.

## 📁 Estructura del Directorio

```
tools/local/aws_utils/
├── README.md                           # Esta documentación
├── aws_s3_menu.py                     # ⭐ Menú interactivo (NUEVO)
├── configure_s3_access.py             # Configuración y validación de S3
├── diagnose_s3_permissions.py         # Diagnóstico de permisos y problemas
├── list_buckets.py                    # Lista buckets S3 disponibles
├── migrate_images_to_s3.py            # Migra imágenes locales a S3
├── monitor_s3.py                      # Monitoreo y métricas de S3
├── s3_utils.py                        # Módulo de utilidades S3 consolidado
├── s3_config.json                     # Configuración generada (se crea automáticamente)
├── s3_diagnostic_report.json          # Reporte de diagnóstico (se crea automáticamente)
└── s3_monitoring_report.json          # Reporte de monitoreo (se crea automáticamente)
```

## 🚀 Acceso Rápido - Menú Interactivo

Para acceder fácilmente a todos los scripts y documentación, ejecuta:

```bash
python3 tools/local/aws_utils/aws_s3_menu.py
```

Este menú te permitirá:
- 📖 Ver el README.md completo
- 🔧 Ejecutar cualquier script de configuración
- 🔍 Ejecutar scripts de diagnóstico
- 📦 Ejecutar scripts de migración
- 📊 Ejecutar scripts de monitoreo
- 📄 Ver reportes generados
- ❓ Obtener ayuda

## 🔧 Scripts Disponibles

### 0. **aws_s3_menu.py** ⭐ NUEVO
Menú interactivo para acceder a todos los scripts de AWS S3.

**Funcionalidades:**
- ✅ Menú interactivo con opciones numeradas
- ✅ Acceso al README.md
- ✅ Ejecución de scripts de configuración
- ✅ Ejecución de scripts de diagnóstico
- ✅ Ejecución de scripts de migración
- ✅ Ejecución de scripts de monitoreo
- ✅ Información de ayuda

**Uso:**
```bash
python3 tools/local/aws_utils/aws_s3_menu.py
```

### 1. **configure_s3_access.py**
Configura y valida el acceso a AWS S3.

**Funcionalidades:**
- ✅ Validación de credenciales AWS
- ✅ Verificación de permisos S3
- ✅ Configuración de bucket
- ✅ Test de conectividad
- ✅ Generación de archivo de configuración

**Uso:**
```bash
python3 tools/local/aws_utils/configure_s3_access.py
```

### 2. **diagnose_s3_permissions.py**
Diagnostica permisos y problemas de acceso a AWS S3.

**Funcionalidades:**
- ✅ Diagnóstico de credenciales AWS
- ✅ Verificación de permisos S3
- ✅ Test de conectividad
- ✅ Análisis de políticas de bucket
- ✅ Reporte detallado de problemas

**Uso:**
```bash
python3 tools/local/aws_utils/diagnose_s3_permissions.py
```

### 3. **list_buckets.py**
Lista todos los buckets S3 disponibles.

**Funcionalidades:**
- ✅ Lista buckets disponibles
- ✅ Muestra región de cada bucket
- ✅ Verifica permisos de acceso

**Uso:**
```bash
python3 tools/local/aws_utils/list_buckets.py
```

### 4. **migrate_images_to_s3.py**
Migra imágenes del sistema de archivos local a S3.

**Funcionalidades:**
- ✅ Conecta a MongoDB y recupera registros con imágenes
- ✅ Sube imágenes existentes a S3
- ✅ Actualiza registros en MongoDB con rutas S3
- ✅ Estadísticas de migración

**Uso:**
```bash
python3 tools/local/aws_utils/migrate_images_to_s3.py
```

### 5. **monitor_s3.py**
Monitorea el uso y estado de AWS S3.

**Funcionalidades:**
- ✅ Monitoreo de uso de bucket
- ✅ Métricas de almacenamiento
- ✅ Estimación de costos
- ✅ Alertas de uso excesivo
- ✅ Reporte de objetos antiguos

**Uso:**
```bash
python3 tools/local/aws_utils/monitor_s3.py
```

### 6. **s3_utils.py**
Módulo de utilidades S3 consolidado.

**Funcionalidades:**
- ✅ Subida de archivos a S3
- ✅ Descarga de archivos de S3
- ✅ Eliminación de archivos de S3
- ✅ Generación de URLs prefirmadas
- ✅ Listado de objetos en bucket
- ✅ Verificación de existencia de archivos
- ✅ Backup y restauración de archivos

**Uso como módulo:**
```python
from tools.local.aws_utils.s3_utils import S3Manager

# Crear instancia del gestor
s3_manager = S3Manager()

# Subir archivo
s3_url = s3_manager.upload_file("archivo.jpg")

# Obtener URL prefirmada
url = s3_manager.get_presigned_url("archivo.jpg")
```

## 🔑 Configuración Requerida

### Variables de Entorno

Configura las siguientes variables en tu archivo `.env`:

```bash
# Credenciales AWS
AWS_ACCESS_KEY_ID=tu_access_key
AWS_SECRET_ACCESS_KEY=tu_secret_key
AWS_REGION=tu_region

# Configuración S3
S3_BUCKET_NAME=tu_bucket_name
```

### Permisos IAM Requeridos

Tu usuario/rol IAM debe tener los siguientes permisos:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:ListAllMyBuckets",
                "s3:GetBucketLocation"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:PutObject",
                "s3:DeleteObject",
                "s3:ListBucket",
                "s3:GetBucketPolicy",
                "s3:PutBucketPolicy"
            ],
            "Resource": [
                "arn:aws:s3:::tu-bucket-name",
                "arn:aws:s3:::tu-bucket-name/*"
            ]
        }
    ]
}
```

## 🚀 Flujo de Trabajo Recomendado

### Opción 1: **Usando el Menú Interactivo** ⭐ RECOMENDADO
```bash
# Ejecutar el menú interactivo
python3 tools/local/aws_utils/aws_s3_menu.py

# Luego seguir las opciones numeradas:
# 1. Ver README.md (opcional)
# 2. Configurar S3
# 3. Diagnosticar permisos
# 4. Listar buckets
# 5. Migrar imágenes a S3
# 6. Monitorear S3
```

### Opción 2: **Ejecución Directa de Scripts**

#### 1. **Configuración Inicial**
```bash
# 1. Configurar credenciales AWS
python3 tools/local/aws_utils/configure_s3_access.py

# 2. Verificar permisos
python3 tools/local/aws_utils/diagnose_s3_permissions.py

# 3. Listar buckets disponibles
python3 tools/local/aws_utils/list_buckets.py
```

#### 2. **Migración de Datos**
```bash
# Migrar imágenes existentes a S3
python3 tools/local/aws_utils/migrate_images_to_s3.py
```

#### 3. **Monitoreo Continuo**
```bash
# Monitorear uso y costos
python3 tools/local/aws_utils/monitor_s3.py
```

## 📊 Reportes Generados

Los scripts generan automáticamente los siguientes reportes:

### **s3_config.json**
Configuración de S3 generada por `configure_s3_access.py`

### **s3_diagnostic_report.json**
Reporte de diagnóstico generado por `diagnose_s3_permissions.py`

### **s3_monitoring_report.json**
Reporte de monitoreo generado por `monitor_s3.py`

## 🔍 Solución de Problemas

### Error: "Credenciales AWS incompletas"
- Verifica que las variables de entorno estén configuradas
- Asegúrate de que el archivo `.env` esté en el directorio raíz del proyecto

### Error: "Acceso denegado"
- Verifica los permisos IAM de tu usuario/rol
- Ejecuta `diagnose_s3_permissions.py` para identificar problemas específicos

### Error: "Bucket no existe"
- Verifica el nombre del bucket en `S3_BUCKET_NAME`
- Usa `list_buckets.py` para ver buckets disponibles

### Error: "Conexión fallida"
- Verifica la región AWS configurada
- Asegúrate de tener conexión a internet
- Verifica que las credenciales sean válidas

## 💡 Mejores Prácticas

### Seguridad
- ✅ Usa roles IAM en lugar de usuarios cuando sea posible
- ✅ Implementa políticas de bucket restrictivas
- ✅ Rota las credenciales regularmente
- ✅ Usa URLs prefirmadas para acceso temporal

### Costos
- ✅ Monitorea el uso regularmente con `monitor_s3.py`
- ✅ Implementa lifecycle policies para objetos antiguos
- ✅ Comprime archivos grandes antes de subirlos
- ✅ Usa clases de almacenamiento apropiadas

### Rendimiento
- ✅ Usa multipart upload para archivos grandes
- ✅ Implementa caching cuando sea apropiado
- ✅ Usa CloudFront para distribución global
- ✅ Optimiza el tamaño de los objetos

## 📞 Soporte

Para problemas o preguntas sobre estos scripts:

1. Ejecuta `diagnose_s3_permissions.py` para identificar problemas
2. Revisa los logs y reportes generados
3. Verifica la documentación de AWS S3
4. Consulta con el equipo de desarrollo

---

**Autor:** EDF Developer  
**Versión:** 1.0  
**Fecha:** 2025-08-08
