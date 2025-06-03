#!/usr/bin/env python3
"""
Script para verificar variables de entorno de AWS
sin revelar información sensible.
"""

import os
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

# Variables a comprobar
aws_vars = {
    "AWS_ACCESS_KEY_ID": "Clave de acceso AWS",
    "AWS_SECRET_ACCESS_KEY": "Clave secreta AWS",
    "AWS_REGION": "Región AWS",
    "S3_BUCKET_NAME": "Nombre del bucket S3"
}

print("== Verificación de Variables de Entorno AWS ==\n")

all_present = True

for var, description in aws_vars.items():
    value = os.getenv(var)
    if value:
        # Ocultar información sensible
        if var in ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"]:
            masked_value = value[:4] + "..." + value[-4:] if len(value) > 8 else "***"
            print(f"✅ {description}: {masked_value}")
        else:
            print(f"✅ {description}: {value}")
    else:
        print(f"❌ {description}: No configurado")
        all_present = False

print("\n== Resumen ==")
if all_present:
    print("✅ Todas las variables de entorno AWS necesarias están configuradas.")
else:
    print("⚠️ Faltan algunas variables de entorno AWS necesarias.")
    print("   Asegúrate de configurar correctamente el archivo .env")

# Comprobar conexión AWS si todas las variables están presentes
if all_present:
    try:
        import boto3
        print("\n== Verificación de Conexión S3 ==")
        s3 = boto3.client('s3')
        print("✅ Cliente S3 inicializado")
        
        bucket = os.getenv('S3_BUCKET_NAME')
        try:
            s3.head_bucket(Bucket=bucket)
            print(f"✅ Bucket '{bucket}' existe y es accesible")
        except Exception as e:
            print(f"❌ Error al acceder al bucket '{bucket}': {e}")
    except ImportError:
        print("\n⚠️ No se pudo importar boto3. Instale boto3 con: pip install boto3")
    except Exception as e:
        print(f"\n❌ Error al inicializar el cliente S3: {e}")

