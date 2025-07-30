#!/usr/bin/env python3
import json
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()
bucket_name = os.getenv('S3_BUCKET_NAME')
aws_access_key = os.getenv('AWS_ACCESS_KEY_ID')

# Verificar si tenemos la información necesaria
if not bucket_name:
    print("⚠️ No se encontró la variable S3_BUCKET_NAME en el archivo .env")
    bucket_name = input("Por favor, ingresa el nombre del bucket S3: ")

# 1. Generar una política IAM para acceso completo al bucket
s3_full_policy = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:ListBucket",
                "s3:GetBucketLocation"
            ],
            "Resource": f"arn:aws:s3:::{bucket_name}"
        },
        {
            "Effect": "Allow",
            "Action": [
                "s3:PutObject",
                "s3:GetObject",
                "s3:DeleteObject"
            ],
            "Resource": f"arn:aws:s3:::{bucket_name}/*"
        }
    ]
}

# 2. Generar configuración CORS para el bucket
cors_config = {
    "CORSRules": [
        {
            "AllowedHeaders": ["*"],
            "AllowedMethods": ["GET", "PUT", "POST", "DELETE", "HEAD"],
            "AllowedOrigins": ["https://edefrutos2025.xyz"],
            "ExposeHeaders": ["ETag"],
            "MaxAgeSeconds": 3000
        }
    ]
}

# 3. Mostrar instrucciones
print("\n🔐 CONFIGURACIÓN DE ACCESO A AMAZON S3")
print("=====================================")
print(f"Bucket S3: {bucket_name}")
if aws_access_key:
    print(f"ID de clave de acceso: {aws_access_key}")
else:
    print("⚠️ No se encontró la clave de acceso AWS en el archivo .env")

print("\n1️⃣ PERMISOS IAM NECESARIOS")
print("---------------------------")
print("Para que el usuario de AWS tenga acceso completo al bucket, debe tener")
print("la siguiente política adjunta a su usuario o rol:")
print("\n```json")
print(json.dumps(s3_full_policy, indent=2))
print("```")

print("\n2️⃣ CONFIGURACIÓN CORS DEL BUCKET")
print("------------------------------")
print("Para permitir que el sitio web interactúe con el bucket S3, configura la siguiente")
print("política CORS en el bucket:")
print("\n```json")
print(json.dumps(cors_config, indent=2))
print("```")

print("\n🛠️ CÓMO APLICAR ESTOS CAMBIOS:")
print("-----------------------------")
print("1. Inicia sesión en la consola de AWS: https://console.aws.amazon.com/")
print("2. Para configurar la política IAM:")
print("   a. Ve a IAM > Users > [tu usuario] > Add permissions > Attach policies directly")
print("   b. Crea una política en línea y pega el JSON de la política IAM")
print("   c. Asigna un nombre como 'S3BucketAccess' y guarda la política")
print("3. Para configurar CORS en el bucket:")
print("   a. Ve a S3 > Buckets > [tu bucket] > Permissions")
print("   b. Desplázate hasta 'Cross-origin resource sharing (CORS)'")
print("   c. Haz clic en 'Edit' y pega el JSON de configuración CORS")
print("   d. Guarda los cambios")
print("4. Reinicia Apache después de realizar estos cambios:")
print("   sudo systemctl restart apache2")

print("\n✅ Después de aplicar estos cambios, ejecuta el script fix_aws_credentials.py")
print("   para verificar que las credenciales funcionan correctamente.")
