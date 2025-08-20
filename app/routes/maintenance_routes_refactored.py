"""
Rutas de mantenimiento refactorizadas para el panel de administración.
Este archivo consolida funciones duplicadas y mejora el manejo de errores.
"""

import csv
import gzip
import io
import json
import os
import shutil
import tempfile
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union

import pymongo
from bson import ObjectId
from flask import Blueprint, current_app, jsonify, render_template, request, send_file
from pymongo import errors as pymongo_errors
from werkzeug.utils import secure_filename

from app.database import get_mongo_db
from app.decorators import admin_required
from app.logging_unified import get_logger

# from app.auth_utils import require_google_drive_auth  # Función no disponible
from app.utils.storage_utils import get_storage_client

# Configurar logger
logger = get_logger(__name__)

def log_info(msg):
    logger.info(msg)

def log_error(msg):
    logger.error(msg)

def log_warning(msg):
    logger.warning(msg)

# Blueprint para rutas de mantenimiento
maintenance_bp = Blueprint('maintenance', __name__, url_prefix='/api')

# ============================================================================
# CLASES DE UTILIDAD PARA PROCESAMIENTO DE ARCHIVOS
# ============================================================================

class FileProcessor:
    """Clase para manejar el procesamiento de diferentes tipos de archivos."""

    @staticmethod
    def detect_file_type(content: bytes) -> str:
        """Detecta el tipo de archivo basado en su contenido."""
        try:
            # Verificar si es gzip
            if content.startswith(b'\x1f\x8b'):
                return 'gzip'

            # Intentar decodificar como texto
            text_content = content.decode('utf-8')

            # Verificar si es JSON
            try:
                json.loads(text_content)
                return 'json'
            except json.JSONDecodeError:
                pass

            # Verificar si es CSV
            if ',' in text_content and '\n' in text_content:
                return 'csv'

            return 'text'
        except UnicodeDecodeError:
            return 'binary'

    @staticmethod
    def process_file_content(content: bytes, file_type: Optional[str] = None) -> Dict[str, Any]:
        """Procesa el contenido del archivo según su tipo."""
        if file_type is None:
            file_type = FileProcessor.detect_file_type(content)

        try:
            if file_type == 'gzip':
                return FileProcessor._process_gzip(content)
            elif file_type == 'json':
                return FileProcessor._process_json(content)
            elif file_type == 'csv':
                return FileProcessor._process_csv(content)
            else:
                raise ValueError(f"Tipo de archivo no soportado: {file_type}")
        except Exception as e:
            log_error(f"Error procesando archivo tipo {file_type}: {str(e)}")
            raise

    @staticmethod
    def _process_gzip(content: bytes) -> Dict[str, Any]:
        """Procesa archivos comprimidos con gzip."""
        try:
            decompressed = gzip.decompress(content)
            # Recursivamente procesar el contenido descomprimido
            return FileProcessor.process_file_content(decompressed)
        except Exception as e:
            raise ValueError(f"Error descomprimiendo archivo gzip: {str(e)}")

    @staticmethod
    def _process_json(content: bytes) -> Dict[str, Any]:
        """Procesa archivos JSON."""
        try:
            text_content = content.decode('utf-8')
            data = json.loads(text_content)

            if not isinstance(data, dict):
                raise ValueError("El archivo JSON debe contener un objeto")

            return data
        except json.JSONDecodeError as e:
            raise ValueError(f"Error parseando JSON: {str(e)}")
        except UnicodeDecodeError as e:
            raise ValueError(f"Error decodificando archivo: {str(e)}")

    @staticmethod
    def _process_csv(content: bytes) -> Dict[str, Any]:
        """Procesa archivos CSV y los convierte a formato de backup."""
        try:
            text_content = content.decode('utf-8')
            csv_reader = csv.DictReader(io.StringIO(text_content))

            # Convertir CSV a formato de backup
            collections = {}
            for row in csv_reader:
                # Asumir que la primera columna indica la colección
                collection_name = row.get('collection', 'default_collection')
                if collection_name not in collections:
                    collections[collection_name] = []

                # Convertir la fila a documento
                doc = {k: v for k, v in row.items() if k != 'collection'}
                collections[collection_name].append(doc)

            return {
                'metadata': {
                    'created_at': datetime.utcnow().isoformat(),
                    'source': 'csv_import',
                    'version': '1.0'
                },
                'collections': collections
            }
        except Exception as e:
            raise ValueError(f"Error procesando CSV: {str(e)}")

# ============================================================================
# CLASES DE UTILIDAD PARA GOOGLE DRIVE
# ============================================================================

class GoogleDriveManager:
    """Clase para manejar operaciones con Google Drive."""

    def __init__(self):
        self.storage_client = None

    def get_client(self):
        """Obtiene el cliente de Google Drive."""
        if not self.storage_client:
            try:
                from app.utils.storage_utils import get_storage_client
                self.storage_client = get_storage_client()
            except Exception as e:
                log_error(f"Error obteniendo cliente de Google Drive: {str(e)}")
                return None
        return self.storage_client

    def list_backups(self) -> List[Dict[str, Any]]:
        """Lista los backups disponibles en Google Drive."""
        try:
            from app.database import get_mongo_db
            db = get_mongo_db()
            if db is None:
                raise ValueError("No se pudo acceder a la base de datos")

            # Obtener backups desde la colección de metadatos
            backups = list(db.backups.find().sort("uploaded_at", -1))

            # Convertir ObjectId a string para JSON
            for backup in backups:
                backup['_id'] = str(backup['_id'])
                if 'uploaded_at' in backup:
                    backup['uploaded_at'] = backup['uploaded_at'].isoformat()

            return backups
        except Exception as e:
            log_error(f"Error listando backups de Google Drive: {str(e)}")
            raise

    def download_file(self, file_id: str, filename: str) -> bytes:
        """Descarga un archivo de Google Drive."""
        try:
            from tools.db_utils.google_drive_utils import download_file
            return download_file(file_id)
        except Exception as e:
            log_error(f"Error descargando archivo {filename}: {str(e)}")
            raise

    def delete_file(self, file_id: str) -> bool:
        """Elimina un archivo de Google Drive."""
        try:
            from app.database import get_mongo_db
            from tools.db_utils.google_drive_utils import delete_file

            # Eliminar de Google Drive
            success = delete_file(file_id)

            if success:
                # Eliminar metadatos de la base de datos
                db = get_mongo_db()
                if db is not None:
                    db.backups.delete_one({"file_id": file_id})

            return success
        except Exception as e:
            log_error(f"Error eliminando archivo {file_id}: {str(e)}")
            return False

# ============================================================================
# CLASES DE UTILIDAD PARA BACKUP Y RESTAURACIÓN
# ============================================================================

class BackupManager:
    """Clase para manejar operaciones de backup y restauración."""

    def __init__(self):
        self.db = get_mongo_db()

    def create_backup(self) -> Dict[str, Any]:
        """Crea un backup completo de la base de datos."""
        try:
            backup_data = {
                'metadata': {
                    'created_at': datetime.utcnow().isoformat(),
                    'version': '1.0',
                    'source': 'maintenance_api'
                },
                'collections': {}
            }

            # Obtener todas las colecciones
            collection_names = self.db.list_collection_names()

            for collection_name in collection_names:
                if collection_name.startswith('system.'):
                    continue

                collection = self.db[collection_name]
                documents = list(collection.find())

                # Convertir ObjectId a string para serialización JSON
                for doc in documents:
                    if '_id' in doc and isinstance(doc['_id'], ObjectId):
                        doc['_id'] = str(doc['_id'])

                backup_data['collections'][collection_name] = documents

            log_info(f"Backup creado con {len(collection_names)} colecciones")
            return backup_data
        except Exception as e:
            log_error(f"Error creando backup: {str(e)}")
            raise

    def restore_backup(self, backup_data: Dict[str, Any]) -> Dict[str, Any]:
        """Restaura un backup en la base de datos."""
        try:
            if not self._validate_backup_structure(backup_data):
                raise ValueError("Estructura de backup inválida")

            collections = backup_data.get('collections', {})
            results = {
                'restored_collections': [],
                'errors': [],
                'total_documents': 0
            }

            for collection_name, documents in collections.items():
                try:
                    result = self._restore_collection(collection_name, documents)
                    results['restored_collections'].append({
                        'name': collection_name,
                        'documents': result['inserted_count'],
                        'errors': result['errors']
                    })
                    results['total_documents'] += result['inserted_count']
                except Exception as e:
                    error_msg = f"Error restaurando colección {collection_name}: {str(e)}"
                    log_error(error_msg)
                    results['errors'].append(error_msg)

            log_info(f"Restauración completada: {results['total_documents']} documentos")
            return results
        except Exception as e:
            log_error(f"Error en restauración: {str(e)}")
            raise

    def _validate_backup_structure(self, backup_data: Dict[str, Any]) -> bool:
        """Valida la estructura del backup."""
        required_keys = ['metadata', 'collections']
        return all(key in backup_data for key in required_keys)

    def _restore_collection(self, collection_name: str, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Restaura una colección específica."""
        collection = self.db[collection_name]
        inserted_count = 0
        errors = []

        for doc in documents:
            try:
                # Convertir string _id de vuelta a ObjectId si es necesario
                if '_id' in doc and isinstance(doc['_id'], str):
                    try:
                        doc['_id'] = ObjectId(doc['_id'])
                    except Exception:
                        # Si no es un ObjectId válido, dejar como string
                        pass

                # Insertar documento
                collection.insert_one(doc)
                inserted_count += 1
            except pymongo_errors.DuplicateKeyError:
                # Documento duplicado, continuar
                continue
            except Exception as e:
                error_msg = f"Error insertando documento: {str(e)}"
                errors.append(error_msg)
                log_warning(error_msg)

        return {
            'inserted_count': inserted_count,
            'errors': errors
        }

# ============================================================================
# RUTAS DE LA API
# ============================================================================

@maintenance_bp.route('/system_status')
@admin_required
def get_system_status():
    """Obtiene el estado del sistema."""
    try:
        import psutil

        # Información de memoria
        memory = psutil.virtual_memory()

        # Información de CPU
        cpu_percent = psutil.cpu_percent(interval=1)

        # Información de disco
        disk = psutil.disk_usage('/')

        status = {
            'memory': {
                'total': memory.total,
                'available': memory.available,
                'percent': memory.percent,
                'used': memory.used
            },
            'cpu': {
                'percent': cpu_percent
            },
            'disk': {
                'total': disk.total,
                'used': disk.used,
                'free': disk.free,
                'percent': (disk.used / disk.total) * 100
            },
            'timestamp': datetime.utcnow().isoformat()
        }

        return jsonify(status)
    except Exception as e:
        log_error(f"Error obteniendo estado del sistema: {str(e)}")
        return jsonify({'error': str(e)}), 500

@maintenance_bp.route('/backup', methods=['POST'])
@admin_required
def create_backup():
    """Crea un backup de la base de datos."""
    try:
        backup_manager = BackupManager()
        backup_data = backup_manager.create_backup()

        # Crear archivo temporal
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        filename = f'backup_{timestamp}.json.gz'

        with tempfile.NamedTemporaryFile(delete=False, suffix='.json.gz') as temp_file:
            # Comprimir y escribir el backup
            json_data = json.dumps(backup_data, ensure_ascii=False, indent=2)
            compressed_data = gzip.compress(json_data.encode('utf-8'))
            temp_file.write(compressed_data)
            temp_file_path = temp_file.name

        return send_file(
            temp_file_path,
            as_attachment=True,
            download_name=filename,
            mimetype='application/gzip'
        )
    except Exception as e:
        log_error(f"Error creando backup: {str(e)}")
        return jsonify({'error': str(e)}), 500

@maintenance_bp.route('/restore', methods=['POST'])
@admin_required
def restore_backup():
    """Restaura un backup desde un archivo subido."""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No se proporcionó archivo'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No se seleccionó archivo'}), 400

        # Leer contenido del archivo
        content = file.read()

        # Procesar archivo
        file_processor = FileProcessor()
        backup_data = file_processor.process_file_content(content)

        # Restaurar backup
        backup_manager = BackupManager()
        results = backup_manager.restore_backup(backup_data)

        return jsonify({
            'success': True,
            'message': 'Backup restaurado exitosamente',
            'results': results
        })
    except Exception as e:
        log_error(f"Error restaurando backup: {str(e)}")
        return jsonify({'error': str(e)}), 500

@maintenance_bp.route('/drive/backups')
@admin_required
# @require_google_drive_auth  # Función no disponible
def list_drive_backups():
    """Lista los backups disponibles en Google Drive."""
    try:
        drive_manager = GoogleDriveManager()
        backups = drive_manager.list_backups()

        return jsonify({
            'success': True,
            'backups': backups
        })
    except Exception as e:
        log_error(f"Error listando backups de Google Drive: {str(e)}")
        return jsonify({'error': str(e)}), 500

@maintenance_bp.route('/drive/restore/<file_id>', methods=['POST'])
@admin_required
# @require_google_drive_auth  # Función no disponible
def restore_from_drive(file_id):
    """Restaura un backup desde Google Drive."""
    try:
        drive_manager = GoogleDriveManager()

        # Descargar archivo
        filename = request.json.get('filename', f'backup_{file_id}')
        content = drive_manager.download_file(file_id, filename)

        # Procesar archivo
        file_processor = FileProcessor()
        backup_data = file_processor.process_file_content(content)

        # Restaurar backup
        backup_manager = BackupManager()
        results = backup_manager.restore_backup(backup_data)

        return jsonify({
            'success': True,
            'message': 'Backup de Google Drive restaurado exitosamente',
            'results': results
        })
    except Exception as e:
        log_error(f"Error restaurando desde Google Drive: {str(e)}")
        return jsonify({'error': str(e)}), 500

@maintenance_bp.route('/drive/delete/<file_id>', methods=['DELETE'])
@admin_required
# @require_google_drive_auth  # Función no disponible
def delete_drive_backup(file_id):
    """Elimina un backup de Google Drive."""
    try:
        drive_manager = GoogleDriveManager()
        success = drive_manager.delete_file(file_id)

        if success:
            return jsonify({
                'success': True,
                'message': 'Backup eliminado exitosamente'
            })
        else:
            return jsonify({'error': 'No se pudo eliminar el archivo'}), 500
    except Exception as e:
        log_error(f"Error eliminando backup de Google Drive: {str(e)}")
        return jsonify({'error': str(e)}), 500

# ============================================================================
# REGISTRO DEL BLUEPRINT
# ============================================================================

def register_maintenance_routes(app):
    """Registra las rutas de mantenimiento en la aplicación Flask."""
    app.register_blueprint(maintenance_bp)
    log_info("Rutas de mantenimiento refactorizadas registradas")
