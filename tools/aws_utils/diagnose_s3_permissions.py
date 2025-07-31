#!/usr/bin/env python3
"""
Script para diagnosticar permisos y configuración de S3
Autor: Sistema de Catálogo de Tablas
Fecha: 2025
"""

import os
import sys
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
import json
from datetime import datetime

def print_header():
    """Imprime el encabezado del diagnóstico"""
    print("=" * 60)
    print("DIAGNÓSTICO DE PERMISOS S3")
    print("=" * 60)
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

def check_aws_credentials():
    """Verifica si las credenciales de AWS están configuradas"""
    print("1. Verificando credenciales de AWS...")
    
    # Verificar variables de entorno
    aws_access_key = os.getenv('AWS_ACCESS_KEY_ID')
    aws_secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
    aws_region = os.getenv('AWS_DEFAULT_REGION')
    
    if aws_access_key and aws_secret_key:
        print("   ✓ Credenciales encontradas en variables de entorno")
        print(f"   - AWS_ACCESS_KEY_ID: {aws_access_key[:8]}...")
        print(f"   - AWS_SECRET_ACCESS_KEY: {'*' * 20}")
        print(f"   - AWS_DEFAULT_REGION: {aws_region or 'No configurada'}")
        return True
    else:
        print("   ✗ Credenciales no encontradas en variables de entorno")
        
        # Verificar archivo de credenciales
        credentials_file = os.path.expanduser('~/.aws/credentials')
        if os.path.exists(credentials_file):
            print("   ✓ Archivo de credenciales encontrado: ~/.aws/credentials")
            return True
        else:
            print("   ✗ Archivo de credenciales no encontrado")
            return False

def test_s3_connection():
    """Prueba la conexión con S3"""
    print("\n2. Probando conexión con S3...")
    
    try:
        s3_client = boto3.client('s3')
        response = s3_client.list_buckets()
        
        print("   ✓ Conexión exitosa con S3")
        print(f"   - Buckets encontrados: {len(response['Buckets'])}")
        
        for bucket in response['Buckets']:
            print(f"     • {bucket['Name']} (creado: {bucket['CreationDate']})")
        
        return s3_client, response['Buckets']
        
    except NoCredentialsError:
        print("   ✗ Error: Credenciales no configuradas")
        return None, []
    except ClientError as e:
        print(f"   ✗ Error de cliente AWS: {e}")
        return None, []
    except Exception as e:
        print(f"   ✗ Error inesperado: {e}")
        return None, []

def check_bucket_permissions(s3_client, bucket_name):
    """Verifica permisos específicos de un bucket"""
    print(f"\n3. Verificando permisos del bucket: {bucket_name}")
    
    permissions = {
        'read': False,
        'write': False,
        'delete': False,
        'list': False
    }
    
    try:
        # Probar listado de objetos
        s3_client.list_objects_v2(Bucket=bucket_name, MaxKeys=1)
        permissions['list'] = True
        print("   ✓ Permiso de listado: OK")
    except ClientError as e:
        print(f"   ✗ Permiso de listado: Error - {e}")
    
    try:
        # Probar lectura (intentar obtener ACL del bucket)
        s3_client.get_bucket_acl(Bucket=bucket_name)
        permissions['read'] = True
        print("   ✓ Permiso de lectura: OK")
    except ClientError as e:
        print(f"   ✗ Permiso de lectura: Error - {e}")
    
    try:
        # Probar escritura (crear un objeto de prueba)
        test_key = 'test-permissions-check.txt'
        s3_client.put_object(
            Bucket=bucket_name,
            Key=test_key,
            Body=b'Test file for permission check'
        )
        permissions['write'] = True
        print("   ✓ Permiso de escritura: OK")
        
        # Limpiar el archivo de prueba
        try:
            s3_client.delete_object(Bucket=bucket_name, Key=test_key)
            permissions['delete'] = True
            print("   ✓ Permiso de eliminación: OK")
        except ClientError as e:
            print(f"   ✗ Permiso de eliminación: Error - {e}")
            
    except ClientError as e:
        print(f"   ✗ Permiso de escritura: Error - {e}")
    
    return permissions

def check_bucket_configuration(s3_client, bucket_name):
    """Verifica la configuración del bucket"""
    print(f"\n4. Verificando configuración del bucket: {bucket_name}")
    
    try:
        # Verificar región del bucket
        location = s3_client.get_bucket_location(Bucket=bucket_name)
        region = location['LocationConstraint'] or 'us-east-1'
        print(f"   - Región: {region}")
        
        # Verificar versionado
        try:
            versioning = s3_client.get_bucket_versioning(Bucket=bucket_name)
            status = versioning.get('Status', 'Disabled')
            print(f"   - Versionado: {status}")
        except ClientError:
            print("   - Versionado: No disponible")
        
        # Verificar encriptación
        try:
            encryption = s3_client.get_bucket_encryption(Bucket=bucket_name)
            print("   - Encriptación: Habilitada")
        except ClientError:
            print("   - Encriptación: No configurada")
        
        # Verificar CORS
        try:
            cors = s3_client.get_bucket_cors(Bucket=bucket_name)
            print(f"   - CORS: Configurado ({len(cors['CORSRules'])} reglas)")
        except ClientError:
            print("   - CORS: No configurado")
            
    except ClientError as e:
        print(f"   ✗ Error verificando configuración: {e}")

def download_bucket(s3_client, bucket_name, local_path):
    """Descarga todo el contenido de un bucket a una carpeta local"""
    print(f"\nDescargando contenido del bucket {bucket_name}...")
    try:
        # Crear directorio local si no existe
        os.makedirs(local_path, exist_ok=True)
        
        # Listar objetos en el bucket
        paginator = s3_client.get_paginator('list_objects_v2')
        total_files = 0
        downloaded_files = 0
        
        # Contar total de archivos
        for page in paginator.paginate(Bucket=bucket_name):
            if 'Contents' in page:
                total_files += len(page['Contents'])
        
        if total_files == 0:
            print("   El bucket está vacío")
            return True
            
        print(f"   Total de archivos a descargar: {total_files}")
        
        # Descargar archivos
        for page in paginator.paginate(Bucket=bucket_name):
            if 'Contents' in page:
                for obj in page['Contents']:
                    # Crear estructura de directorios local
                    local_file_path = os.path.join(local_path, obj['Key'])
                    os.makedirs(os.path.dirname(local_file_path), exist_ok=True)
                    
                    # Descargar archivo
                    s3_client.download_file(bucket_name, obj['Key'], local_file_path)
                    downloaded_files += 1
                    
                    # Mostrar progreso
                    progress = (downloaded_files / total_files) * 100
                    print(f"\r   Progreso: {progress:.1f}% ({downloaded_files}/{total_files})", end="")
        
        print("\n   ✓ Descarga completada")
        return True
        
    except Exception as e:
        print(f"\n   ✗ Error durante la descarga: {e}")
        return False

def delete_bucket_contents(s3_client, bucket_name, delete_bucket=False):
    """Elimina todo el contenido de un bucket y opcionalmente el bucket mismo"""
    print(f"\nEliminando contenido del bucket {bucket_name}...")
    try:
        # Listar y eliminar objetos
        paginator = s3_client.get_paginator('list_objects_v2')
        total_objects = 0
        deleted_objects = 0
        
        # Contar total de objetos
        for page in paginator.paginate(Bucket=bucket_name):
            if 'Contents' in page:
                total_objects += len(page['Contents'])
        
        if total_objects == 0:
            print("   El bucket está vacío")
        else:
            print(f"   Total de objetos a eliminar: {total_objects}")
            
            # Eliminar objetos
            for page in paginator.paginate(Bucket=bucket_name):
                if 'Contents' in page:
                    objects_to_delete = [{'Key': obj['Key']} for obj in page['Contents']]
                    s3_client.delete_objects(
                        Bucket=bucket_name,
                        Delete={'Objects': objects_to_delete}
                    )
                    deleted_objects += len(objects_to_delete)
                    
                    # Mostrar progreso
                    progress = (deleted_objects / total_objects) * 100
                    print(f"\r   Progreso: {progress:.1f}% ({deleted_objects}/{total_objects})", end="")
            
            print("\n   ✓ Contenido eliminado")
        
        # Eliminar el bucket si se solicita
        if delete_bucket:
            s3_client.delete_bucket(Bucket=bucket_name)
            print("   ✓ Bucket eliminado")
        
        return True
        
    except Exception as e:
        print(f"\n   ✗ Error durante la eliminación: {e}")
        return False

def show_menu(s3_client, buckets):
    """Muestra un menú interactivo para operaciones de mantenimiento"""
    while True:
        print("\n" + "=" * 60)
        print("MENÚ DE MANTENIMIENTO DE BUCKETS")
        print("=" * 60)
        print("1. Diagnosticar permisos de buckets")
        print("2. Descargar contenido de un bucket")
        print("3. Eliminar contenido de un bucket")
        print("4. Eliminar bucket completo")
        print("5. Salir")
        
        try:
            opcion = input("\nSeleccione una opción (1-5): ")
            
            if opcion == "1":
                # Verificar permisos para cada bucket
                for bucket in buckets:
                    bucket_name = bucket['Name']
                    permissions = check_bucket_permissions(s3_client, bucket_name)
                    check_bucket_configuration(s3_client, bucket_name)
                    
                    print(f"\n📊 Resumen de permisos para {bucket_name}:")
                    for perm, status in permissions.items():
                        status_icon = "✓" if status else "✗"
                        print(f"   {status_icon} {perm.capitalize()}: {'OK' if status else 'Error'}")
            
            elif opcion in ["2", "3", "4"]:
                # Mostrar buckets disponibles
                print("\nBuckets disponibles:")
                for i, bucket in enumerate(buckets, 1):
                    print(f"{i}. {bucket['Name']}")
                
                bucket_num = int(input("\nSeleccione el número de bucket: ")) - 1
                if 0 <= bucket_num < len(buckets):
                    bucket_name = buckets[bucket_num]['Name']
                    
                    if opcion == "2":
                        local_path = input("Ingrese la ruta local para la descarga: ")
                        download_bucket(s3_client, bucket_name, local_path)
                    
                    elif opcion == "3":
                        if input(f"¿Está seguro de eliminar TODO el contenido de {bucket_name}? (s/N): ").lower() == 's':
                            delete_bucket_contents(s3_client, bucket_name, delete_bucket=False)
                    
                    elif opcion == "4":
                        if input(f"¿Está seguro de eliminar el bucket {bucket_name} y TODO su contenido? (s/N): ").lower() == 's':
                            delete_bucket_contents(s3_client, bucket_name, delete_bucket=True)
                else:
                    print("Número de bucket inválido")
            
            elif opcion == "5":
                print("\nSaliendo...")
                break
            
            else:
                print("Opción inválida")
                
        except ValueError:
            print("Por favor, ingrese un número válido")
        except Exception as e:
            print(f"Error: {e}")

def main():
    """Función principal"""
    print_header()
    
    # Verificar credenciales
    if not check_aws_credentials():
        print("\n❌ No se pueden verificar los permisos sin credenciales válidas")
        print("\nPara configurar credenciales:")
        print("1. Usar variables de entorno:")
        print("   export AWS_ACCESS_KEY_ID=tu_access_key")
        print("   export AWS_SECRET_ACCESS_KEY=tu_secret_key")
        print("   export AWS_DEFAULT_REGION=tu_region")
        print("\n2. Usar AWS CLI:")
        print("   aws configure")
        sys.exit(1)
    
    # Probar conexión
    s3_client, buckets = test_s3_connection()
    
    if not s3_client:
        print("\n❌ No se pudo establecer conexión con S3")
        sys.exit(1)
    
    if not buckets:
        print("\n⚠️  No se encontraron buckets")
        return
    
    # Mostrar menú de operaciones
    show_menu(s3_client, buckets)

if __name__ == "__main__":
    main()
