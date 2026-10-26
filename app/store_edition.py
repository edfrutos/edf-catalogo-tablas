"""Comportamiento propio de la edición de tienda (``EDF_EDITION=store``).

Sin cuentas: la app abre directamente con un único usuario local, creado la primera vez
en el almacén SQLite. Este módulo solo se carga en la edición de tienda; la edición
estándar no lo importa.
"""

from __future__ import annotations

import datetime as _dt
import logging
import threading

from flask import redirect, request, session

logger = logging.getLogger(__name__)

LOCAL_EMAIL = "local@tablateca.local"
LOCAL_USERNAME = "tablateca"
LOCAL_NAME = "Usuario local"

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
    session.permanent = True
    try:
        from flask_login import login_user

        from app.models.user import User

        login_user(User(user))
    except Exception as exc:  # flask_login es accesorio: la sesión ya basta
        logger.debug("login_user omitido: %s", exc)


def init_store_edition(app) -> None:
    @app.before_request
    def _auto_login():
        path = request.path or "/"
        if path.startswith("/static/"):
            return None
        if path.rstrip("/") in ACCOUNT_PATHS:
            return redirect("/")
        if session.get("logged_in") and session.get("user_id"):
            return None
        from app.database import get_mongo_db

        db = get_mongo_db()
        if db is None:
            return None
        _open_local_session(db)
        return None

    app.config["EDF_EDITION"] = "store"
