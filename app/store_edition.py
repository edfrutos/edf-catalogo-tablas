"""Comportamiento propio de la edición de tienda (``EDF_EDITION=store``).

Sin cuentas: la app abre directamente con un único usuario local, creado la primera vez
en el almacén SQLite. Este módulo solo se carga en la edición de tienda; la edición
estándar no lo importa.

Seguridad. Flask escucha en 127.0.0.1 y CSRF está desactivado en la app, así que una
página web cualquiera del navegador del usuario podría enviar peticiones al puerto
local. Por eso NO se crea ninguna sesión por iniciativa del servidor:

* la sesión solo se abre con la URL de entrada que lleva el token de arranque, que se
  genera en cada ejecución y solo conoce el launcher (mismo proceso);
* se rechaza cualquier petición cuyo ``Host`` no sea local (DNS rebinding);
* las peticiones que modifican datos se rechazan si vienen de otro origen
  (``Origin`` / ``Sec-Fetch-Site``).
"""

from __future__ import annotations

import datetime as _dt
import hmac
import logging
import secrets
import threading
from urllib.parse import urlsplit

from flask import abort, redirect, request, session

logger = logging.getLogger(__name__)

LOCAL_EMAIL = "local@tablateca.local"
LOCAL_USERNAME = "tablateca"
LOCAL_NAME = "Usuario local"

ENTER_PATH = "/_store/enter"
# Token de esta ejecución: solo lo conoce el launcher (mismo proceso que Flask).
LAUNCH_TOKEN = secrets.token_urlsafe(32)

LOCAL_HOSTS = {"127.0.0.1", "localhost", "::1"}
SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}

# Pantallas de cuentas que no existen en la edición de tienda.
ACCOUNT_PATHS = (
    "/login",
    "/register",
    "/registro",
    "/welcome",
    "/forgot_password",
    "/reset_password",
    "/auth/login",
    "/auth/register",
    "/auth/forgot_password",
    "/auth/reset_password",
)

_lock = threading.Lock()


LAUNCH_HEADER = "X-EDF-Launch"


def launch_headers() -> dict:
    """Cabecera que usa el launcher para sus descargas (urllib no lleva la cookie)."""
    return {LAUNCH_HEADER: LAUNCH_TOKEN}


def entry_path() -> str:
    """Ruta de entrada con el token de esta ejecución (la usa el launcher)."""
    return f"{ENTER_PATH}?t={LAUNCH_TOKEN}"


def ensure_local_user(db) -> dict:
    """Devuelve el usuario local, creándolo si no existe."""
    users = db["users"]
    with _lock:
        user = users.find_one({"email": LOCAL_EMAIL})
        if user is None:
            now = _dt.datetime.utcnow()
            doc = {
                "email": LOCAL_EMAIL,
                "username": LOCAL_USERNAME,
                "nombre": LOCAL_NAME,
                "name": LOCAL_NAME,
                # Sin contraseña utilizable: no hay inicio de sesión por formulario.
                "password": "!",
                "role": "admin",
                "active": True,
                "is_active": True,
                "created_at": now,
            }
            users.insert_one(doc)
            user = doc
            logger.info("Usuario local creado")
    return user


def _open_local_session(db) -> None:
    user = ensure_local_user(db)
    session["user_id"] = str(user["_id"])
    session["email"] = user["email"]
    session["username"] = user.get("username", "")
    session["nombre"] = user.get("nombre", "")
    session["role"] = user.get("role", "admin")
    session["logged_in"] = True
    session["edf_store"] = True
    session.permanent = True
    try:
        from flask_login import login_user

        from app.models.user import User

        login_user(User(user))
    except Exception as exc:  # flask_login es accesorio: la sesión ya basta
        logger.debug("login_user omitido: %s", exc)


def _host_is_local() -> bool:
    try:
        host = urlsplit("//" + (request.host or "")).hostname
    except ValueError:
        return False
    return host in LOCAL_HOSTS


def _cross_origin_write() -> bool:
    """True si una petición que modifica datos no viene de este mismo origen."""
    if request.method in SAFE_METHODS:
        return False
    site = request.headers.get("Sec-Fetch-Site")
    if site is not None and site not in ("same-origin", "none"):
        return True
    origin = request.headers.get("Origin")
    if origin is not None:
        try:
            return urlsplit(origin).netloc != request.host
        except ValueError:
            return True
    return False


# Paneles que no existen en la edición de tienda (sin cuentas, sin servidor, sin Drive/S3):
# se ocultan del menú y además responden 404 aunque se escriba la URL.
BLOCKED_PREFIXES = (
    # usuarios y contraseñas
    "/admin/usuarios",
    "/admin/assign-temp-password",
    "/admin/password-management",
    "/admin/bulk_user_action",
    "/admin/cleanup_resets",
    "/admin/catalogos-usuario",
    "/usuarios",
    "/perfil",
    "/editar_perfil",
    "/logout",
    "/login_pywebview",
    "/forgot-password",
    "/reset-password",
    "/temp-password-reset",
    # base de datos, copias remotas, Drive y S3
    "/admin/db",
    "/admin/api/",
    "/admin/backups",
    "/admin/drive-backups",
    "/admin/gdrive_upload_test",
    "/admin/reset_gdrive_token",
    "/admin/restore-drive-backup",
    "/admin/restore-local-backup",
    "/admin/s3",
    "/admin/generate-presigned-url",
    "/api/config",
    # sistema, mantenimiento, logs y herramientas
    "/admin/maintenance",
    "/admin/logs",
    "/admin/system",
    "/admin/tools",
    "/admin/scripts-tools-api",
    "/admin/notification-settings",
    "/admin/test-modal-functions",
    "/admin/truncate_log",
    "/admin/delete-temp-files",
    "/api/maintenance",
    "/api/system",
    # desarrollo
    "/dev-template",
    "/test_session",
)
# Exportación de catálogos: sí disponible (CSV/JSON y copia ZIP); el resto de /admin/backup/ no.
DOWNLOAD_BACKUP_PATHS = ("/admin/backup/csv", "/admin/backup/json", "/admin/backup/zip")
ALLOWED_BACKUP_PATHS = DOWNLOAD_BACKUP_PATHS + ("/admin/backup/importar",)


def is_blocked_path(path: str) -> bool:
    """True si la ruta pertenece a un panel que no existe en la edición de tienda."""
    path = path or "/"
    if path.startswith("/admin/backup/") or path == "/admin/backup":
        return path.rstrip("/") not in ALLOWED_BACKUP_PATHS
    return any(path == p.rstrip("/") or path.startswith(p) for p in BLOCKED_PREFIXES)


def _denied():
    return (
        "<h1>Acceso denegado</h1><p>Abre TablaTeca desde su propia ventana.</p>",
        403,
    )


def _launch_header_ok() -> bool:
    value = request.headers.get(LAUNCH_HEADER, "")
    return bool(value) and hmac.compare_digest(value.encode(), LAUNCH_TOKEN.encode())


def _has_local_session() -> bool:
    return bool(
        session.get("logged_in") and session.get("user_id") and session.get("edf_store")
    )


def init_store_edition(app) -> None:
    @app.before_request
    def _store_gate():
        if not _host_is_local() or _cross_origin_write():
            return _denied()

        path = request.path or "/"
        if path.startswith("/static/"):
            return None

        if path == ENTER_PATH:
            token = request.args.get("t", "")
            if not hmac.compare_digest(token.encode(), LAUNCH_TOKEN.encode()):
                return _denied()
            from app.database import get_mongo_db

            db = get_mongo_db()
            if db is None:
                return _denied()
            _open_local_session(db)
            return redirect("/")

        if request.method in ("GET", "HEAD") and _launch_header_ok():
            # Descarga iniciada por el propio launcher (solo lectura). Las copias CSV/JSON
            # pasan por rutas con sesión: el launcher las pide sin cookie, así que se abre
            # la sesión local (mismo token secreto que /_store/enter, solo en loopback).
            if path.rstrip("/") in DOWNLOAD_BACKUP_PATHS and not _has_local_session():
                from app.database import get_mongo_db

                db = get_mongo_db()
                if db is None:
                    return _denied()
                _open_local_session(db)
            return None

        if not _has_local_session():
            return _denied()

        if path.rstrip("/") in ACCOUNT_PATHS:
            return redirect("/")
        if is_blocked_path(path):
            abort(404)
        return None

    from app.store_backup_routes import store_backup_bp

    app.register_blueprint(store_backup_bp)
    app.config["EDF_EDITION"] = "store"
    # Las plantillas ocultan los paneles que no existen en la tienda.
    app.jinja_env.globals["is_store_edition"] = True

    from app.store_settings_routes import store_settings_bp

    app.register_blueprint(store_settings_bp)
