#!/usr/bin/env python3
# Script: backup_mongodb.py
# Descripción: Realiza respaldos automáticos de la base de datos MongoDB
# Uso: python3 backup_mongodb.py [--retention 7] [--backup-dir ./backups]
# Requiere: pymongo, python-dotenv, pymongobackup
# Variables de entorno: MONGO_URI
# Autor: EDF Equipo de Desarrollo - 2025-06-05
"""
Script mejorado para respaldos de MongoDB con cifrado y almacenamiento en la nube
"""

import os
import sys
import subprocess
import datetime
import logging
import tarfile
import shutil
import json
from pathlib import Path
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError
from cryptography.fernet import Fernet
import pymongo
from pymongo import MongoClient
import boto3
from botocore.exceptions import ClientError
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import argparse

# Configuración básica de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('backup_mongodb.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Cargar variables de entorno
load_dotenv()

class MongoBackup:
    def __init__(self, config_path='backup_config.json'):
        """Inicializar configuración"""
        self.config = self._load_config(config_path)
        self.backup_dir = Path(self.config.get('backup_dir', '/backups/mongodb'))
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Configuración de cifrado
        self.encryption_key = os.getenv('ENCRYPTION_KEY')
        if not self.encryption_key:
            logger.warning("No se encontró clave de cifrado. Generando una nueva...")
            self.encryption_key = Fernet.generate_key().decode()
            logger.info(f"Nueva clave de cifrado generada. Guárdala de forma segura: {self.encryption_key}")
        self.cipher_suite = Fernet(self.encryption_key.encode())
        
        # Configuración de notificaciones
        self.notify_email = self.config.get('notify_email')
        self.smtp_config = self.config.get('smtp', {})
        
        # Configuración de Google Drive
        self.google_credentials = self.config.get('google_credentials')
        self.google_folder_id = self.config.get('google_folder_id')
        
        # Configuración de S3
        self.s3_config = self.config.get('s3', {})
        
    def _load_config(self, config_path='backup_config.json'):
        """Cargar configuración desde archivo JSON"""
        default_config = {
            'backup_dir': '/backups/mongodb',
            'retention_days': 7,
            's3': {
                'enabled': False,
                'bucket_name': '',
                'access_key': '',
                'secret_key': '',
                'region': 'us-east-1'
            },
            'google_drive': {
                'enabled': False,
                'folder_id': '',
                'credentials_file': ''
            },
            'notifications': {
                'enabled': True,
                'email': '',
                'smtp': {
                    'host': 'smtp.gmail.com',
                    'port': 587,
                    'user': '',
                    'password': '',
                    'from': 'noreply@example.com'
                }
            }
        }
        
        try:
            with open(config_path) as f:
                user_config = json.load(f)
                # Combinar con la configuración por defecto
                return {**default_config, **user_config}
        except FileNotFoundError:
            logger.warning(f"Archivo de configuración {config_path} no encontrado. Usando valores por defecto.")
            return default_config
        except json.JSONDecodeError:
            logger.error(f"Error al decodificar el archivo de configuración {config_path}")
            return default_config

    def _connect_mongodb(self):
        """Establecer conexión con MongoDB"""
        try:
            client = MongoClient(
                host=self.config.get('mongo_uri', 'mongodb://localhost:27017/'),
                username=os.getenv('MONGO_USER'),
                password=os.getenv('MONGO_PASSWORD'),
                authSource='admin'
            )
            # Verificar conexión
            client.admin.command('ping')
            return client
        except Exception as e:
            logger.error(f"Error al conectar con MongoDB: {str(e)}")
            self._notify("Error en respaldo MongoDB", f"No se pudo conectar a MongoDB: {str(e)}")
            sys.exit(1)

    def _create_backup(self):
        """Crear respaldo de la base de datos"""
        try:
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_name = f"mongodb_backup_{timestamp}"
            temp_dir = self.backup_dir / backup_name
            temp_dir.mkdir(exist_ok=True)
            
            # Verificar espacio en disco
            if not self._check_disk_space():
                raise Exception("Espacio en disco insuficiente para el respaldo")
                
            # Crear respaldo con mongodump
            self._run_mongodump(temp_dir)
            
            # Comprimir el respaldo
            backup_file = self._compress_backup(temp_dir, backup_name)
            
            # Cifrar el respaldo
            encrypted_file = self._encrypt_backup(backup_file)
            
            # Subir a almacenamiento en la nube
            self._upload_to_cloud(encrypted_file)
            
            # Limpiar archivos temporales
            self._cleanup_temp_files(temp_dir, backup_file)
            
            logger.info("Respaldo completado exitosamente")
            self._notify_success(encrypted_file)
            
            return True
            
        except subprocess.CalledProcessError as e:
            error_msg = f"Error en mongodump: {str(e)}"
            logger.error(error_msg)
            self._notify_failure("Error en mongodump", error_msg)
        except Exception as e:
            error_msg = f"Error inesperado: {str(e)}"
            logger.error(error_msg, exc_info=True)
            self._notify_failure("Error en el respaldo", error_msg)
        
        return False

    def _compress_directory(self, source_dir, output_file):
        """Comprimir directorio a archivo tar.gz"""
        with tarfile.open(output_file, "w:gz") as tar:
            tar.add(source_dir, arcname=os.path.basename(source_dir))
        logger.info(f"Directorio comprimido: {output_file}")

    def _encrypt_file(self, file_path):
        """Cifrar archivo usando Fernet"""
        encrypted_path = Path(f"{file_path}.enc")
        
        with open(file_path, 'rb') as f:
            file_data = f.read()
        
        encrypted_data = self.cipher_suite.encrypt(file_data)
        
        with open(encrypted_path, 'wb') as f:
            f.write(encrypted_data)
            
        logger.info(f"Archivo cifrado: {encrypted_path}")
        return encrypted_path

    def _upload_to_google_drive(self, file_path):
        """Subir archivo a Google Drive"""
        if not self.google_credentials or not self.google_folder_id:
            return
            
        try:
            credentials = service_account.Credentials.from_service_account_file(
                self.google_credentials,
                scopes=['https://www.googleapis.com/auth/drive.file']
            )
            
            service = build('drive', 'v3', credentials=credentials)
            
            file_metadata = {
                'name': file_path.name,
                'parents': [self.google_folder_id]
            }
            
            media = MediaFileUpload(
                file_path,
                mimetype='application/octet-stream',
                resumable=True
            )
            
            file = service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()
            
            logger.info(f"Archivo subido a Google Drive con ID: {file.get('id')}")
            
        except HttpError as e:
            logger.error(f"Error al subir a Google Drive: {str(e)}")
        except Exception as e:
            logger.error(f"Error inesperado al subir a Google Drive: {str(e)}")

    def _upload_to_s3(self, file_path):
        """Subir archivo a Amazon S3"""
        if not self.s3_config:
            return
            
        try:
            s3_client = boto3.client(
                's3',
                aws_access_key_id=self.s3_config.get('access_key'),
                aws_secret_access_key=self.s3_config.get('secret_key'),
                region_name=self.s3_config.get('region', 'us-east-1')
            )
            
            s3_client.upload_file(
                str(file_path),
                self.s3_config['bucket_name'],
                f"backups/{file_path.name}"
            )
            
            logger.info(f"Archivo subido a S3: s3://{self.s3_config['bucket_name']}/backups/{file_path.name}")
            
        except ClientError as e:
            logger.error(f"Error al subir a S3: {str(e)}")
        except Exception as e:
            logger.error(f"Error inesperado al subir a S3: {str(e)}")

    def _notify(self, subject, message):
        """Enviar notificación por correo electrónico"""
        if not self.notify_email:
            return
            
        try:
            msg = MIMEMultipart()
            msg['From'] = self.smtp_config.get('from', 'noreply@example.com')
            msg['To'] = self.notify_email
            msg['Subject'] = f"[MongoDB Backup] {subject}"
            
            msg.attach(MIMEText(message, 'plain'))
            
            with smtplib.SMTP(
                host=self.smtp_config.get('host', 'smtp.gmail.com'),
                port=self.smtp_config.get('port', 587)
            ) as server:
                server.starttls()
                if 'user' in self.smtp_config and 'password' in self.smtp_config:
                    server.login(
                        self.smtp_config['user'],
                        self.smtp_config['password']
                    )
                server.send_message(msg)
                
            logger.info("Notificación enviada por correo electrónico")
            
        except Exception as e:
            logger.error(f"Error al enviar notificación: {str(e)}")

    def cleanup_old_backups(self, days_to_keep=7):
        """Eliminar respaldos antiguos"""
        try:
            cutoff_date = datetime.datetime.now() - datetime.timedelta(days=days_to_keep)
            deleted = 0
            
            for file_path in self.backup_dir.glob('*.enc'):
                file_time = datetime.datetime.fromtimestamp(file_path.stat().st_mtime)
                if file_time < cutoff_date:
                    file_path.unlink()
                    logger.info(f"Eliminado respaldo antiguo: {file_path}")
                    deleted += 1
                    
            logger.info(f"Se eliminaron {deleted} respaldos antiguos")
            return deleted
            
        except Exception as e:
            logger.error(f"Error al limpiar respaldos antiguos: {str(e)}")
            return 0

    def run(self):
        """Ejecutar el proceso completo de respaldo"""
        logger.info("=== Iniciando proceso de respaldo de MongoDB ===")
        
        # Verificar espacio en disco
        total, used, free = shutil.disk_usage(self.backup_dir)
        if free < 1 * 1024 * 1024 * 1024:  # Menos de 1GB libre
            logger.error("Espacio en disco insuficiente para el respaldo")
            self._notify(
                "Error en respaldo MongoDB",
                "Espacio en disco insuficiente para el respaldo"
            )
            return False
        
        # Crear respaldo
        backup_file = self._create_backup()
        
        # Limpiar respaldos antiguos
        self.cleanup_old_backups(days_to_keep=self.config.get('retention_days', 7))
        
        return backup_file is not None

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Herramienta de respaldo para MongoDB')
    parser.add_argument('--config', default='backup_config.json', help='Ruta al archivo de configuración')
    parser.add_argument('--cleanup', action='store_true', help='Solo limpiar respaldos antiguos')
    args = parser.parse_args()
    
    backup = MongoBackup(config_path=args.config)
    
    if args.cleanup:
        backup.cleanup_old_backups()
    else:
        backup.run()