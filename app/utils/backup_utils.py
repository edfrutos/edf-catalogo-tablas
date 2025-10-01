"""
Utilidades para manejo de backups y procesamiento de archivos.
Este módulo contiene las clases y funciones refactorizadas para el manejo
de backups, procesamiento de archivos y operaciones con Google Drive.
"""

import csv
import gzip
import io
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from bson import ObjectId
from pymongo import errors as pymongo_errors

from app.database import get_mongo_db
from app.logging_unified import get_logger

# Configurar logger
logger = get_logger(__name__)


def log_info(msg):
    logger.info(msg)


def log_error(msg):
    logger.error(msg)


def log_warning(msg):
    logger.warning(msg)


# ============================================================================
# EXCEPCIONES PERSONALIZADAS
# ============================================================================


class BackupError(Exception):
    """Excepción base para errores de backup."""

    pass


class FileProcessingError(Exception):
    """Excepción para errores de procesamiento de archivos."""

    pass


class GoogleDriveError(Exception):
    """Excepción para errores de Google Drive."""

    pass


# ============================================================================
# PROCESADOR DE ARCHIVOS MEJORADO
# ============================================================================


class FileProcessor:
    """Clase mejorada para manejar el procesamiento de diferentes tipos de archivos."""

    SUPPORTED_EXTENSIONS = {".json", ".gz", ".json.gz", ".csv"}
    MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB

    def __init__(self):
        self.temp_files = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup_temp_files()

    def cleanup_temp_files(self):
        """Limpia archivos temporales creados durante el procesamiento."""
        for temp_file in self.temp_files:
            try:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
            except Exception as e:
                log_warning(
                    f"No se pudo eliminar archivo temporal {temp_file}: {str(e)}"
                )
        self.temp_files.clear()

    def validate_file(self, filename: str, content: bytes) -> bool:
        """Valida que el archivo sea procesable."""
        # Verificar extensión
        file_path = Path(filename)
        if file_path.suffix.lower() not in self.SUPPORTED_EXTENSIONS:
            if not (
                file_path.suffixes
                and "".join(file_path.suffixes[-2:]).lower()
                in self.SUPPORTED_EXTENSIONS
            ):
                raise FileProcessingError(
                    f"Extensión de archivo no soportada: {filename}"
                )

        # Verificar tamaño
        if len(content) > self.MAX_FILE_SIZE:
            raise FileProcessingError(f"Archivo demasiado grande: {len(content)} bytes")

        # Verificar que no esté vacío
        if len(content) == 0:
            raise FileProcessingError("El archivo está vacío")

        return True

    def detect_file_type(self, content: bytes, filename: str = None) -> str:
        """Detecta el tipo de archivo basado en su contenido y nombre."""
        try:
            # Verificar por extensión primero si está disponible
            if filename:
                file_path = Path(filename)
                if file_path.suffix.lower() == ".gz" or ".json.gz" in filename.lower():
                    return "gzip"
                elif file_path.suffix.lower() == ".json":
                    return "json"
                elif file_path.suffix.lower() == ".csv":
                    return "csv"

            # Verificar por contenido
            if content.startswith(b"\x1f\x8b"):
                return "gzip"

            # Intentar decodificar como texto
            try:
                text_content = content.decode("utf-8")

                # Verificar si es JSON válido
                try:
                    json.loads(text_content)
                    return "json"
                except json.JSONDecodeError:
                    pass

                # Verificar si parece CSV
                if self._looks_like_csv(text_content):
                    return "csv"

                return "text"
            except UnicodeDecodeError:
                return "binary"
        except Exception as e:
            log_error(f"Error detectando tipo de archivo: {str(e)}")
            return "unknown"

    def _looks_like_csv(self, text_content: str) -> bool:
        """Determina si el contenido parece ser CSV."""
        lines = text_content.strip().split("\n")
        if len(lines) < 2:
            return False

        # Verificar que las primeras líneas tengan el mismo número de columnas
        first_line_cols = len(lines[0].split(","))
        if first_line_cols < 2:
            return False

        # Verificar algunas líneas más
        for i in range(1, min(5, len(lines))):
            if len(lines[i].split(",")) != first_line_cols:
                return False

        return True

    def process_file_content(
        self, content: bytes, filename: str = None
    ) -> Dict[str, Any]:
        """Procesa el contenido del archivo según su tipo."""
        try:
            # Validar archivo
            if filename:
                self.validate_file(filename, content)

            # Detectar tipo
            file_type = self.detect_file_type(content, filename)
            log_info(f"Procesando archivo tipo: {file_type}")

            # Procesar según tipo
            if file_type == "gzip":
                return self._process_gzip(content)
            elif file_type == "json":
                return self._process_json(content)
            elif file_type == "csv":
                return self._process_csv(content)
            else:
                raise FileProcessingError(f"Tipo de archivo no soportado: {file_type}")
        except Exception as e:
            log_error(f"Error procesando archivo: {str(e)}")
            raise FileProcessingError(f"Error procesando archivo: {str(e)}")

    def _process_gzip(self, content: bytes) -> Dict[str, Any]:
        """Procesa archivos comprimidos con gzip."""
        try:
            log_info("Descomprimiendo archivo gzip")
            decompressed = gzip.decompress(content)

            # Recursivamente procesar el contenido descomprimido
            return self.process_file_content(decompressed)
        except Exception as e:
            raise FileProcessingError(f"Error descomprimiendo archivo gzip: {str(e)}")

    def _process_json(self, content: bytes) -> Dict[str, Any]:
        """Procesa archivos JSON."""
        try:
            log_info("Procesando archivo JSON")
            text_content = content.decode("utf-8")
            data = json.loads(text_content)

            # Validar estructura básica
            if not isinstance(data, dict):
                raise FileProcessingError("El archivo JSON debe contener un objeto")

            # Verificar si es un backup válido
            if "collections" not in data:
                log_warning("El archivo JSON no parece ser un backup válido")
                # Intentar convertir a formato de backup
                data = self._convert_to_backup_format(data)

            return data
        except json.JSONDecodeError as e:
            raise FileProcessingError(f"Error parseando JSON: {str(e)}")
        except UnicodeDecodeError as e:
            raise FileProcessingError(f"Error decodificando archivo: {str(e)}")

    def _process_csv(self, content: bytes) -> Dict[str, Any]:
        """Procesa archivos CSV y los convierte a formato de backup."""
        try:
            log_info("Procesando archivo CSV")
            text_content = content.decode("utf-8")

            # Detectar delimitador
            delimiter = self._detect_csv_delimiter(text_content)

            csv_reader = csv.DictReader(io.StringIO(text_content), delimiter=delimiter)

            # Convertir CSV a formato de backup
            collections = {}
            row_count = 0

            for row in csv_reader:
                row_count += 1

                # Determinar nombre de colección
                collection_name = row.get(
                    "collection",
                    row.get("table", row.get("coleccion", "imported_data")),
                )

                if collection_name not in collections:
                    collections[collection_name] = []

                # Limpiar y convertir la fila
                doc = self._clean_csv_row(row)
                collections[collection_name].append(doc)

            log_info(
                f"CSV procesado: {row_count} filas en {len(collections)} colecciones"
            )

            return {
                "metadata": {
                    "created_at": datetime.utcnow().isoformat(),
                    "source": "csv_import",
                    "version": "1.0",
                    "original_format": "csv",
                    "rows_processed": row_count,
                },
                "collections": collections,
            }
        except Exception as e:
            raise FileProcessingError(f"Error procesando CSV: {str(e)}")

    def _detect_csv_delimiter(self, content: str) -> str:
        """Detecta el delimitador del CSV."""
        sample = content[:1000]  # Usar solo una muestra
        sniffer = csv.Sniffer()
        try:
            delimiter = sniffer.sniff(sample).delimiter
            return delimiter
        except BaseException:
            # Fallback a coma
            return ","

    def _clean_csv_row(self, row: Dict[str, str]) -> Dict[str, Any]:
        """Limpia y convierte una fila de CSV."""
        cleaned = {}
        for key, value in row.items():
            if key and key != "collection":
                # Intentar convertir valores numéricos
                cleaned_value = self._convert_csv_value(value)
                cleaned[key.strip()] = cleaned_value
        return cleaned

    def _convert_csv_value(self, value: str) -> Any:
        """Convierte un valor de CSV al tipo apropiado."""
        if not value or value.strip() == "":
            return None

        value = value.strip()

        # Intentar convertir a número
        try:
            if "." in value:
                return float(value)
            else:
                return int(value)
        except ValueError:
            pass

        # Intentar convertir a booleano
        if value.lower() in ("true", "false", "verdadero", "falso", "sí", "no"):
            return value.lower() in ("true", "verdadero", "sí")

        # Devolver como string
        return value

    def _convert_to_backup_format(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Convierte datos genéricos a formato de backup."""
        return {
            "metadata": {
                "created_at": datetime.utcnow().isoformat(),
                "source": "json_import",
                "version": "1.0",
                "original_format": "json",
            },
            "collections": {
                "imported_data": [data] if isinstance(data, dict) else data
            },
        }


# ============================================================================
# GESTOR DE BACKUPS MEJORADO
# ============================================================================


class BackupManager:
    """Clase mejorada para manejar operaciones de backup y restauración."""

    def __init__(self):
        self.db = get_mongo_db()
        self.excluded_collections = {"system.indexes", "system.users"}

    def create_backup(self, collections: List[str] = None) -> Dict[str, Any]:
        """Crea un backup completo o parcial de la base de datos."""
        try:
            log_info("Iniciando creación de backup")

            backup_data = {
                "metadata": {
                    "created_at": datetime.utcnow().isoformat(),
                    "version": "2.0",
                    "source": "backup_manager",
                    "database_name": self.db.name,
                },
                "collections": {},
            }

            # Obtener colecciones a respaldar
            if collections:
                collection_names = collections
            else:
                collection_names = [
                    name
                    for name in self.db.list_collection_names()
                    if not name.startswith("system.")
                    and name not in self.excluded_collections
                ]

            total_documents = 0

            for collection_name in collection_names:
                try:
                    log_info(f"Respaldando colección: {collection_name}")
                    collection = self.db[collection_name]
                    documents = list(collection.find())

                    # Convertir ObjectId a string para serialización JSON
                    processed_docs = []
                    for doc in documents:
                        processed_doc = self._process_document_for_backup(doc)
                        processed_docs.append(processed_doc)

                    backup_data["collections"][collection_name] = processed_docs
                    total_documents += len(processed_docs)

                    log_info(
                        f"Colección {collection_name}: {len(processed_docs)} documentos"
                    )
                except Exception as e:
                    log_error(
                        f"Error respaldando colección {collection_name}: {str(e)}"
                    )
                    raise BackupError(
                        f"Error respaldando colección {collection_name}: {str(e)}"
                    )  # noqa: B904

            backup_data["metadata"]["total_collections"] = len(collection_names)
            backup_data["metadata"]["total_documents"] = total_documents

            log_info(
                f"Backup creado: {len(collection_names)} colecciones, {total_documents} documentos"
            )
            return backup_data
        except Exception as e:
            log_error(f"Error creando backup: {str(e)}")
            raise BackupError(f"Error creando backup: {str(e)}")  # noqa: B904

    def _process_document_for_backup(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        """Procesa un documento para el backup, convirtiendo tipos especiales."""
        processed: Dict[str, Any] = {}
        for key, value in doc.items():
            if isinstance(value, ObjectId):
                processed[key] = str(value)
            elif isinstance(value, datetime):
                processed[key] = value.isoformat()
            elif isinstance(value, dict):
                processed[key] = self._process_document_for_backup(value)
            elif isinstance(value, list):
                processed[key] = [
                    (
                        self._process_document_for_backup(item)
                        if isinstance(item, dict)
                        else item
                    )
                    for item in value
                ]
            else:
                processed[key] = value
        return processed

    def restore_backup(
        self, backup_data: Dict[str, Any], overwrite: bool = False
    ) -> Dict[str, Any]:
        """Restaura un backup en la base de datos."""
        try:
            log_info("Iniciando restauración de backup")

            if not self._validate_backup_structure(backup_data):
                raise BackupError("Estructura de backup inválida")

            collections = backup_data.get("collections", {})
            results = {
                "restored_collections": [],
                "errors": [],
                "total_documents": 0,
                "skipped_documents": 0,
            }

            for collection_name, documents in collections.items():
                try:
                    log_info(f"Restaurando colección: {collection_name}")
                    result = self._restore_collection(
                        collection_name, documents, overwrite
                    )

                    results["restored_collections"].append(
                        {
                            "name": collection_name,
                            "documents_inserted": result["inserted_count"],
                            "documents_skipped": result["skipped_count"],
                            "errors": result["errors"],
                        }
                    )

                    results["total_documents"] += result["inserted_count"]
                    results["skipped_documents"] += result["skipped_count"]

                    if result["errors"]:
                        results["errors"].extend(result["errors"])

                except Exception as e:
                    error_msg = (
                        f"Error restaurando colección {collection_name}: {str(e)}"
                    )
                    log_error(error_msg)
                    results["errors"].append(error_msg)

            log_info(
                f"Restauración completada: {results['total_documents']} documentos insertados, {results['skipped_documents']} omitidos"
            )
            return results
        except Exception as e:
            log_error(f"Error en restauración: {str(e)}")
            raise BackupError(f"Error en restauración: {str(e)}")

    def _validate_backup_structure(self, backup_data: Dict[str, Any]) -> bool:
        """Valida la estructura del backup."""
        if not isinstance(backup_data, dict):
            return False

        required_keys = ["metadata", "collections"]
        if not all(key in backup_data for key in required_keys):
            return False

        if not isinstance(backup_data["collections"], dict):
            return False

        return True

    def _restore_collection(
        self,
        collection_name: str,
        documents: List[Dict[str, Any]],
        overwrite: bool = False,
    ) -> Dict[str, Any]:
        """Restaura una colección específica."""
        collection = self.db[collection_name]
        inserted_count = 0
        skipped_count = 0
        errors = []

        # Si overwrite es True, limpiar la colección primero
        if overwrite:
            try:
                _ = collection.delete_many({})
                log_info(f"Colección {collection_name} limpiada para sobrescritura")
            except Exception as e:
                log_warning(
                    f"No se pudo limpiar la colección {collection_name}: {str(e)}"
                )

        for doc in documents:
            try:
                # Procesar documento para restauración
                processed_doc = self._process_document_for_restore(doc)

                # Insertar documento
                _ = collection.insert_one(processed_doc)
                inserted_count += 1
            except pymongo_errors.DuplicateKeyError:
                # Documento duplicado, continuar
                skipped_count += 1
                continue
            except Exception as e:
                error_msg = f"Error insertando documento en {collection_name}: {str(e)}"
                errors.append(error_msg)
                log_warning(error_msg)

        return {
            "inserted_count": inserted_count,
            "skipped_count": skipped_count,
            "errors": errors,
        }

    def _process_document_for_restore(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        """Procesa un documento para la restauración, convirtiendo tipos especiales."""
        processed: Dict[str, Any] = {}
        for key, value in doc.items():
            if key == "_id" and isinstance(value, str):
                try:
                    processed[key] = ObjectId(value)
                except Exception:
                    # Si no es un ObjectId válido, dejar como string
                    processed[key] = value
            elif isinstance(value, str) and self._looks_like_datetime(value):
                try:
                    processed[key] = datetime.fromisoformat(
                        value.replace("Z", "+00:00")
                    )
                except Exception:
                    processed[key] = value
            elif isinstance(value, dict):
                processed[key] = self._process_document_for_restore(value)
            elif isinstance(value, list):
                processed[key] = [
                    (
                        self._process_document_for_restore(item)
                        if isinstance(item, dict)
                        else item
                    )
                    for item in value
                ]
            else:
                processed[key] = value
        return processed

    def _looks_like_datetime(self, value: str) -> bool:
        """Determina si una cadena parece ser una fecha ISO."""
        if not isinstance(value, str) or len(value) < 19:
            return False

        # Buscar patrón básico de fecha ISO
        return "T" in value and ("-" in value or ":" in value)


# ============================================================================
# GESTOR DE GOOGLE DRIVE MEJORADO
# ============================================================================


class GoogleDriveManager:
    """Clase mejorada para manejar operaciones con Google Drive."""

    def __init__(self):
        self.storage_client = None
        self._authenticated = False
        self.folder_name = os.getenv("GOOGLE_DRIVE_FOLDER", "Backups_CatalogoTablas")

    def get_client(self):
        """Obtiene el cliente de Google Drive con manejo de errores."""
        try:
            if not self.storage_client:
                from .storage_utils import get_storage_client

                self.storage_client = get_storage_client()
                if self.storage_client:
                    self._authenticated = True
                    log_info("Cliente de Google Drive inicializado")
                else:
                    raise GoogleDriveError(
                        "No se pudo inicializar el cliente de Google Drive"
                    )
            return self.storage_client
        except Exception as e:
            log_error(f"Error obteniendo cliente de Google Drive: {str(e)}")
            raise GoogleDriveError(f"Error de autenticación con Google Drive: {str(e)}")

    def is_authenticated(self) -> bool:
        """Verifica si está autenticado con Google Drive."""
        try:
            client = self.get_client()
            return client is not None and self._authenticated
        except BaseException:
            return False

    def list_backups(self, folder_name: str = None) -> List[Dict[str, Any]]:
        """Lista los backups disponibles en Google Drive."""
        try:
            client = self.get_client()
            if not client:
                raise GoogleDriveError("Cliente de Google Drive no disponible")

            folder_name = folder_name or self.folder_name
            log_info(f"Listando backups en carpeta: {folder_name}")

            # Importar funciones de Google Drive
            import sys

            sys.path.append(
                os.path.join(os.path.dirname(__file__), "../../tools/db_utils")
            )
            from tools.db_utils.google_drive_utils_v2 import list_files_in_folder

            # Listar archivos en la carpeta
            files = list_files_in_folder(folder_name)

            backups = []
            for file_info in files:
                if file_info["name"].endswith(".json.gz") or file_info["name"].endswith(
                    ".json"
                ):
                    backups.append(
                        {
                            "id": file_info["id"],
                            "name": file_info["name"],
                            "size": file_info.get("size", 0),
                            "created_date": file_info.get("created", ""),
                            "modified_date": file_info.get("modified", ""),
                            "download_url": file_info.get("download_url", ""),
                        }
                    )

            log_info(f"Encontrados {len(backups)} backups")
            return backups
        except Exception as e:
            log_error(f"Error listando backups de Google Drive: {str(e)}")
            raise GoogleDriveError(f"Error listando backups: {str(e)}")

    def download_file(self, file_id: str, filename: str) -> bytes:
        """Descarga un archivo de Google Drive."""
        try:
            client = self.get_client()
            if not client:
                raise GoogleDriveError("Cliente de Google Drive no disponible")

            log_info(f"Descargando archivo: {filename} (ID: {file_id})")

            # Importar función de descarga
            import sys

            sys.path.append(
                os.path.join(os.path.dirname(__file__), "../../tools/db_utils")
            )
            from tools.db_utils.google_drive_utils_v2 import download_file

            # Descargar el archivo
            content = download_file(file_id)

            if content:
                log_info(f"Archivo descargado: {len(content)} bytes")
                return content
            else:
                raise GoogleDriveError(f"No se pudo descargar el archivo {filename}")

        except Exception as e:
            log_error(f"Error descargando archivo {filename}: {str(e)}")
            raise GoogleDriveError(f"Error descargando archivo: {str(e)}")

    def upload_file(
        self, content: bytes, filename: str, folder_name: str = None
    ) -> str:
        """Sube un archivo a Google Drive."""
        try:
            client = self.get_client()
            if not client:
                raise GoogleDriveError("Cliente de Google Drive no disponible")

            folder_name = folder_name or self.folder_name
            log_info(
                f"Subiendo archivo: {filename} ({len(content)} bytes) a carpeta: {folder_name}"
            )

            # Importar funciones de Google Drive
            import sys
            import tempfile

            sys.path.append(
                os.path.join(os.path.dirname(__file__), "../../tools/db_utils")
            )
            from tools.db_utils.google_drive_utils_v2 import upload_file_to_drive

            # Crear archivo temporal
            with tempfile.NamedTemporaryFile(
                delete=False, suffix=".json.gz"
            ) as temp_file:
                temp_file.write(content)
                temp_file_path = temp_file.name

            try:
                # Subir archivo a Google Drive
                result = upload_file_to_drive(temp_file_path, folder_name)

                if result and "file_id" in result:
                    file_id = result["file_id"]
                    log_info(f"Archivo subido exitosamente: {file_id}")
                    return file_id
                else:
                    raise GoogleDriveError("No se recibió ID del archivo subido")

            finally:
                # Limpiar archivo temporal
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)

        except Exception as e:
            log_error(f"Error subiendo archivo {filename}: {str(e)}")
            raise GoogleDriveError(f"Error subiendo archivo: {str(e)}")

    def delete_file(self, file_id: str) -> bool:
        """Elimina un archivo de Google Drive."""
        try:
            client = self.get_client()
            if not client:
                raise GoogleDriveError("Cliente de Google Drive no disponible")

            log_info(f"Eliminando archivo: {file_id}")

            # Usar el cliente de PyDrive2 para eliminar
            file_obj = client.CreateFile({"id": file_id})
            file_obj.Delete()

            log_info(f"Archivo eliminado exitosamente: {file_id}")
            return True

        except Exception as e:
            log_error(f"Error eliminando archivo {file_id}: {str(e)}")
            raise GoogleDriveError(f"Error eliminando archivo: {str(e)}")


# ============================================================================
# FUNCIONES DE UTILIDAD
# ============================================================================


def create_compressed_backup(backup_data: Dict[str, Any]) -> bytes:
    """Crea un backup comprimido en formato JSON.gz."""
    try:
        json_data = json.dumps(backup_data, ensure_ascii=False, indent=2)
        compressed_data = gzip.compress(json_data.encode("utf-8"))
        return compressed_data
    except Exception as e:
        raise BackupError(f"Error creando backup comprimido: {str(e)}")


def validate_backup_file(filename: str) -> bool:
    """Valida que un archivo sea un backup válido basado en su nombre."""
    valid_extensions = {".json", ".gz", ".json.gz"}
    file_path = Path(filename)

    # Verificar extensión
    if file_path.suffix.lower() in valid_extensions:
        return True

    # Verificar extensión compuesta (.json.gz)
    if len(file_path.suffixes) >= 2:
        compound_ext = "".join(file_path.suffixes[-2:]).lower()
        if compound_ext in valid_extensions:
            return True

    return False


def get_backup_info(backup_data: Dict[str, Any]) -> Dict[str, Any]:
    """Extrae información resumida de un backup."""
    metadata = backup_data.get("metadata", {})
    collections = backup_data.get("collections", {})

    total_documents = sum(len(docs) for docs in collections.values())

    return {
        "created_at": metadata.get("created_at"),
        "version": metadata.get("version"),
        "source": metadata.get("source"),
        "total_collections": len(collections),
        "total_documents": total_documents,
        "collections": list(collections.keys()),
    }
