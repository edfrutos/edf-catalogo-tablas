#!/usr/bin/env python3
import os
import boto3
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

# Obtener credenciales de AWS desde variables de entorno
aws_access_key = os.getenv('AWS_ACCESS_KEY_ID')
aws_secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
aws_region = os.getenv('AWS_REGION', 'us-east-1')
bucket_name = os.getenv('S3_BUCKET_NAME')

# Verificar si tenemos todas las credenciales necesarias
if not all([aws_access_key, aws_secret_key, bucket_name]):
    print("Faltan variables de entorno necesarias:")
    print(f"AWS_ACCESS_KEY_ID: {'Configurado' if aws_access_key else 'No configurado'}")
    print(f"AWS_SECRET_ACCESS_KEY: {'Configurado' if aws_secret_key else 'No configurado'}")
    print(f"S3_BUCKET_NAME: {'Configurado' if bucket_name else 'No configurado'}")
    exit(1)

try:
    # Crear cliente S3
    s3 = boto3.client(
        's3',
        aws_access_key_id=aws_access_key,
        aws_secret_access_key=aws_secret_key,
        region_name=aws_region
    )
    
    # Verificar que podemos listar el bucket
    print(f"Intentando listar objetos en el bucket {bucket_name}...")
    response = s3.list_objects_v2(Bucket=bucket_name, MaxKeys=5)
    
    if 'Contents' in response:
        print(f"Conexión exitosa al bucket. Se encontraron {len(response['Contents'])} objetos.")
        for obj in response['Contents'][:5]:
            print(f"- {obj['Key']} ({obj['Size']} bytes)")
    else:
        print("El bucket existe pero está vacío.")
    
    # Verificar la configuración CORS
    print("\nVerificando configuración CORS...")
    try:
        cors = s3.get_bucket_cors(Bucket=bucket_name)
        print("Configuración CORS actual:")
        for rule in cors.get('CORSRules', []):
            print(f"- Allowed Methods: {rule.get('AllowedMethods', [])}")
            print(f"- Allowed Origins: {rule.get('AllowedOrigins', [])}")
            print(f"- Allowed Headers: {rule.get('AllowedHeaders', [])}")
            print(f"- Expose Headers: {rule.get('ExposeHeaders', [])}")
            print(f"- Max Age Seconds: {rule.get('MaxAgeSeconds', '')}")
    except s3.exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchCORSConfiguration':
            print("No hay configuración CORS para este bucket.")
        else:
            print(f"Error al verificar CORS: {e}")
    
    # Probar generación de URL prefirmada
    print("\nProbando generación de URL prefirmada...")
    if 'Contents' in response and len(response['Contents']) > 0:
        test_key = response['Contents'][0]['Key']
        url = s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket_name, 'Key': test_key},
            ExpiresIn=3600
        )
        print(f"URL prefirmada generada para {test_key}:")
        print(url)
    else:
        print("No hay objetos en el bucket para probar la generación de URL.")
        
except Exception as e:
    print(f"Error al conectar con S3: {e}")
