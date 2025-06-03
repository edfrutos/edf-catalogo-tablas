#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para diagnosticar permisos de AWS S3 en el bucket edf-catalogo-tablas.
Este script intenta realizar operaciones básicas (listar, leer, escribir, eliminar)
e informa específicamente cuáles operaciones tienen éxito y cuáles fallan.
"""

import os
import uuid
import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configuración de AWS
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_REGION = os.getenv('AWS_REGION')
S3_BUCKET_NAME = os.getenv('S3_BUCKET_NAME')

# Colores para la consola
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_success(message):
    print(f"{GREEN}✓ ÉXITO: {message}{RESET}")

def print_error(message):
    print(f"{RED}✗ ERROR: {message}{RESET}")

def print_info(message):
    print(f"{BLUE}ℹ INFO: {message}{RESET}")

def print_section(message):
    print(f"\n{YELLOW}▶ {message}{RESET}")
    print("-" * 80)

def check_environment_variables():
    """Verifica que todas las variables de entorno necesarias estén configuradas."""
    print_section("VERIFICANDO VARIABLES DE ENTORNO")
    
    all_vars_set = True
    
    if not AWS_ACCESS_KEY_ID:
        print_error("Variable AWS_ACCESS_KEY_ID no está configurada")
        all_vars_set = False
    else:
        print_success(f"AWS_ACCESS_KEY_ID configurada ({AWS_ACCESS_KEY_ID[:4]}...)")
    
    if not AWS_SECRET_ACCESS_KEY:
        print_error("Variable AWS_SECRET_ACCESS_KEY no está configurada")
        all_vars_set = False
    else:
        print_success(f"AWS_SECRET_ACCESS_KEY configurada ({len(AWS_SECRET_ACCESS_KEY)} caracteres)")
    
    if not AWS_REGION:
        print_error("Variable AWS_REGION no está configurada")
        all_vars_set = False
    else:
        print_success(f"AWS_REGION configurada ({AWS_REGION})")
    
    if not S3_BUCKET_NAME:
        print_error("Variable S3_BUCKET_NAME no está configurada")
        all_vars_set = False
    else:
        print_success(f"S3_BUCKET_NAME configurada ({S3_BUCKET_NAME})")
    
    return all_vars_set

def init_s3_client():
    """Inicializa el cliente de S3."""
    try:
        return boto3.client(
            's3',
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            region_name=AWS_REGION
        )
    except Exception as e:
        print_error(f"No se pudo inicializar el cliente S3: {str(e)}")
        return None

def check_bucket_exists(s3_client):
    """Verifica si el bucket existe y es accesible."""
    print_section("VERIFICANDO EXISTENCIA DEL BUCKET")
    
    try:
        s3_client.head_bucket(Bucket=S3_BUCKET_NAME)
        print_success(f"El bucket '{S3_BUCKET_NAME}' existe y es accesible")
        return True
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', 'Unknown')
        if error_code == '403':
            print_error(f"El bucket '{S3_BUCKET_NAME}' existe pero no tienes permisos para acceder a él")
            print_info("Esto puede deberse a permisos IAM incorrectos o una política de bucket restrictiva")
        elif error_code == '404':
            print_error(f"El bucket '{S3_BUCKET_NAME}' no existe")
            print_info("Asegúrate de que has creado el bucket en la región correcta")
        else:
            print_error(f"Error al verificar el bucket: {str(e)}")
        return False
    except Exception as e:
        print_error(f"Error inesperado al verificar el bucket: {str(e)}")
        return False

def check_list_permission(s3_client):
    """Verifica el permiso para listar objetos en el bucket."""
    print_section("VERIFICANDO PERMISO DE LISTAR OBJETOS")
    
    try:
        s3_client.list_objects_v2(Bucket=S3_BUCKET_NAME, MaxKeys=1)
        print_success(f"Puedes listar objetos en el bucket '{S3_BUCKET_NAME}'")
        return True
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', 'Unknown')
        print_error(f"No puedes listar objetos en el bucket (Error {error_code})")
        print_info("Permiso necesario: s3:ListBucket")
        return False
    except Exception as e:
        print_error(f"Error inesperado al listar objetos: {str(e)}")
        return False

def check_read_permission(s3_client):
    """Verifica el permiso para leer objetos del bucket."""
    print_section("VERIFICANDO PERMISO DE LECTURA")
    
    # Primero listamos para ver si hay algún objeto que podamos usar para la prueba
    try:
        response = s3_client.list_objects_v2(Bucket=S3_BUCKET_NAME, MaxKeys=1)
        if 'Contents' in response and len(response['Contents']) > 0:
            test_object = response['Contents'][0]['Key']
            print_info(f"Intentando leer el objeto existente: {test_object}")
            
            try:
                s3_client.head_object(Bucket=S3_BUCKET_NAME, Key=test_object)
                print_success(f"Puedes verificar la existencia de objetos en el bucket")
                
                try:
                    s3_client.get_object(Bucket=S3_BUCKET_NAME, Key=test_object)
                    print_success(f"Puedes leer objetos del bucket '{S3_BUCKET_NAME}'")
                    return True
                except ClientError as e:
                    error_code = e.response.get('Error', {}).get('Code', 'Unknown')
                    print_error(f"No puedes leer objetos del bucket (Error {error_code})")
                    print_info("Permiso necesario: s3:GetObject")
                    return False
            except ClientError as e:
                error_code = e.response.get('Error', {}).get('Code', 'Unknown')
                print_error(f"No puedes verificar la existencia de objetos (Error {error_code})")
                print_info("Permiso necesario: s3:HeadObject")
                return False
        else:
            print_info("No hay objetos en el bucket para probar la lectura")
            print_info("Se omitirá la prueba de lectura")
            return None
    except ClientError:
        print_error("No se puede listar objetos para probar la lectura")
        print_info("Se omitirá la prueba de lectura")
        return None
    except Exception as e:
        print_error(f"Error inesperado al verificar permisos de lectura: {str(e)}")
        return None

def check_write_permission(s3_client):
    """Verifica el permiso para escribir objetos en el bucket."""
    print_section("VERIFICANDO PERMISO DE ESCRITURA")
    
    # Crear un archivo temporal para la prueba
    test_key = f"test-permissions-{uuid.uuid4()}.txt"
    test_content = b"Este es un archivo de prueba para verificar permisos de S3."
    
    print_info(f"Intentando escribir un objeto de prueba: {test_key}")
    
    try:
        s3_client.put_object(Bucket=S3_BUCKET_NAME, Key=test_key, Body=test_content)
        print_success(f"Puedes escribir objetos en el bucket '{S3_BUCKET_NAME}'")
        
        # Intentar eliminar el objeto de prueba
        try:
            s3_client.delete_object(Bucket=S3_BUCKET_NAME, Key=test_key)
            print_success(f"Puedes eliminar objetos del bucket '{S3_BUCKET_NAME}'")
            return True, True  # Éxito en escritura y eliminación
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            print_error(f"No puedes eliminar objetos del bucket (Error {error_code})")
            print_info("Permiso necesario: s3:DeleteObject")
            print_info(f"⚠️ El objeto de prueba {test_key} permanece en el bucket")
            return True, False  # Éxito en escritura, fallo en eliminación
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', 'Unknown')
        print_error(f"No puedes escribir objetos en el bucket (Error {error_code})")
        print_info("Permiso necesario: s3:PutObject")
        return False, None  # Fallo en escritura, no se prueba eliminación
    except Exception as e:
        print_error(f"Error inesperado al verificar permisos de escritura: {str(e)}")
        return False, None

def summarize_permissions(list_ok, read_ok, write_ok, delete_ok):
    """Muestra un resumen de los permisos verificados."""
    print_section("RESUMEN DE PERMISOS")
    
    if list_ok:
        print_success("s3:ListBucket - Listar objetos en el bucket")
    else:
        print_error("s3:ListBucket - Listar objetos en el bucket")
    
    if read_ok is True:
        print_success("s3:GetObject - Leer objetos del bucket")
    elif read_ok is False:
        print_error("s3:GetObject - Leer objetos del bucket")
    else:
        print_info("s3:GetObject - No se pudo verificar (no hay objetos para leer)")
    
    if write_ok:
        print_success("s3:PutObject - Escribir objetos en el bucket")
    else:
        print_error("s3:PutObject - Escribir objetos en el bucket")
    
    if delete_ok is True:
        print_success("s3:DeleteObject - Eliminar objetos del bucket")
    elif delete_ok is False:
        print_error("s3:DeleteObject - Eliminar objetos del bucket")
    else:
        print_info("s3:DeleteObject - No se pudo verificar (fallo al escribir objeto de prueba)")

def suggest_policy_fixes(list_ok, read_ok, write_ok, delete_ok):
    """Sugiere correcciones de política basadas en los permisos faltantes."""
    print_section("SOLUCIONES SUGERIDAS")
    
    missing_permissions = []
    if not list_ok:
        missing_permissions.append("s3:ListBucket")
    if read_ok is False:
        missing_permissions.append("s3:GetObject")
    if not write_ok:
        missing_permissions.append("s3:PutObject")
    if delete_ok is False:
        missing_permissions.append("s3:DeleteObject")
    
    if not missing_permissions:
        print_success("¡Todos los permisos están correctamente configurados!")
        return
    
    print_info(f"Permisos faltantes: {', '.join(missing_permissions)}")
    
    # Sugerir una política IAM
    print("\nPolítica IAM sugerida para el usuario:")
    print("```json")
    policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": missing_permissions,
                "Resource": [
                    f"arn:aws:s3:::{S3_BUCKET_NAME}",
                    f"arn:aws:s3:::{S3_BUCKET_NAME}/*"
                ]
            }
        ]
    }
    import json
    print(json.dumps(policy, indent=4))
    print("```")
    
    # Sugerir una política de bucket
    print("\nAlternativamente, política de bucket sugerida:")
    print("```json")
    bucket_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "AWS": "arn:aws:iam::CUENTA_AWS:user/NOMBRE_USUARIO"
                },
                "Action": missing_permissions,
                "Resource": [
                    f"arn:aws:s3:::{S3_BUCKET_NAME}",
                    f"arn:aws:s3:::{S3_BUCKET_NAME}/*"
                ]
            }
        ]
    }
    print(json.dumps(bucket_policy, indent=4))
    print("```")
    
    print_info("Reemplaza 'CUENTA_AWS' con tu ID de cuenta AWS y 'NOMBRE_USUARIO' con el nombre de tu usuario IAM")
    print_info("Puedes aplicar la política IAM en la consola de AWS: IAM > Usuarios > TuUsuario > Añadir permisos")
    print_info("O la política de bucket en: S3 > TuBucket > Permisos > Política de bucket")

def main():
    """Función principal para diagnosticar permisos S3."""
    print("\n" + "=" * 80)
    print(f"{BLUE}DIAGNÓSTICO DE PERMISOS AWS S3 PARA {S3_BUCKET_NAME}{RESET}")
    print("=" * 80)
    
    if not check_environment_variables():
        print_error("Faltan variables de entorno necesarias. Revisa la configuración.")
        return
    
    s3_client = init_s3_client()
    if not s3_client:
        return
    
    bucket_exists = check_bucket_exists(s3_client)
    if not bucket_exists:
        print_section("RECOMENDACIONES")
        print_info("Verifica que:")
        print("1. El nombre del bucket está correctamente escrito")
        print("2. El bucket existe en la región especificada")
        print("3. Tienes los permisos necesarios en IAM")
        return
    
    list_ok = check_list_permission(s3_client)
    read_ok = check_read_permission(s3_client)
    write_ok, delete_ok = check_write_permission(s3_client)


    # Mostrar resumen y sugerencias
    summarize_permissions(list_ok, read_ok, write_ok, delete_ok)
    suggest_policy_fixes(list_ok, read_ok, write_ok, delete_ok)

if __name__ == "__main__":
    main()
