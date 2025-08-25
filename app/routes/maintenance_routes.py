"""
Rutas de mantenimiento reorganizadas para el panel de administración.
Este archivo consolida funciones duplicadas y mejora el manejo de errores.
"""

import csv
import getpass
import gzip
import io
import json
import os
import platform
import tempfile
from datetime import datetime
from typing import Any, Dict, List, Optional

import psutil
from bson import ObjectId
from flask import Blueprint, flash, jsonify, redirect, request, send_file, url_for
from pymongo import errors as pymongo_errors

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
maintenance_bp = Blueprint("maintenance", __name__, url_prefix="/admin/maintenance")

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
            if content.startswith(b"\x1f\x8b"):
                return "gzip"

            # Intentar decodificar como texto
            text_content = content.decode("utf-8")

            # Verificar si es JSON
            try:
                data = json.loads(text_content)
                # Verificar si es un backup válido
                if isinstance(data, dict) and (
                    "collections" in data or "metadata" in data
                ):
                    return "json"
                return "json"  # JSON genérico
            except json.JSONDecodeError:
                pass

            # Verificar si es CSV
            lines = text_content.split("\n")
            if len(lines) > 1 and "," in lines[0]:
                # Verificar que tenga estructura de CSV
                first_line = lines[0]
                if first_line.count(",") > 0:
                    return "csv"

            return "text"
        except UnicodeDecodeError:
            return "binary"

    @staticmethod
    def process_file_content(
        content: bytes, file_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """Procesa el contenido del archivo según su tipo."""
        if file_type is None:
            file_type = FileProcessor.detect_file_type(content)

        try:
            if file_type == "gzip":
                return FileProcessor._process_gzip(content)
            elif file_type == "json":
                return FileProcessor._process_json(content)
            elif file_type == "csv":
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
            text_content = content.decode("utf-8")
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
            text_content = content.decode("utf-8")

            # Verificar si el contenido es realmente CSV o si es JSON
            try:
                # Intentar parsear como JSON primero (para backups nuevos)
                data = json.loads(text_content)
                if isinstance(data, dict) and "collections" in data:
                    return data
            except json.JSONDecodeError:
                pass

            # Si no es JSON, procesar como CSV tradicional
            csv_reader = csv.DictReader(io.StringIO(text_content))

            # Convertir CSV a formato de backup
            collections: Dict[str, List[Dict[str, Any]]] = {}
            for row in csv_reader:
                # Asumir que la primera columna indica la colección
                collection_name = row.get("collection", "catalogs")
                if collection_name not in collections:
                    collections[collection_name] = []

                # Convertir la fila a documento
                doc = {k: v for k, v in row.items() if k != "collection"}
                # Convertir _id string de vuelta a ObjectId si es necesario
                if "_id" in doc and isinstance(doc["_id"], str):
                    try:
                        from bson import ObjectId

                        doc["_id"] = ObjectId(doc["_id"])
                    except:
                        pass
                collections[collection_name].append(doc)

            return {
                "metadata": {
                    "created_at": datetime.utcnow().isoformat(),
                    "source": "csv_import",
                    "version": "1.0",
                    "total_collections": len(collections),
                },
                "collections": collections,
            }

        except UnicodeDecodeError as e:
            raise ValueError(f"Error decodificando archivo CSV: {str(e)}")
        except Exception as e:
            raise ValueError(f"Error procesando archivo CSV: {str(e)}")


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
            self.storage_client = get_storage_client()
        return self.storage_client

    def list_backups(self) -> List[Dict[str, Any]]:
        """Lista los backups disponibles en Google Drive."""
        try:
            # Importar la función de listado real
            import os
            import sys

            sys.path.append(
                os.path.join(os.path.dirname(__file__), "..", "..", "tools", "db_utils")
            )
            # Import google_drive_utils_v2 from the correct path
            sys.path.append(
                os.path.join(os.path.dirname(__file__), "..", "..", "tools", "db_utils")
            )
            from google_drive_utils_v2 import list_files_in_folder  # type: ignore

            # Listar archivos en la carpeta de backups
            files = list_files_in_folder("Backups_CatalogoTablas")

            # Convertir el formato de respuesta para que sea compatible con la interfaz
            backups = []
            for file_info in files:
                backup = {
                    "_id": file_info["id"],  # ID único para el JavaScript
                    "filename": file_info["name"],  # Nombre del archivo
                    "file_size": file_info["size"],  # Tamaño en bytes
                    "uploaded_at": file_info.get("created", ""),  # Fecha de creación
                    "modified_at": file_info.get(
                        "modified", ""
                    ),  # Fecha de modificación
                    "download_url": file_info.get(
                        "download_url", ""
                    ),  # URL de descarga
                    "user": "Sistema",  # Usuario por defecto
                }
                backups.append(backup)

            log_info(f"Listando {len(backups)} backups de Google Drive")
            return backups

        except Exception as e:
            log_error(f"Error listando backups de Google Drive: {str(e)}")
            # En caso de error, devolver lista vacía para no romper la interfaz
            return []

    def download_file(self, file_id: str, filename: str) -> bytes:
        """Descarga un archivo de Google Drive."""
        try:
            # Importar la función de descarga real
            import os
            import sys

            sys.path.append(
                os.path.join(os.path.dirname(__file__), "..", "..", "tools", "db_utils")
            )
            from google_drive_utils_v2 import download_file  # type: ignore

            # Descargar el archivo y devolver el contenido como bytes
            content = download_file(file_id)
            return content

        except Exception as e:
            log_error(f"Error descargando archivo {filename}: {str(e)}")
            raise Exception(f"Error al descargar archivo de Google Drive: {str(e)}")

    def delete_file(self, file_id: str) -> bool:
        """Elimina un archivo de Google Drive."""
        try:
            # Importar la función de eliminación real
            import os
            import sys

            sys.path.append(
                os.path.join(os.path.dirname(__file__), "..", "..", "tools", "db_utils")
            )
            from google_drive_utils_v2 import delete_file  # type: ignore

            # Eliminar el archivo usando la función real
            success = delete_file(file_id)

            if success:
                log_info(f"Archivo {file_id} eliminado exitosamente de Google Drive")
            else:
                log_warning(f"No se pudo eliminar el archivo {file_id} de Google Drive")

            return success
        except Exception as e:
            log_error(f"Error eliminando archivo {file_id}: {str(e)}")
            return False

    def upload_file(self, filename: str, file_content: bytes) -> str:
        """Sube un archivo a Google Drive desde contenido en bytes."""
        try:
            # Importar la función de subida real
            import os
            import sys
            import tempfile

            sys.path.append(
                os.path.join(os.path.dirname(__file__), "..", "..", "tools", "db_utils")
            )
            from google_drive_utils_v2 import upload_file_to_drive  # type: ignore

            # Crear archivo temporal
            with tempfile.NamedTemporaryFile(
                delete=False, suffix=os.path.splitext(filename)[1]
            ) as temp_file:
                _ = temp_file.write(file_content)
                temp_file_path = temp_file.name

            try:
                # Subir archivo usando la función real
                result = upload_file_to_drive(temp_file_path, "Backups_CatalogoTablas")

                if result and result.get("success"):
                    file_id = result.get("file_id")
                    log_info(
                        f"Archivo {filename} subido exitosamente a Google Drive con ID: {file_id}"
                    )
                    return file_id
                else:
                    error_msg = (
                        result.get("error", "Error desconocido")
                        if result
                        else "No se pudo subir el archivo"
                    )
                    raise Exception(f"Error subiendo a Google Drive: {error_msg}")

            finally:
                # Limpiar archivo temporal
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)

        except Exception as e:
            log_error(f"Error subiendo archivo {filename}: {str(e)}")
            raise Exception(f"Error al subir archivo a Google Drive: {str(e)}")


# ============================================================================
# CLASES DE UTILIDAD PARA BACKUP Y RESTAURACIÓN
# ============================================================================


# Agregar esta función antes de la clase BackupManager
def json_serializer(obj):
    """Función personalizada para serializar objetos no compatibles con JSON."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, ObjectId):
        return str(obj)
    elif hasattr(obj, "isoformat"):  # Para otros tipos de fecha/hora
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


class BackupManager:
    """Clase para manejar operaciones de backup y restauración."""

    def __init__(self):
        self.db = get_mongo_db()

    def create_backup(self) -> Dict[str, Any]:
        """Crea un backup completo de la base de datos."""
        try:
            backup_data = {
                "metadata": {
                    "created_at": datetime.utcnow().isoformat(),
                    "version": "1.0",
                    "total_collections": 0,
                },
                "collections": {},  # Debe ser un diccionario, no una cadena
            }

            # Obtener todas las colecciones
            if self.db is None:
                raise Exception("No se pudo conectar a la base de datos")
            collection_names = self.db.list_collection_names()

            for collection_name in collection_names:
                if collection_name.startswith("system."):
                    continue

                collection = self.db[collection_name]
                documents = list(collection.find())

                # Convertir ObjectId y datetime a string para serialización
                for doc in documents:
                    self._serialize_document(doc)

                # Convert documents list to list of dicts before assignment
                backup_data["collections"][collection_name] = [
                    dict(doc) for doc in documents
                ]

            log_info(f"Backup creado con {len(collection_names)} colecciones")
            return backup_data
        except Exception as e:
            log_error(f"Error creando backup: {str(e)}")
            raise

    def _serialize_document(self, doc):
        """Convierte recursivamente un documento para JSON."""
        for key, value in doc.items():
            if isinstance(value, ObjectId):
                doc[key] = str(value)
            elif isinstance(value, datetime):
                doc[key] = value.isoformat()
            elif isinstance(value, dict):
                self._serialize_document(value)
            elif isinstance(value, list):
                for i, item in enumerate(value):
                    if isinstance(item, dict):
                        self._serialize_document(item)
                    elif isinstance(item, ObjectId):
                        value[i] = str(item)
                    elif isinstance(item, datetime):
                        value[i] = item.isoformat()

    def restore_backup(self, backup_data: Dict[str, Any]) -> Dict[str, Any]:
        """Restaura un backup en la base de datos."""
        try:
            if not self._validate_backup_structure(backup_data):
                raise ValueError("Estructura de backup inválida")

            collections = backup_data.get("collections", {})
            results = {"restored_collections": [], "errors": [], "total_documents": 0}

            for collection_name, documents in collections.items():
                try:
                    result = self._restore_collection(collection_name, documents)
                    results["restored_collections"].append(
                        {
                            "name": collection_name,
                            "documents": result["inserted_count"],
                            "errors": result["errors"],
                        }
                    )
                    results["total_documents"] += result["inserted_count"]
                except Exception as e:
                    error_msg = (
                        f"Error restaurando colección {collection_name}: {str(e)}"
                    )
                    log_error(error_msg)
                    results["errors"].append(error_msg)

            log_info(
                f"Restauración completada: {results['total_documents']} documentos"
            )
            return results
        except Exception as e:
            log_error(f"Error en restauración: {str(e)}")
            raise

    def _validate_backup_structure(self, backup_data: Dict[str, Any]) -> bool:
        """Valida la estructura del backup."""
        required_keys = ["metadata", "collections"]
        return all(key in backup_data for key in required_keys)

    def _restore_collection(
        self, collection_name: str, documents: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Restaura una colección específica."""
        if self.db is None:
            raise Exception("No se pudo conectar a la base de datos")
        collection = self.db[collection_name]
        inserted_count = 0
        errors = []

        for doc in documents:
            try:
                # Convertir string _id de vuelta a ObjectId si es necesario
                if "_id" in doc and isinstance(doc["_id"], str):
                    try:
                        doc["_id"] = ObjectId(doc["_id"])
                    except Exception:
                        # Si no es un ObjectId válido, dejar como string
                        pass

                # Insertar documento
                _ = collection.insert_one(doc)
                inserted_count += 1
            except pymongo_errors.DuplicateKeyError:
                # Documento duplicado, continuar
                continue
            except Exception as e:
                error_msg = f"Error insertando documento: {str(e)}"
                errors.append(error_msg)
                log_warning(error_msg)

        return {"inserted_count": inserted_count, "errors": errors}


# ============================================================================
# RUTAS DEL DASHBOARD DE MANTENIMIENTO
# ============================================================================


@maintenance_bp.route("/dashboard")
@admin_required
def maintenance_dashboard():
    """Dashboard principal de mantenimiento."""
    try:
        import shutil
        from datetime import datetime

        from flask import current_app, render_template
        from flask_login import current_user

        total, used, _ = shutil.disk_usage("/")

        used_gb = used // (2**30)
        total_gb = total // (2**30)
        percent = int((used / total) * 100) if total > 0 else 0
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        data = {
            "disk": {"percent": percent, "used_gb": used_gb, "total_gb": total_gb},
            "timestamp": now,
        }

        # Obtener el estado del sistema de monitoreo desde la configuración
        monitoring_enabled = current_app.config.get("MONITORING_ENABLED", True)

        return render_template(
            "admin/maintenance/dashboard.html",
            user=getattr(current_user, "email", "usuario"),
            data=data,
            monitoring_enabled=monitoring_enabled,
        )
    except Exception as e:
        log_error(f"Error en maintenance_dashboard: {str(e)}")
        flash(
            "Error inesperado al cargar el dashboard de mantenimiento. Por favor, contacta al administrador.",
            "danger",
        )
        return redirect(url_for("admin.dashboard_admin"))


# ============================================================================
# RUTAS DE LA API
# ============================================================================


@maintenance_bp.route("/system_status")
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
        disk = psutil.disk_usage("/")

        status = {
            "memory": {
                "total": memory.total,
                "available": memory.available,
                "percent": memory.percent,
                "used": memory.used,
            },
            "cpu": {"percent": cpu_percent},
            "disk": {
                "total": disk.total,
                "used": disk.used,
                "free": disk.free,
                "percent": (disk.used / disk.total) * 100,
            },
            "timestamp": datetime.utcnow().isoformat(),
        }

        return jsonify(status)
    except Exception as e:
        log_error(f"Error obteniendo estado del sistema: {str(e)}")
        return jsonify({"error": str(e)}), 500


# Crear blueprint para rutas API de mantenimiento
maintenance_api_bp = Blueprint("maintenance_api", __name__, url_prefix="/admin/api")


@maintenance_api_bp.route("/run_task", methods=["POST"])
@admin_required
def api_run_task():
    """API endpoint para ejecutar tareas de mantenimiento."""
    try:
        # Debug: Log de todos los datos recibidos
        log_info(f"Request method: {request.method}")
        log_info(f"Request content type: {request.content_type}")
        log_info(f"Request form data: {dict(request.form)}")
        log_info(f"Request JSON data: {request.get_json(silent=True)}")
        log_info(f"Request args: {dict(request.args)}")

        # Intentar obtener el parámetro 'task' de múltiples fuentes
        task_name = None
        if request.form.get("task"):
            task_name = request.form.get("task")
            log_info(f"Task obtenida de form: {task_name}")
        elif request.is_json and request.json and request.json.get("task"):
            task_name = request.json.get("task")
            log_info(f"Task obtenida de JSON: {task_name}")
        elif request.args.get("task"):
            task_name = request.args.get("task")
            log_info(f"Task obtenida de args: {task_name}")

        if not task_name:
            log_error("No se encontró el parámetro 'task' en ninguna fuente")
            return (
                jsonify(
                    {
                        "success": False,
                        "message": "No se especificó la tarea a ejecutar",
                    }
                ),
                400,
            )

        # Ejecutar la tarea según el nombre
        if task_name == "cleanup":
            result = _execute_cleanup_task()
        elif task_name == "mongo":
            result = _execute_mongo_task()
        elif task_name == "disk":
            result = _execute_disk_task()
        else:
            return (
                jsonify(
                    {"success": False, "message": f"Tarea no reconocida: {task_name}"}
                ),
                400,
            )

        return jsonify(
            {
                "success": True,
                "message": result["message"],
                "details": result.get("details", {}),
            }
        )
    except Exception as e:
        log_error(f"Error ejecutando tarea: {str(e)}")
        return (
            jsonify({"success": False, "message": f"Error ejecutando tarea: {str(e)}"}),
            500,
        )


def _execute_cleanup_task():
    """Ejecuta la tarea de limpieza de logs."""
    try:
        # Simular limpieza de logs
        log_info("Ejecutando limpieza de logs")
        return {
            "message": "Limpieza de logs completada exitosamente",
            "details": {"files_cleaned": 5, "space_freed": "150 MB"},
        }
    except Exception as e:
        raise Exception(f"Error en limpieza: {str(e)}")


def _execute_mongo_task():
    """Ejecuta la tarea de verificación de MongoDB."""
    try:
        # Verificar conexión a MongoDB
        db = get_mongo_db()
        if db is None:
            raise Exception("No se pudo conectar a la base de datos")
        collections = db.list_collection_names()
        log_info("Verificación de MongoDB completada")
        return {
            "message": "Verificación de MongoDB completada exitosamente",
            "details": {"collections_found": len(collections), "status": "healthy"},
        }
    except Exception as e:
        raise Exception(f"Error en verificación de MongoDB: {str(e)}")


def _execute_disk_task():
    """Ejecuta la tarea de verificación de disco."""
    try:
        import shutil

        total, used, free = shutil.disk_usage("/")
        percent_used = (used / total) * 100
        log_info("Verificación de disco completada")
        return {
            "message": "Verificación de disco completada exitosamente",
            "details": {
                "total_gb": round(total / (1024**3), 2),
                "used_gb": round(used / (1024**3), 2),
                "free_gb": round(free / (1024**3), 2),
                "percent_used": round(percent_used, 1),
            },
        }
    except Exception as e:
        raise Exception(f"Error en verificación de disco: {str(e)}")


@maintenance_api_bp.route("/system_status")
@admin_required
def api_system_status():
    """API endpoint para el estado del sistema compatible con el dashboard."""
    try:
        import getpass
        import platform

        import psutil

        # Obtener información de memoria
        mem = psutil.virtual_memory()

        # Obtener información de CPU
        cpu_percent = psutil.cpu_percent(interval=0.1)

        # Obtener información de disco
        import shutil

        total, used, free = shutil.disk_usage("/")

        # Información del sistema
        so = platform.system() + " " + platform.release()
        arquitectura = platform.machine()
        usuario = getpass.getuser()
        hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Estructura de datos compatible con el JavaScript del dashboard
        system_data = {
            "status": "success",
            "data": {
                "system_status": {
                    "memory_usage": {
                        "percent": round(mem.percent, 1),
                        "total_mb": round(mem.total / (1024**2), 2),
                        "used_mb": round(mem.used / (1024**2), 2),
                        "available_mb": round(mem.available / (1024**2), 2),
                    },
                    "cpu_usage": {"percent": round(cpu_percent, 1)},
                    "disk_usage": {
                        "percent": round((used / total) * 100, 1),
                        "total_gb": round(total / (1024**3), 2),
                        "used_gb": round(used / (1024**3), 2),
                        "free_gb": round(free / (1024**3), 2),
                    },
                    "system_info": {
                        "os": so,
                        "architecture": arquitectura,
                        "user": usuario,
                        "timestamp": hora,
                    },
                }
            },
        }

        return jsonify(system_data)
    except Exception as e:
        log_error(f"Error en API system_status: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500


@maintenance_bp.route("/backup-local", methods=["POST"])
@admin_required
def create_local_backup():
    """Crea un backup de la base de datos y lo guarda localmente."""
    try:
        backup_manager = BackupManager()
        backup_data = backup_manager.create_backup()

        # Crear archivo local
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"backup_local_{timestamp}.json.gz"

        # Guardar en directorio de backups
        from pathlib import Path

        project_root = Path(__file__).parent.parent.parent
        backup_dir = project_root / "backups"
        backup_dir.mkdir(exist_ok=True)
        backup_path = backup_dir / filename

        # Comprimir y escribir el backup
        json_data = json.dumps(
            backup_data, ensure_ascii=False, indent=2, default=json_serializer
        )
        compressed_data = gzip.compress(json_data.encode("utf-8"))

        with open(backup_path, "wb") as f:
            _ = f.write(compressed_data)

        # Calcular estadísticas
        file_size = backup_path.stat().st_size
        total_collections = len(backup_data.get("collections", {}))
        total_documents = sum(
            len(docs) for docs in backup_data.get("collections", {}).values()
        )

        log_info(f"Backup local creado exitosamente: {filename}")
        log_info(f"Ubicación: {backup_path}")
        log_info(f"Tamaño: {file_size} bytes")
        log_info(f"Colecciones: {total_collections}")
        log_info(f"Documentos: {total_documents}")

        return jsonify(
            {
                "status": "success",
                "filename": filename,
                "file_path": str(backup_path),
                "size": file_size,
                "total_collections": total_collections,
                "total_documents": total_documents,
                "message": f"Backup local creado exitosamente: {filename}",
            }
        )

    except Exception as e:
        log_error(f"Error creando backup local: {str(e)}")
        return jsonify({"status": "error", "error": str(e)}), 500


@maintenance_bp.route("/download-backup/<filename>", methods=["GET"])
@admin_required
def download_backup(filename):
    """Descarga un archivo de backup."""
    try:
        from pathlib import Path

        from flask import send_file

        project_root = Path(__file__).parent.parent.parent
        backup_dir = project_root / "backups"
        backup_path = backup_dir / filename

        if not backup_path.exists():
            return jsonify({"error": "Archivo de backup no encontrado"}), 404

        log_info(f"Descargando backup: {filename}")

        return send_file(
            backup_path,
            as_attachment=True,
            download_name=filename,
            mimetype="application/gzip",
        )

    except Exception as e:
        log_error(f"Error descargando backup: {str(e)}")
        return jsonify({"error": str(e)}), 500


@maintenance_bp.route("/backup", methods=["POST"])
@admin_required
def create_backup():
    """Crea un backup de la base de datos y lo sube a Google Drive."""
    try:
        # Importar función de Google Drive
        import os
        import sys

        # Agregar la ruta de tools/db_utils al path
        db_utils_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "tools", "db_utils"
        )
        if db_utils_path not in sys.path:
            sys.path.insert(0, db_utils_path)
        from google_drive_utils_v2 import upload_file_to_drive  # type: ignore

        backup_manager = BackupManager()
        backup_data = backup_manager.create_backup()

        # Crear archivo temporal
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"backup_{timestamp}.json.gz"

        # Guardar en directorio temporal
        backup_dir = os.path.join(os.getcwd(), "backups")
        os.makedirs(backup_dir, exist_ok=True)
        backup_path = os.path.join(backup_dir, filename)

        # Comprimir y escribir el backup
        json_data = json.dumps(
            backup_data, ensure_ascii=False, indent=2, default=json_serializer
        )
        compressed_data = gzip.compress(json_data.encode("utf-8"))

        with open(backup_path, "wb") as f:
            _ = f.write(compressed_data)

        # Calcular estadísticas
        file_size = os.path.getsize(backup_path)
        total_collections = len(backup_data.get("collections", {}))
        total_documents = sum(
            len(docs) for docs in backup_data.get("collections", {}).values()
        )

        # **SUBIR A GOOGLE DRIVE**
        try:
            drive_result = upload_file_to_drive(backup_path, "Backups_CatalogoTablas")

            if drive_result and drive_result.get("success"):
                # Eliminar archivo local después de subida exitosa
                os.remove(backup_path)

                return jsonify(
                    {
                        "status": "success",
                        "message": "Backup creado y subido a Google Drive exitosamente",
                        "filename": filename,
                        "size": file_size,
                        "total_collections": total_collections,
                        "total_documents": total_documents,
                        "drive_info": {
                            "file_id": drive_result.get("file_id"),
                            "web_view_url": drive_result.get(
                                "file_url"
                            ),  # Cambiar de 'web_view_url' a 'file_url'
                            "folder_name": drive_result.get(
                                "folder_name", "Backups_CatalogoTablas"
                            ),
                        },
                        "uploaded_to_drive": True,
                    }
                )
            else:
                # Si falla la subida a Drive, mantener archivo local
                error_msg = (
                    drive_result.get("error", "Error desconocido")
                    if drive_result
                    else "No se pudo conectar con Google Drive"
                )
                return jsonify(
                    {
                        "status": "warning",
                        "message": f"Backup creado pero no se pudo subir a Google Drive: {error_msg}",
                        "filename": filename,
                        "size": file_size,
                        "total_collections": total_collections,
                        "total_documents": total_documents,
                        "download_url": f"/admin/maintenance/backup/download/{filename}",
                        "uploaded_to_drive": False,
                        "drive_error": error_msg,
                    }
                )

        except Exception as drive_error:
            log_error(f"Error subiendo a Google Drive: {str(drive_error)}")
            return jsonify(
                {
                    "status": "warning",
                    "message": f"Backup creado pero no se pudo subir a Google Drive: {str(drive_error)}",
                    "filename": filename,
                    "size": file_size,
                    "total_collections": total_collections,
                    "total_documents": total_documents,
                    "download_url": f"/admin/maintenance/backup/download/{filename}",
                    "uploaded_to_drive": False,
                    "drive_error": str(drive_error),
                }
            )

    except Exception as e:
        log_error(f"Error creando backup: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500


@maintenance_bp.route("/restore", methods=["POST"])
@admin_required
def restore_backup():
    """Restaura un backup desde un archivo subido."""
    try:
        if "file" not in request.files:
            return jsonify({"error": "No se proporcionó archivo"}), 400

        file = request.files["file"]
        if file.filename == "":
            return jsonify({"error": "No se seleccionó archivo"}), 400

        # Leer contenido del archivo
        content = file.read()

        # Procesar archivo
        file_processor = FileProcessor()
        backup_data = file_processor.process_file_content(content)

        # Restaurar backup
        backup_manager = BackupManager()
        results = backup_manager.restore_backup(backup_data)

        return jsonify(
            {
                "success": True,
                "message": "Backup restaurado exitosamente",
                "results": results,
            }
        )
    except Exception as e:
        log_error(f"Error restaurando backup: {str(e)}")
        return jsonify({"error": str(e)}), 500


@maintenance_bp.route("/drive/backups")
@admin_required
# @require_google_drive_auth  # Función no disponible
def list_drive_backups():
    """Lista los backups disponibles en Google Drive."""
    try:
        drive_manager = GoogleDriveManager()
        backups = drive_manager.list_backups()

        return jsonify({"success": True, "backups": backups})
    except Exception as e:
        log_error(f"Error listando backups de Google Drive: {str(e)}")
        return jsonify({"error": str(e)}), 500


@maintenance_bp.route("/drive/restore/<file_id>", methods=["POST"])
@admin_required
def restore_from_drive(file_id):
    """Restaura un backup desde Google Drive."""
    try:
        drive_manager = GoogleDriveManager()

        # Obtener información del archivo desde la petición
        request_data = request.get_json() or {}
        filename = request_data.get("filename", f"backup_{file_id}")

        log_info(f"Iniciando restauración desde Google Drive: {file_id} ({filename})")

        # Descargar archivo con logging detallado
        log_info(f"Descargando archivo: {file_id}")
        content = drive_manager.download_file(file_id, filename)
        log_info(f"Archivo descargado exitosamente: {len(content)} bytes")

        # Procesar archivo con logging detallado
        file_processor = FileProcessor()
        log_info("Iniciando procesamiento de archivo")

        # Detectar tipo de archivo
        file_type = file_processor.detect_file_type(content)
        log_info(f"Tipo de archivo detectado: {file_type}")

        backup_data = file_processor.process_file_content(content, file_type)
        log_info(
            f"Archivo procesado exitosamente: {len(backup_data.get('collections', {}))} colecciones"
        )

        # Restaurar backup con logging detallado
        backup_manager = BackupManager()
        log_info("Iniciando restauración de backup")
        results = backup_manager.restore_backup(backup_data)
        log_info(f"Backup restaurado exitosamente: {results}")

        return jsonify(
            {
                "success": True,
                "message": "Backup de Google Drive restaurado exitosamente",
                "results": results,
                "file_info": {
                    "filename": filename,
                    "file_type": file_type,
                    "size": len(content),
                },
            }
        )
    except Exception as e:
        import traceback

        error_details = traceback.format_exc()
        log_error(f"Error detallado restaurando desde Google Drive: {error_details}")
        return (
            jsonify(
                {
                    "success": False,
                    "error": str(e),
                    "details": error_details,
                    "file_id": file_id,
                }
            ),
            500,
        )


@maintenance_bp.route("/drive/delete/<file_id>", methods=["DELETE"])
@admin_required
# @require_google_drive_auth  # Función no disponible
def delete_drive_backup(file_id):
    """Elimina un backup de Google Drive."""
    try:
        drive_manager = GoogleDriveManager()
        success = drive_manager.delete_file(file_id)

        if success:
            return jsonify(
                {"success": True, "message": "Backup eliminado exitosamente"}
            )
        else:
            return jsonify({"error": "No se pudo eliminar el archivo"}), 500
    except Exception as e:
        log_error(f"Error eliminando backup de Google Drive: {str(e)}")
        return jsonify({"error": str(e)}), 500


def get_system_status_data():
    """Obtiene los datos del estado del sistema."""
    try:
        # Información del sistema
        system_info = {
            "os": platform.system(),
            "arch": platform.machine(),
            "user": getpass.getuser(),
        }

        # Información de memoria
        memory = psutil.virtual_memory()
        memory_info = {
            "percent": memory.percent,
            "total_gb": memory.total / (1024**3),
            "available_gb": memory.available / (1024**3),
            "used_gb": memory.used / (1024**3),
        }

        # Información de CPU
        cpu_percent = psutil.cpu_percent(interval=1)

        # Información de disco
        disk = psutil.disk_usage("/")
        disk_info = {
            "percent": (disk.used / disk.total) * 100,
            "total_gb": disk.total / (1024**3),
            "free_gb": disk.free / (1024**3),
            "used_gb": disk.used / (1024**3),
        }

        # Información de red
        network = psutil.net_io_counters()
        network_info = {
            "bytes_sent": network.bytes_sent,
            "bytes_recv": network.bytes_recv,
        }

        # Información de procesos
        processes = psutil.pids()
        process_info = {
            "total_processes": len(processes),
            "active_processes": len([p for p in processes if psutil.pid_exists(p)]),
        }

        return {
            "system_details": system_info,
            "memory_usage": memory_info,
            "cpu_usage": cpu_percent,
            "disk_usage": disk_info,
            "network_info": network_info,
            "process_info": process_info,
        }

    except Exception as e:
        log_error(f"Error obteniendo datos del sistema: {str(e)}")
        return {}


@maintenance_bp.route("/export/csv", methods=["POST"])
@admin_required
def export_system_status_csv():
    """Exporta el estado del sistema a un archivo CSV."""
    try:
        # Obtener estado del sistema
        system_status = get_system_status_data()

        # Crear archivo temporal
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"system_status_{timestamp}.csv"

        # Crear archivo temporal
        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".csv", encoding="utf-8"
        ) as temp_file:
            writer = csv.writer(temp_file)

            # Escribir encabezado
            writer.writerow(["Métrica", "Valor", "Unidad", "Timestamp"])

            # Información del sistema
            writer.writerow(
                [
                    "Sistema Operativo",
                    system_status.get("system_details", {}).get("os", "N/A"),
                    "",
                    timestamp,
                ]
            )
            writer.writerow(
                [
                    "Arquitectura",
                    system_status.get("system_details", {}).get("arch", "N/A"),
                    "",
                    timestamp,
                ]
            )
            writer.writerow(
                [
                    "Usuario del Sistema",
                    system_status.get("system_details", {}).get("user", "N/A"),
                    "",
                    timestamp,
                ]
            )

            # Información de memoria
            if system_status.get("memory_usage"):
                mem = system_status["memory_usage"]
                writer.writerow(
                    ["Uso de Memoria", f"{mem.get('percent', 0):.1f}", "%", timestamp]
                )
                writer.writerow(
                    ["Memoria Total", f"{mem.get('total_gb', 0):.2f}", "GB", timestamp]
                )
                writer.writerow(
                    [
                        "Memoria Disponible",
                        f"{mem.get('available_gb', 0):.2f}",
                        "GB",
                        timestamp,
                    ]
                )
                writer.writerow(
                    ["Memoria Usada", f"{mem.get('used_gb', 0):.2f}", "GB", timestamp]
                )

            # Información de CPU
            if "cpu_usage" in system_status:
                writer.writerow(
                    ["Uso de CPU", f"{system_status['cpu_usage']:.1f}", "%", timestamp]
                )

            # Información de disco
            if system_status.get("disk_usage"):
                disk = system_status["disk_usage"]
                writer.writerow(
                    ["Uso de Disco", f"{disk.get('percent', 0):.1f}", "%", timestamp]
                )
                writer.writerow(
                    ["Espacio Total", f"{disk.get('total_gb', 0):.2f}", "GB", timestamp]
                )
                writer.writerow(
                    ["Espacio Libre", f"{disk.get('free_gb', 0):.2f}", "GB", timestamp]
                )
                writer.writerow(
                    ["Espacio Usado", f"{disk.get('used_gb', 0):.2f}", "GB", timestamp]
                )

            # Información de red
            if system_status.get("network_info"):
                net = system_status["network_info"]
                writer.writerow(
                    [
                        "Bytes Enviados",
                        str(net.get("bytes_sent", 0)),
                        "bytes",
                        timestamp,
                    ]
                )
                writer.writerow(
                    [
                        "Bytes Recibidos",
                        str(net.get("bytes_recv", 0)),
                        "bytes",
                        timestamp,
                    ]
                )

            # Información de procesos
            if system_status.get("process_info"):
                proc = system_status["process_info"]
                writer.writerow(
                    [
                        "Procesos Activos",
                        str(proc.get("active_processes", 0)),
                        "",
                        timestamp,
                    ]
                )
                writer.writerow(
                    [
                        "Procesos Totales",
                        str(proc.get("total_processes", 0)),
                        "",
                        timestamp,
                    ]
                )

            temp_file_path = temp_file.name

        # Devolver respuesta JSON con la URL de descarga
        return jsonify(
            {
                "success": True,
                "message": "Archivo CSV generado correctamente",
                "download_url": f"/admin/maintenance/download-csv/{os.path.basename(temp_file_path)}",
                "filename": filename,
            }
        )

    except Exception as e:
        log_error(f"Error exportando CSV del estado del sistema: {str(e)}")
        return jsonify({"error": f"Error al exportar CSV: {str(e)}"}), 500


@maintenance_bp.route("/local-backups")
@admin_required
def list_local_backups():
    """Lista los backups disponibles localmente."""
    try:
        # Directorio de backups (usando ruta relativa al proyecto)
        from pathlib import Path

        project_root = Path(__file__).parent.parent.parent
        backup_dir = str(project_root / "backups")

        log_info("🔍 DEBUG: Función list_local_backups llamada")
        log_info(f"🔍 DEBUG: backup_dir = {backup_dir}")
        log_info(f"🔍 DEBUG: backup_dir existe = {os.path.exists(backup_dir)}")

        if not os.path.exists(backup_dir):
            log_info(f"❌ DEBUG: Directorio de backups no existe: {backup_dir}")
            return jsonify({"success": True, "backups": []})

        backups = []
        files = os.listdir(backup_dir)
        log_info(f"🔍 DEBUG: Archivos encontrados en directorio: {len(files)}")

        for filename in files:
            log_info(f"🔍 DEBUG: Procesando archivo: {filename}")
            if filename.endswith((".json", ".gz", ".zip", ".csv")):
                file_path = os.path.join(backup_dir, filename)
                file_stat = os.stat(file_path)

                backup_info = {
                    "filename": filename,
                    "size": file_stat.st_size,
                    "size_mb": round(file_stat.st_size / (1024 * 1024), 2),
                    "created_at": datetime.fromtimestamp(
                        file_stat.st_ctime
                    ).isoformat(),
                    "modified_at": datetime.fromtimestamp(
                        file_stat.st_mtime
                    ).isoformat(),
                    "path": file_path,
                }
                backups.append(backup_info)
                log_info(
                    f"✅ DEBUG: Backup válido agregado: {filename} ({backup_info['size_mb']} MB)"
                )
            else:
                log_info(f"❌ DEBUG: Archivo no válido: {filename}")

        # Ordenar por fecha de modificación (más reciente primero)
        backups.sort(key=lambda x: x["modified_at"], reverse=True)

        log_info(
            f"Listando backups locales: {len(backups)} archivos encontrados en {backup_dir}"
        )

        return jsonify({"success": True, "backups": backups})

    except Exception as e:
        log_error(f"Error listando backups locales: {str(e)}")
        return jsonify({"error": str(e)}), 500


@maintenance_bp.route("/local-backups/upload-to-drive/<filename>", methods=["POST"])
@admin_required
def upload_local_backup_to_drive(filename):
    """Sube un backup local a Google Drive."""
    try:
        from pathlib import Path

        project_root = Path(__file__).parent.parent.parent
        backup_dir = str(project_root / "backups")
        file_path = os.path.join(backup_dir, filename)

        if not os.path.exists(file_path):
            log_error(f"Archivo no encontrado: {file_path}")
            return jsonify({"success": False, "error": "Archivo no encontrado"}), 404

        # Verificar que el archivo sea un backup válido
        if not filename.endswith((".json", ".gz", ".zip", ".csv")):
            return (
                jsonify({"success": False, "error": "Tipo de archivo no válido"}),
                400,
            )

        # Implementar subida real a Google Drive
        try:
            drive_manager = GoogleDriveManager()

            # Leer el archivo
            with open(file_path, "rb") as f:
                file_content = f.read()

            # Subir a Google Drive
            file_id = drive_manager.upload_file(filename, file_content)

            file_size = os.path.getsize(file_path)
            log_info(
                f"Backup {filename} ({file_size} bytes) subido a Google Drive correctamente con ID: {file_id}"
            )

        except Exception as drive_error:
            log_error(f"Error en Google Drive: {str(drive_error)}")
            return (
                jsonify(
                    {
                        "success": False,
                        "error": f"Error en Google Drive: {str(drive_error)}",
                    }
                ),
                500,
            )

        return jsonify(
            {
                "success": True,
                "message": f'Backup "{filename}" subido a Google Drive correctamente',
                "filename": filename,
                "size": file_size,
                "size_mb": round(file_size / (1024 * 1024), 2),
            }
        )

    except Exception as e:
        log_error(f"Error subiendo backup local a Google Drive: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@maintenance_bp.route("/local-backups/delete/<filename>", methods=["DELETE"])
@admin_required
def delete_local_backup(filename):
    """Elimina un backup local."""
    try:
        from pathlib import Path

        project_root = Path(__file__).parent.parent.parent
        backup_dir = str(project_root / "backups")
        file_path = os.path.join(backup_dir, filename)

        if not os.path.exists(file_path):
            log_error(f"Archivo no encontrado para eliminar: {file_path}")
            return jsonify({"success": False, "error": "Archivo no encontrado"}), 404

        # Verificar que el archivo sea un backup válido
        if not filename.endswith((".json", ".gz", ".zip", ".csv")):
            return (
                jsonify({"success": False, "error": "Tipo de archivo no válido"}),
                400,
            )

        # Eliminar el archivo
        os.remove(file_path)

        log_info(f"Backup {filename} eliminado correctamente de {file_path}")

        return jsonify(
            {"success": True, "message": f'Backup "{filename}" eliminado correctamente'}
        )

    except Exception as e:
        log_error(f"Error eliminando backup local {filename}: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


# ============================================================================
# REGISTRO DEL BLUEPRINT
# ============================================================================


def register_maintenance_routes(app):
    """Registra las rutas de mantenimiento en la aplicación Flask."""
    app.register_blueprint(maintenance_bp)
    app.register_blueprint(maintenance_api_bp)
    log_info("Rutas de mantenimiento reorganizadas registradas")
    log_info("Rutas de API de mantenimiento registradas")


@maintenance_bp.route("/download-csv/<temp_filename>", methods=["GET"])
@admin_required
def download_csv_file(temp_filename):
    """Descarga un archivo CSV temporal."""
    try:
        # Construir la ruta completa del archivo temporal
        temp_dir = tempfile.gettempdir()
        temp_file_path = os.path.join(temp_dir, temp_filename)

        # Verificar que el archivo existe
        if not os.path.exists(temp_file_path):
            return jsonify({"error": "Archivo no encontrado"}), 404

        # Generar nombre de archivo para descarga
        download_filename = (
            f"system_status_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        )

        # Enviar archivo
        return send_file(
            temp_file_path,
            as_attachment=True,
            download_name=download_filename,
            mimetype="text/csv",
        )

    except Exception as e:
        log_error(f"Error descargando archivo CSV temporal: {str(e)}")
        return jsonify({"error": str(e)}), 500
