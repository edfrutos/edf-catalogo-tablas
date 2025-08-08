# EDF Catálogo Tablas

Sistema de gestión de catálogos y tablas con integración AWS S3.

## 🚀 Acceso Rápido

### AWS S3 Utils
Para acceder a todas las utilidades de AWS S3:

```bash
# Opción 1: Acceso directo desde raíz
python3 aws_s3_utils.py

# Opción 2: Acceso directo al menú
python3 tools/local/aws_utils/aws_s3_menu.py
```

### Aplicación Principal
```bash
# Ejecutar la aplicación Flask
python3 main_app.py

# O usar el script de lanzamiento
./run_app.sh
```

## 📁 Estructura del Proyecto

```
edf_catalogotablas/
├── app/                           # Aplicación Flask principal
├── tools/                         # Herramientas y utilidades
│   └── local/
│       └── aws_utils/            # ⭐ Utilidades AWS S3
│           ├── aws_s3_menu.py    # Menú interactivo
│           ├── README.md         # Documentación S3
│           ├── configure_s3_access.py
│           ├── diagnose_s3_permissions.py
│           ├── list_buckets.py
│           ├── migrate_images_to_s3.py
│           ├── monitor_s3.py
│           └── s3_utils.py
├── scripts/                       # Scripts de mantenimiento
├── tests/                         # Tests del proyecto
├── docs/                          # Documentación
├── aws_s3_utils.py               # ⭐ Acceso rápido a AWS S3
├── main_app.py                   # Aplicación principal
└── README.md                     # Este archivo
```

## 🔧 AWS S3 - Utilidades Disponibles

### Menú Interactivo
El menú te permite acceder a todas las funcionalidades de AWS S3:

- 📖 **Ver README.md** - Documentación completa
- 🔧 **Configurar S3** - Configuración inicial
- 🔍 **Diagnosticar permisos** - Verificación de acceso
- 📦 **Listar buckets** - Buckets disponibles
- 🔄 **Migrar imágenes** - Migración a S3
- 📊 **Monitorear S3** - Métricas y costos
- 📄 **Ver reportes** - Reportes generados
- ❓ **Ayuda** - Información de ayuda

### Scripts Individuales
También puedes ejecutar los scripts directamente:

```bash
# Configuración
python3 tools/local/aws_utils/configure_s3_access.py

# Diagnóstico
python3 tools/local/aws_utils/diagnose_s3_permissions.py

# Migración
python3 tools/local/aws_utils/migrate_images_to_s3.py

# Monitoreo
python3 tools/local/aws_utils/monitor_s3.py
```

## 🔑 Configuración AWS S3

### Variables de Entorno
Configura en tu archivo `.env`:

```bash
AWS_ACCESS_KEY_ID=tu_access_key
AWS_SECRET_ACCESS_KEY=tu_secret_key
AWS_REGION=tu_region
S3_BUCKET_NAME=tu_bucket_name
```

### Permisos IAM Requeridos
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:ListAllMyBuckets",
                "s3:GetObject",
                "s3:PutObject",
                "s3:DeleteObject",
                "s3:ListBucket"
            ],
            "Resource": "*"
        }
    ]
}
```

## 📊 Reportes Generados

Los scripts de AWS S3 generan automáticamente:

- `s3_config.json` - Configuración de S3
- `s3_diagnostic_report.json` - Reporte de diagnóstico
- `s3_monitoring_report.json` - Reporte de monitoreo

## 🚀 Flujo de Trabajo Recomendado

### 1. Configuración Inicial
```bash
python3 aws_s3_utils.py
# Luego seguir las opciones del menú
```

### 2. Migración de Datos
```bash
# Desde el menú: Opción 5
# O directamente:
python3 tools/local/aws_utils/migrate_images_to_s3.py
```

### 3. Monitoreo Continuo
```bash
# Desde el menú: Opción 6
# O directamente:
python3 tools/local/aws_utils/monitor_s3.py
```

## 📖 Documentación Detallada

Para información completa sobre AWS S3:
- [README de AWS Utils](tools/local/aws_utils/README.md)
- [Documentación AWS S3](https://docs.aws.amazon.com/s3/)

## 🔧 Desarrollo

### Instalación
```bash
pip install -r requirements.txt
```

### Tests
```bash
pytest
```

### Linting
```bash
pylint app/
```

## 📞 Soporte

Para problemas con AWS S3:
1. Ejecuta el diagnóstico: `python3 tools/local/aws_utils/diagnose_s3_permissions.py`
2. Revisa los reportes generados
3. Consulta la documentación en `tools/local/aws_utils/README.md`

---

**Autor:** EDF Developer  
**Versión:** 1.0  
**Fecha:** 2025-08-08
