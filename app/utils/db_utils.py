# Script: db_utils.py
# Descripción: [Explica brevemente qué hace el script]
# Uso: python3 db_utils.py [opciones]
# Requiere: [librerías externas, si aplica]
# Variables de entorno: [si aplica]
# Autor: EDF Developer - 2025-05-28

from flask import current_app, g


def get_db():
    db = getattr(g, "db", None)
    if db is None:
        # Intentar forzar la inicialización si no existe
        try:
            from app.database import get_mongo_db, initialize_db

            # Intentar reconectar
            if initialize_db(current_app):
                db = get_mongo_db()
                if db is not None:
                    g.db = db

                else:
                    current_app.logger.error(
                        "[get_db] Reconexión fallida: get_mongo_db() devolvió None."
                    )
            else:
                current_app.logger.error(
                    "[get_db] Reconexión fallida: initialize_db() devolvió False."
                )
        except Exception as e:
            current_app.logger.error(
                f"[get_db] Error crítico al intentar reconectar a la base de datos: {e}"
            )
            db = None
    return db


ALLOWED_EXTENSIONS = {
    "jpg",
    "jpeg",
    "png",
    "gif",
    "bmp",
    "svg",
    "webp",
    "avif",
    "tiff",
    "ico",
}


def allowed_image(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
