#!/usr/bin/env python3
"""
Script: s3_utils.py
Descripción: Módulo de utilidades para AWS S3 consolidado.
             Incluye funciones para subir, descargar, eliminar y gestionar archivos en S3.

Funcionalidades:
  ✅ Subida de archivos a S3
  ✅ Descarga de archivos de S3
  ✅ Eliminación de archivos de S3
  ✅ Generación de URLs prefirmadas
  ✅ Listado de objetos en bucket
  ✅ Verificación de existencia de archivos
  ✅ Backup y restauración de archivos

Uso:
  from tools.local.aws_utils.s3_utils import S3Manager

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
import logging
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class S3Manager:
    """Gestor de operaciones S3."""

    def __init__(self, bucket_name=None, region=None):
        """
        Inicializa el gestor S3.

        Args:
            bucket_name (str): Nombre del bucket S3. Si es None, usa S3_BUCKET_NAME
            region (str): Región AWS. Si es None, usa AWS_REGION
        """
        self.aws_access_key = os.getenv("AWS_ACCESS_KEY_ID")
        self.aws_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        self.aws_region = region or os.getenv("AWS_REGION")
        self.bucket_name = bucket_name or os.getenv("S3_BUCKET_NAME")

        if not all([self.aws_access_key, self.aws_secret_key, self.aws_region]):
            raise ValueError(
                "Credenciales AWS incompletas. Verifica AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION"
            )

        if not self.bucket_name:
            raise ValueError(
                "Nombre de bucket no especificado. Configura S3_BUCKET_NAME o pasa bucket_name"
            )

        self.s3_client = boto3.client(
            "s3",
            aws_access_key_id=self.aws_access_key,
            aws_secret_access_key=self.aws_secret_key,
            region_name=self.aws_region,
        )

        logger.info(f"S3Manager inicializado para bucket: {self.bucket_name}")

    def upload_file(
        self, file_path, object_name=None, delete_local=False, metadata=None
    ):
        """
        Sube un archivo a S3.

        Args:
            file_path (str): Ruta local del archivo
            object_name (str): Nombre del objeto en S3. Si es None, usa el nombre del archivo
            delete_local (bool): Si es True, elimina el archivo local después de subir
            metadata (dict): Metadatos adicionales para el objeto

        Returns:
            str|None: URL S3 del archivo subido o None si falla
        """
        if not os.path.exists(file_path):
            logger.error(f"Archivo no encontrado: {file_path}")
            return None

        if object_name is None:
            object_name = os.path.basename(file_path)

        try:
            extra_args = {}
            if metadata:
                extra_args["Metadata"] = metadata

            self.s3_client.upload_file(
                file_path, self.bucket_name, object_name, ExtraArgs=extra_args
            )

            s3_url = f"s3://{self.bucket_name}/{object_name}"
            logger.info(f"Archivo subido exitosamente: {s3_url}")

            if delete_local:
                os.remove(file_path)
                logger.info(f"Archivo local eliminado: {file_path}")

            return s3_url

        except ClientError as e:
            logger.error(f"Error subiendo archivo a S3: {e}")
            return None

    def download_file(self, object_name, file_path=None):
        """
        Descarga un archivo de S3.

        Args:
            object_name (str): Nombre del objeto en S3
            file_path (str): Ruta local donde guardar. Si es None, usa el nombre del objeto

        Returns:
            bool: True si la descarga fue exitosa
        """
        if file_path is None:
            file_path = os.path.basename(object_name)

        try:
            self.s3_client.download_file(self.bucket_name, object_name, file_path)
            logger.info(f"Archivo descargado: {object_name} -> {file_path}")
            return True

        except ClientError as e:
            logger.error(f"Error descargando archivo de S3: {e}")
            return False

    def delete_file(self, object_name):
        """
        Elimina un archivo de S3.

        Args:
            object_name (str): Nombre del objeto en S3

        Returns:
            bool: True si la eliminación fue exitosa
        """
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=object_name)
            logger.info(f"Archivo eliminado de S3: {object_name}")
            return True

        except ClientError as e:
            logger.error(f"Error eliminando archivo de S3: {e}")
            return False

    def get_presigned_url(self, object_name, expiration=3600, operation="get_object"):
        """
        Genera una URL prefirmada para un objeto S3.

        Args:
            object_name (str): Nombre del objeto en S3
            expiration (int): Tiempo de expiración en segundos (por defecto 1 hora)
            operation (str): Operación ('get_object', 'put_object', etc.)

        Returns:
            str|None: URL prefirmada o None si falla
        """
        try:
            url = self.s3_client.generate_presigned_url(
                operation,
                Params={"Bucket": self.bucket_name, "Key": object_name},
                ExpiresIn=expiration,
            )
            logger.info(f"URL prefirmada generada para: {object_name}")
            return url

        except ClientError as e:
            logger.error(f"Error generando URL prefirmada: {e}")
            return None

    def list_objects(self, prefix="", max_keys=1000):
        """
        Lista objetos en el bucket S3.

        Args:
            prefix (str): Prefijo para filtrar objetos
            max_keys (int): Número máximo de objetos a listar

        Returns:
            list: Lista de objetos encontrados
        """
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name, Prefix=prefix, MaxKeys=max_keys
            )

            objects = response.get("Contents", [])
            logger.info(f"Encontrados {len(objects)} objetos con prefijo '{prefix}'")
            return objects

        except ClientError as e:
            logger.error(f"Error listando objetos: {e}")
            return []

    def object_exists(self, object_name):
        """
        Verifica si un objeto existe en S3.

        Args:
            object_name (str): Nombre del objeto en S3

        Returns:
            bool: True si el objeto existe
        """
        try:
            self.s3_client.head_object(Bucket=self.bucket_name, Key=object_name)
            return True

        except ClientError as e:
            # Manejar el error de forma segura verificando las claves
            error_code = None
            try:
                error_code = e.response.get("Error", {}).get("Code")
            except (KeyError, TypeError):
                pass

            if error_code == "404":
                return False
            else:
                logger.error(f"Error verificando existencia de objeto: {e}")
                return False

    def get_object_metadata(self, object_name):
        """
        Obtiene metadatos de un objeto S3.

        Args:
            object_name (str): Nombre del objeto en S3

        Returns:
            dict|None: Metadatos del objeto o None si falla
        """
        try:
            response = self.s3_client.head_object(
                Bucket=self.bucket_name, Key=object_name
            )
            return {
                "size": response["ContentLength"],
                "last_modified": response["LastModified"],
                "content_type": response.get("ContentType"),
                "metadata": response.get("Metadata", {}),
            }

        except ClientError as e:
            logger.error(f"Error obteniendo metadatos: {e}")
            return None

    def copy_object(self, source_key, destination_key, source_bucket=None):
        """
        Copia un objeto dentro del mismo bucket o entre buckets.

        Args:
            source_key (str): Clave del objeto origen
            destination_key (str): Clave del objeto destino
            source_bucket (str): Bucket origen. Si es None, usa el bucket actual

        Returns:
            bool: True si la copia fue exitosa
        """
        source_bucket = source_bucket or self.bucket_name

        try:
            copy_source = {"Bucket": source_bucket, "Key": source_key}
            self.s3_client.copy_object(
                CopySource=copy_source, Bucket=self.bucket_name, Key=destination_key
            )
            logger.info(f"Objeto copiado: {source_key} -> {destination_key}")
            return True

        except ClientError as e:
            logger.error(f"Error copiando objeto: {e}")
            return False

    def backup_file(self, file_path, backup_prefix="backups/"):
        """
        Crea un backup de un archivo en S3.

        Args:
            file_path (str): Ruta del archivo a respaldar
            backup_prefix (str): Prefijo para el backup

        Returns:
            str|None: URL S3 del backup o None si falla
        """
        if not os.path.exists(file_path):
            logger.error(f"Archivo no encontrado para backup: {file_path}")
            return None

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.basename(file_path)
        backup_key = f"{backup_prefix}{timestamp}_{filename}"

        metadata = {
            "original_path": file_path,
            "backup_date": timestamp,
            "backup_type": "file_backup",
        }

        return self.upload_file(file_path, backup_key, metadata=metadata)

    def get_bucket_info(self):
        """
        Obtiene información del bucket S3.

        Returns:
            dict|None: Información del bucket o None si falla
        """
        try:
            response = self.s3_client.head_bucket(Bucket=self.bucket_name)

            # Obtener estadísticas básicas
            objects = self.list_objects()
            total_size = sum(obj["Size"] for obj in objects)

            return {
                "name": self.bucket_name,
                "region": self.aws_region,
                "object_count": len(objects),
                "total_size": total_size,
                "creation_date": response.get("ResponseMetadata", {})
                .get("HTTPHeaders", {})
                .get("date"),
            }

        except ClientError as e:
            logger.error(f"Error obteniendo información del bucket: {e}")
            return None


# Funciones de conveniencia para uso directo
def upload_to_s3(file_path, object_name=None, bucket_name=None):
    """Función de conveniencia para subir archivos a S3."""
    try:
        s3_manager = S3Manager(bucket_name=bucket_name)
        return s3_manager.upload_file(file_path, object_name)
    except Exception as e:
        logger.error(f"Error en upload_to_s3: {e}")
        return None


def download_from_s3(object_name, file_path=None, bucket_name=None):
    """Función de conveniencia para descargar archivos de S3."""
    try:
        s3_manager = S3Manager(bucket_name=bucket_name)
        return s3_manager.download_file(object_name, file_path)
    except Exception as e:
        logger.error(f"Error en download_from_s3: {e}")
        return False


def delete_from_s3(object_name, bucket_name=None):
    """Función de conveniencia para eliminar archivos de S3."""
    try:
        s3_manager = S3Manager(bucket_name=bucket_name)
        return s3_manager.delete_file(object_name)
    except Exception as e:
        logger.error(f"Error en delete_from_s3: {e}")
        return False


def get_s3_url(object_name, expiration=3600, bucket_name=None):
    """Función de conveniencia para obtener URLs prefirmadas."""
    try:
        s3_manager = S3Manager(bucket_name=bucket_name)
        return s3_manager.get_presigned_url(object_name, expiration)
    except Exception as e:
        logger.error(f"Error en get_s3_url: {e}")
        return None


if __name__ == "__main__":
    # Ejemplo de uso
    print("🔧 S3 Utils - Módulo de utilidades para AWS S3")
    print("=" * 50)

    try:
        s3_manager = S3Manager()
        bucket_info = s3_manager.get_bucket_info()

        if bucket_info:
            print(f"📦 Bucket: {bucket_info['name']}")
            print(f"🌍 Región: {bucket_info['region']}")
            print(f"📄 Objetos: {bucket_info['object_count']}")
            print(f"💾 Tamaño total: {bucket_info['total_size']} bytes")
        else:
            print("❌ No se pudo obtener información del bucket")

    except Exception as e:
        print(f"❌ Error: {e}")
        print("💡 Verifica las credenciales AWS y la configuración del bucket")
