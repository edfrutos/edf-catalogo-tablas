# Guía de Configuración y Solución de Problemas de AWS S3

Esta guía te ayudará a resolver problemas comunes de permisos en AWS S3, configurar correctamente un bucket, y establecer políticas IAM adecuadas para tu aplicación.

## Índice
- [Creación y Configuración de un Bucket S3](#creación-y-configuración-de-un-bucket-s3)
- [Configuración de Políticas IAM](#configuración-de-políticas-iam)
- [Verificación y Solución de Problemas de Acceso](#verificación-y-solución-de-problemas-de-acceso)
- [Integración con tu Aplicación](#integración-con-tu-aplicación)

## Creación y Configuración de un Bucket S3

### 1. Crear un nuevo bucket

1. Inicia sesión en la [Consola de AWS](https://console.aws.amazon.com/)
2. Navega a **S3** desde el menú de servicios
3. Haz clic en **Crear bucket**
4. Configura el bucket:
   - **Nombre del bucket**: `edf-catalogo-tablas` (debe ser único globalmente)
   - **Región**: EU (Frankfurt) eu-central-1
   - **Configuración de bloqueo de acceso público**: Para desarrollo, puedes desmarcar "Bloquear todo el acceso público" aunque no es recomendable para producción
   - **Versionado**: Opcional, habilitar si deseas mantener versiones de archivos
   - **Cifrado**: Habilitado (recomendado)
5. Haz clic en **Crear bucket**

### 2. Configurar CORS (importante para aplicaciones web)

1. Ve a tu bucket recién creado
2. Selecciona la pestaña **Permisos**
3. Desplázate hacia abajo hasta **CORS** (Cross-origin resource sharing)
4. Haz clic en **Editar** y pega la siguiente configuración:

```json
[
    {
        "AllowedHeaders": ["*"],
        "AllowedMethods": ["GET", "PUT", "POST", "DELETE", "HEAD"],
        "AllowedOrigins": ["*"],
        "ExposeHeaders": ["ETag"]
    }
]
```

Para producción, reemplaza `"AllowedOrigins": ["*"]` con tus dominios específicos (ej. `["https://edefrutos2025.xyz"]`).

### 3. Configurar una política de bucket (opcional)

Si necesitas acceso público a ciertos objetos:

1. En la pestaña **Permisos** de tu bucket
2. Desplázate hasta **Política de bucket**
3. Haz clic en **Editar** y pega una política como esta (ajusta según tus necesidades):

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "PublicReadForGetBucketObjects",
            "Effect": "Allow",
            "Principal": "*",
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::edf-catalogo-tablas/*"
        }
    ]
}
```

**NOTA**: Esta política permite lectura pública de todos los objetos. Para una aplicación en producción, considera usar políticas más restrictivas.

## Configuración de Políticas IAM

### 1. Crear un usuario IAM con acceso programático

Si aún no tienes un usuario IAM:

1. Ve a la consola de **IAM** en AWS
2. Navega a **Usuarios** → **Añadir usuarios**
3. Configura:
   - **Nombre de usuario**: `edf-catalogo-app`
   - **Tipo de acceso**: Marca "Acceso programático"
4. Haz clic en **Siguiente: Permisos**

### 2. Configurar permisos adecuados

Hay dos enfoques:

#### Opción A: Adjuntar política existente (más sencillo)

1. Busca y selecciona `AmazonS3FullAccess` (esto da acceso completo a S3, considera usar algo más restrictivo en producción)
2. Continúa hasta completar la creación del usuario
3. **IMPORTANTE**: Guarda el Access Key ID y Secret Access Key que se muestran

#### Opción B: Crear una política personalizada (más seguro)

1. En lugar de usar una política existente, selecciona **Adjuntar políticas directamente**
2. Haz clic en **Crear política**
3. En el editor JSON, pega:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:ListBucket"
            ],
            "Resource": "arn:aws:s3:::edf-catalogo-tablas"
        },
        {
            "Effect": "Allow",
            "Action": [
                "s3:PutObject",
                "s3:GetObject",
                "s3:DeleteObject"
            ],
            "Resource": "arn:aws:s3:::edf-catalogo-tablas/*"
        }
    ]
}
```

4. Haz clic en **Siguiente** y proporciona un nombre como `edf-catalogo-s3-policy`
5. Crea la política y asígnala al usuario
6. Completa la creación del usuario y guarda las credenciales

### 3. Verificar los permisos de un usuario existente

Si ya tienes un usuario IAM con acceso programático:

1. Ve a **IAM** → **Usuarios**
2. Selecciona tu usuario
3. En la pestaña **Permisos**, verifica que tenga los permisos necesarios para S3
4. Si necesitas añadir permisos, haz clic en **Añadir permisos** y sigue los pasos anteriores

## Verificación y Solución de Problemas de Acceso

### 1. Verificar credenciales y conexión

Ejecuta el siguiente código Python para verificar que puedes conectarte a AWS S3:

```python
import boto3
from botocore.exceptions import ClientError
import os

# Configurar credenciales (mejor usar variables de entorno)
AWS_ACCESS_KEY_ID = 'TU_ACCESS_KEY_ID'
AWS_SECRET_ACCESS_KEY = 'TU_SECRET_ACCESS_KEY'
AWS_REGION = 'eu-central-1'
BUCKET_NAME = 'edf-catalogo-tablas'

# Inicializar cliente S3
s3 = boto3.client(
    's3',
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION
)

# Verificar acceso al bucket
try:
    s3.head_bucket(Bucket=BUCKET_NAME)
    print(f"✅ Conexión exitosa al bucket {BUCKET_NAME}")
    
    # Listar objetos en el bucket
    response = s3.list_objects_v2(Bucket=BUCKET_NAME, MaxKeys=5)
    print(f"Objetos en el bucket: {response.get('KeyCount', 0)}")
    
except ClientError as e:
    error_code = e.response.get('Error', {}).get('Code', 'Desconocido')
    if error_code == '403':
        print(f"❌ Error de permisos (403 Forbidden): No tienes acceso al bucket {BUCKET_NAME}")
        print("   Verifica las políticas IAM y los permisos del bucket")
    elif error_code == '404':
        print(f"❌ Error 404: El bucket {BUCKET_NAME} no existe o no está en la región configurada")
    else:
        print(f"❌ Error {error_code}: {e}")
```

### 2. Problemas comunes y soluciones

#### Error 403 (Forbidden)

**Causas posibles**:
- El usuario IAM no tiene permisos suficientes
- La política del bucket bloquea el acceso
- La configuración de acceso público del bucket está bloqueando el acceso

**Soluciones**:
1. Verifica que el usuario IAM tenga los permisos necesarios (`s3:ListBucket`, `s3:GetObject`, `s3:PutObject`, `s3:DeleteObject`)
2. Revisa la política del bucket para asegurarte de que no esté bloqueando el acceso
3. Comprueba la configuración de "Block Public Access" del bucket

#### Error 404 (Not Found)

**Causas posibles**:
- El bucket no existe
- El bucket existe pero en una región diferente
- Error en el nombre del bucket

**Soluciones**:
1. Verifica que el bucket exista en la consola de AWS
2. Confirma que estás usando la región correcta
3. Comprueba que el nombre del bucket esté escrito correctamente

#### Errores de conexión

**Causas posibles**:
- Problemas de red
- Credenciales incorrectas
- Región incorrecta

**Soluciones**:
1. Verifica tu conexión a internet
2. Comprueba que las credenciales (Access Key ID y Secret Access Key) sean correctas
3. Asegúrate de usar la región correcta

## Integración con tu Aplicación

### 1. Actualizar el archivo .env

Asegúrate de que tu archivo `.env` tenga las siguientes variables:

```
AWS_ACCESS_KEY_ID=tu_access_key
AWS_SECRET_ACCESS_KEY=tu_secret_key
AWS_REGION=eu-central-1
S3_BUCKET_NAME=edf-catalogo-tablas
```

### 2. Verificación final

Después de configurar todo, ejecuta el script de verificación para asegurarte de que tu aplicación puede:
- Conectarse a S3
- Subir archivos
- Leer archivos
- Eliminar archivos

### 3. Migración de imágenes existentes

Una vez que hayas configurado correctamente el acceso a S3, puedes ejecutar el script de migración que hemos creado:

```bash
python migrate_images_to_s3.py
```

Este script transferirá todas las imágenes existentes de tu sistema de archivos local a AWS S3, y actualizará las referencias en la base de datos.

---

## Recursos Adicionales

- [Documentación oficial de AWS S3](https://docs.aws.amazon.com/s3/index.html)
- [Guía de mejores prácticas de seguridad para S3](https://docs.aws.amazon.com/AmazonS3/latest/userguide/security-best-practices.html)
- [Documentación de Boto3 (SDK de AWS para Python)](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html)

