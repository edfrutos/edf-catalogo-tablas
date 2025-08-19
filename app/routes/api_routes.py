"""
Rutas de API - EDF CatálogoDeTablas
===================================

Endpoints de API críticos para la aplicación
"""

from flask import Blueprint, jsonify, request, current_app
from flask_login import login_required, current_user
from app.models.database import get_mongo_db
import os
import boto3
from datetime import datetime

# Crear blueprint
api_bp = Blueprint("api_routes", __name__, url_prefix="/api")


@api_bp.route("/health", methods=["GET"])
def health_check():
    """Health check de la aplicación y base de datos"""
    try:
        # Verificar conexión a MongoDB
        db = get_mongo_db()
        collections = db.list_collection_names()

        # Verificar configuración de AWS S3
        s3_enabled = False
        try:
            if current_app.config.get("AWS_ACCESS_KEY_ID") and current_app.config.get(
                "AWS_SECRET_ACCESS_KEY"
            ):
                s3_enabled = True
        except Exception:
            pass

        # Verificar configuración de Google Drive
        drive_enabled = False
        try:
            # Para aplicaciones empaquetadas, buscar en múltiples ubicaciones
            if getattr(sys, "frozen", False):
                # Aplicación empaquetada - buscar en el bundle
                app_dir = os.path.dirname(sys.executable)
                credentials_paths = [
                    os.path.join(
                        app_dir,
                        "..",
                        "Frameworks",
                        "tools",
                        "db_utils",
                        "credentials.json",
                    ),
                    os.path.join(app_dir, "tools", "db_utils", "credentials.json"),
                ]
            else:
                # Aplicación normal
                credentials_paths = [
                    os.path.join(
                        current_app.root_path,
                        "..",
                        "tools",
                        "db_utils",
                        "credentials.json",
                    )
                ]

            # Verificar si existe en alguna de las ubicaciones
            for credentials_path in credentials_paths:
                if os.path.exists(credentials_path):
                    drive_enabled = True
                    break
        except Exception:
            pass

        return (
            jsonify(
                {
                    "status": "healthy",
                    "timestamp": datetime.now().isoformat(),
                    "database": {
                        "status": "connected",
                        "collections_count": len(collections),
                    },
                    "services": {"aws_s3": s3_enabled, "google_drive": drive_enabled},
                    "version": "1.0.0",
                }
            ),
            200,
        )

    except Exception as e:
        return (
            jsonify(
                {
                    "status": "unhealthy",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat(),
                }
            ),
            500,
        )


@api_bp.route("/catalogs", methods=["GET"])
@login_required
def list_catalogs():
    """Listar catálogos del usuario"""
    try:
        db = get_mongo_db()
        catalogs = list(
            db.catalogs.find(
                {"owner_id": current_user.id},
                {
                    "_id": 0,
                    "name": 1,
                    "description": 1,
                    "created_at": 1,
                    "updated_at": 1,
                },
            )
        )

        return (
            jsonify(
                {"status": "success", "catalogs": catalogs, "count": len(catalogs)}
            ),
            200,
        )

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@api_bp.route("/maintenance/status", methods=["GET"])
@login_required
def maintenance_status():
    """Estado del sistema de mantenimiento"""
    try:
        # Verificar estado de directorios críticos
        critical_dirs = ["logs", "uploads", "static", "templates"]
        dir_status = {}

        for dir_name in critical_dirs:
            dir_path = os.path.join(current_app.root_path, "..", dir_name)
            dir_status[dir_name] = {
                "exists": os.path.exists(dir_path),
                "writable": (
                    os.access(dir_path, os.W_OK) if os.path.exists(dir_path) else False
                ),
            }

        # Verificar espacio en disco
        import shutil

        total, used, free = shutil.disk_usage(current_app.root_path)

        return (
            jsonify(
                {
                    "status": "success",
                    "maintenance": {
                        "directories": dir_status,
                        "disk_space": {
                            "total_gb": round(total / (1024**3), 2),
                            "used_gb": round(used / (1024**3), 2),
                            "free_gb": round(free / (1024**3), 2),
                            "usage_percent": round((used / total) * 100, 2),
                        },
                    },
                }
            ),
            200,
        )

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@api_bp.route("/config/s3", methods=["GET"])
@login_required
def s3_config():
    """Configuración de AWS S3"""
    try:
        config = {
            "enabled": bool(current_app.config.get("AWS_ACCESS_KEY_ID")),
            "bucket": current_app.config.get("AWS_S3_BUCKET"),
            "region": current_app.config.get("AWS_DEFAULT_REGION", "us-east-1"),
        }

        return jsonify({"status": "success", "s3_config": config}), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@api_bp.route("/config/drive", methods=["GET"])
@login_required
def drive_config():
    """Configuración de Google Drive"""
    try:
        credentials_path = os.path.join(
            current_app.root_path, "..", "tools", "db_utils", "credentials.json"
        )
        token_path = os.path.join(
            current_app.root_path, "..", "tools", "db_utils", "token.json"
        )

        config = {
            "enabled": os.path.exists(credentials_path),
            "credentials_file": os.path.exists(credentials_path),
            "token_file": os.path.exists(token_path),
        }

        return jsonify({"status": "success", "drive_config": config}), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@api_bp.route("/upload", methods=["POST"])
@login_required
def upload_file():
    """Endpoint para subida de archivos"""
    try:
        if "file" not in request.files:
            return (
                jsonify({"status": "error", "message": "No se proporcionó archivo"}),
                400,
            )

        file = request.files["file"]
        if file.filename == "":
            return (
                jsonify({"status": "error", "message": "No se seleccionó archivo"}),
                400,
            )

        # Aquí iría la lógica de subida de archivos
        # Por ahora solo devolvemos un mensaje de éxito

        return (
            jsonify(
                {
                    "status": "success",
                    "message": "Archivo recibido correctamente",
                    "filename": file.filename,
                }
            ),
            200,
        )

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
