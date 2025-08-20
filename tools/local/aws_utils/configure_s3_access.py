#!/usr/bin/env python3
"""
Script: configure_s3_access.py
Descripción: Configura y valida el acceso a AWS S3 para el proyecto EDF Catálogo Tablas.
             Verifica credenciales, configura bucket y establece permisos básicos.

Funcionalidades:
  ✅ Validación de credenciales AWS
  ✅ Verificación de permisos S3
  ✅ Configuración de bucket
  ✅ Test de conectividad
  ✅ Generación de archivo de configuración

Uso:
  python3 configure_s3_access.py

Requisitos:
  - boto3
  - python-dotenv
  - Credenciales AWS configuradas

Variables de entorno:
  - AWS_ACCESS_KEY_ID
  - AWS_SECRET_ACCESS_KEY
  - AWS_REGION
  - S3_BUCKET_NAME

Autor: EDF Developer - 2025-08-08
Versión: 1.0
"""

import json
import os
import sys
from pathlib import Path

import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()


class S3Configurator:
    """Configurador de acceso a AWS S3."""

    def __init__(self):
        self.aws_access_key = os.getenv("AWS_ACCESS_KEY_ID")
        self.aws_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        self.aws_region = os.getenv("AWS_REGION")
        self.s3_bucket_name = os.getenv("S3_BUCKET_NAME")
        self.s3_client = None

    def validate_credentials(self):
        """Valida que las credenciales AWS estén configuradas."""
        print("🔍 Validando credenciales AWS...")

        if not self.aws_access_key:
            print("❌ AWS_ACCESS_KEY_ID no está configurada")
            return False

        if not self.aws_secret_key:
            print("❌ AWS_SECRET_ACCESS_KEY no está configurada")
            return False

        if not self.aws_region:
            print("❌ AWS_REGION no está configurada")
            return False

        print("✅ Credenciales AWS configuradas")
        return True

    def test_aws_connection(self):
        """Prueba la conexión a AWS."""
        print("🔍 Probando conexión a AWS...")

        try:
            # Crear cliente STS para verificar credenciales
            sts_client = boto3.client(
                "sts",
                aws_access_key_id=self.aws_access_key,
                aws_secret_access_key=self.aws_secret_key,
                region_name=self.aws_region,
            )

            # Obtener identidad del usuario
            identity = sts_client.get_caller_identity()
            print("✅ Conexión exitosa a AWS")
            print(f"   Usuario: {identity['Arn']}")
            print(f"   Account ID: {identity['Account']}")

            return True

        except NoCredentialsError:
            print("❌ No se pudieron encontrar credenciales AWS")
            return False
        except ClientError as e:
            print(f"❌ Error de autenticación AWS: {e}")
            return False
        except Exception as e:
            print(f"❌ Error inesperado: {e}")
            return False

    def initialize_s3_client(self):
        """Inicializa el cliente S3."""
        print("🔍 Inicializando cliente S3...")

        try:
            self.s3_client = boto3.client(
                "s3",
                aws_access_key_id=self.aws_access_key,
                aws_secret_access_key=self.aws_secret_key,
                region_name=self.aws_region,
            )
            print("✅ Cliente S3 inicializado")
            return True
        except Exception as e:
            print(f"❌ Error inicializando cliente S3: {e}")
            return False

    def list_s3_buckets(self):
        """Lista todos los buckets S3 disponibles."""
        print("🔍 Listando buckets S3 disponibles...")

        try:
            response = self.s3_client.list_buckets()
            buckets = response["Buckets"]

            if not buckets:
                print("⚠️  No se encontraron buckets S3")
                return []

            print(f"✅ Encontrados {len(buckets)} buckets:")
            for bucket in buckets:
                print(f"   📦 {bucket['Name']} (Creado: {bucket['CreationDate']})")

            return [bucket["Name"] for bucket in buckets]

        except ClientError as e:
            print(f"❌ Error listando buckets: {e}")
            return []

    def check_bucket_exists(self, bucket_name):
        """Verifica si un bucket específico existe."""
        print(f"🔍 Verificando bucket: {bucket_name}")

        try:
            self.s3_client.head_bucket(Bucket=bucket_name)
            print(f"✅ Bucket '{bucket_name}' existe")
            return True
        except ClientError as e:
            # Manejar el error de forma segura verificando las claves
            error_code = None
            try:
                error_code = e.response.get("Error", {}).get("Code")
            except (KeyError, TypeError):
                pass

            if error_code == "404":
                print(f"❌ Bucket '{bucket_name}' no existe")
            else:
                print(f"❌ Error verificando bucket: {e}")
            return False

    def create_bucket_if_not_exists(self, bucket_name):
        """Crea el bucket si no existe."""
        if self.check_bucket_exists(bucket_name):
            return True

        print(f"🔧 Creando bucket: {bucket_name}")

        try:
            # Crear bucket en la región especificada
            if self.aws_region == "us-east-1":
                self.s3_client.create_bucket(Bucket=bucket_name)
            else:
                self.s3_client.create_bucket(
                    Bucket=bucket_name,
                    CreateBucketConfiguration={"LocationConstraint": self.aws_region},
                )

            print(f"✅ Bucket '{bucket_name}' creado exitosamente")
            return True

        except ClientError as e:
            print(f"❌ Error creando bucket: {e}")
            return False

    def test_s3_permissions(self, bucket_name):
        """Prueba permisos básicos de S3."""
        print(f"🔍 Probando permisos en bucket: {bucket_name}")

        test_key = "test_permissions.txt"
        test_content = "Test de permisos S3"

        try:
            # Test de escritura
            self.s3_client.put_object(
                Bucket=bucket_name, Key=test_key, Body=test_content
            )
            print("✅ Permiso de escritura: OK")

            # Test de lectura
            response = self.s3_client.get_object(Bucket=bucket_name, Key=test_key)
            content = response["Body"].read().decode("utf-8")
            if content == test_content:
                print("✅ Permiso de lectura: OK")
            else:
                print("❌ Permiso de lectura: FALLÓ")
                return False

            # Test de eliminación
            self.s3_client.delete_object(Bucket=bucket_name, Key=test_key)
            print("✅ Permiso de eliminación: OK")

            return True

        except ClientError as e:
            print(f"❌ Error en test de permisos: {e}")
            return False

    def configure_bucket_policy(self, bucket_name):
        """Configura una política básica de bucket."""
        print(f"🔧 Configurando política de bucket: {bucket_name}")

        # Política básica para permitir acceso público de lectura
        bucket_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "PublicReadGetObject",
                    "Effect": "Allow",
                    "Principal": "*",
                    "Action": "s3:GetObject",
                    "Resource": f"arn:aws:s3:::{bucket_name}/*",
                }
            ],
        }

        try:
            self.s3_client.put_bucket_policy(
                Bucket=bucket_name, Policy=json.dumps(bucket_policy)
            )
            print("✅ Política de bucket configurada")
            return True
        except ClientError as e:
            print(f"❌ Error configurando política: {e}")
            return False

    def generate_config_file(self):
        """Genera un archivo de configuración con los datos de S3."""
        print("🔧 Generando archivo de configuración...")

        config = {
            "aws_region": self.aws_region,
            "s3_bucket_name": self.s3_bucket_name,
            "configured_at": str(Path.cwd()),
            "status": "configured",
        }

        config_file = Path("tools/local/aws_utils/s3_config.json")
        config_file.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(config_file, "w") as f:
                json.dump(config, f, indent=2)
            print(f"✅ Configuración guardada en: {config_file}")
            return True
        except Exception as e:
            print(f"❌ Error guardando configuración: {e}")
            return False

    def run_configuration(self):
        """Ejecuta el proceso completo de configuración."""
        print("🚀 INICIANDO CONFIGURACIÓN DE AWS S3")
        print("=" * 50)

        # Paso 1: Validar credenciales
        if not self.validate_credentials():
            return False

        # Paso 2: Probar conexión AWS
        if not self.test_aws_connection():
            return False

        # Paso 3: Inicializar cliente S3
        if not self.initialize_s3_client():
            return False

        # Paso 4: Listar buckets existentes
        buckets = self.list_s3_buckets()

        # Paso 5: Configurar bucket
        if self.s3_bucket_name:
            if not self.create_bucket_if_not_exists(self.s3_bucket_name):
                return False

            if not self.test_s3_permissions(self.s3_bucket_name):
                return False

            # Opcional: Configurar política de bucket
            self.configure_bucket_policy(self.s3_bucket_name)
        else:
            print("⚠️  S3_BUCKET_NAME no configurado, saltando configuración de bucket")

        # Paso 6: Generar archivo de configuración
        self.generate_config_file()

        print("\n" + "=" * 50)
        print("🎉 CONFIGURACIÓN COMPLETADA")
        print("=" * 50)
        return True


def main():
    """Función principal."""
    configurator = S3Configurator()

    if configurator.run_configuration():
        print("✅ Configuración de S3 exitosa")
        sys.exit(0)
    else:
        print("❌ Configuración de S3 falló")
        sys.exit(1)


if __name__ == "__main__":
    main()
