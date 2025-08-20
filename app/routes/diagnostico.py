# app/routes/diagnostico.py

import json
import logging
import traceback
from datetime import datetime
from functools import wraps

from bson import ObjectId, json_util  # noqa: F401
from flask import Blueprint, current_app, g, jsonify, request, session, url_for

logger = logging.getLogger(__name__)
diagnostico_bp = Blueprint("diagnostico", __name__, url_prefix="/diagnostico")


# Función auxiliar para buscar usuarios
def find_user_by_email_or_name(identifier):
    try:
        # Obtener la colección de usuarios
        users_collection = getattr(g, "users_collection", None)
        if users_collection is None and hasattr(g, "mongo"):
            users_collection = g.mongo.db.users

        # Intentar buscar por email
        usuario = users_collection.find_one({"email": identifier})
        if usuario:
            return usuario

        # Intentar buscar por username
        usuario = users_collection.find_one({"username": identifier})
        if usuario:
            return usuario

        # Intentar buscar por nombre
        usuario = users_collection.find_one({"nombre": identifier})
        if usuario:
            return usuario

        return None
    except Exception as e:
        logger.error(f"Error buscando usuario: {str(e)}")
        return None


# Decorador para requerir autenticación
def auth_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session or not session.get("logged_in"):
            return jsonify(
                {
                    "status": "error",
                    "message": "Autenticación requerida",
                    "redirect": url_for("auth.login"),
                }
            ), 401
        return f(*args, **kwargs)

    return decorated_function


# Ruta principal de diagnóstico
@diagnostico_bp.route("/")
def diagnostico_home():
    """Página principal de diagnóstico"""
    # Añadir un valor de prueba a la sesión
    session["diagnostico_timestamp"] = datetime.utcnow().isoformat()
    session.modified = True

    return jsonify(
        {
            "status": "success",
            "message": "Diagnóstico de sesión",
            "endpoints": {
                "session": url_for("diagnostico.diagnostico_session"),
                "login_directo": url_for("diagnostico.login_directo"),
                "admin_check": url_for("diagnostico.admin_check"),
                "fix_session": url_for("diagnostico.fix_session"),
            },
        }
    )


# Ruta para diagnosticar la sesión
@diagnostico_bp.route("/session")
def diagnostico_session():
    """Muestra información sobre la sesión actual"""
    session_info = {
        "user_id": session.get("user_id"),
        "username": session.get("username"),
        "email": session.get("email"),
        "role": session.get("role"),
        "logged_in": session.get("logged_in"),
        "timestamp": datetime.utcnow().isoformat(),
        "cookie_name": current_app.config.get("SESSION_COOKIE_NAME"),
        "cookie_secure": current_app.config.get("SESSION_COOKIE_SECURE"),
        "session_lifetime": str(current_app.config.get("PERMANENT_SESSION_LIFETIME")),
        "request_cookies": {k: v for k, v in request.cookies.items()},
        "session_keys": list(session.keys()) if session else [],
        "full_session": dict(session),
    }

    # Añadir un valor de prueba a la sesión
    session["diagnostico_timestamp"] = datetime.utcnow().isoformat()
    session.modified = True

    # Registrar información para análisis
    logger.info(
        f"Diagnóstico de sesión solicitado: {json.dumps(session_info, default=str)}"
    )

    return jsonify(session_info)


# Ruta para acceso directo de administrador
@diagnostico_bp.route("/login_directo")
def login_directo():
    """Acceso directo para depuración"""
    try:
        # Buscar usuario admin
        usuario = find_user_by_email_or_name("admin@example.com")
        if not usuario:
            # Intentar buscar cualquier usuario con rol admin
            users_collection = getattr(g, "users_collection", None)
            if users_collection is None and hasattr(g, "mongo"):
                users_collection = g.mongo.db.users
            usuario = users_collection.find_one({"role": "admin"})

        if not usuario:
            from flask import abort

            abort(404, description="No se encontró usuario admin")  # noqa: F821

        # Establecer sesión
        session.clear()
        session.permanent = True
        session["user_id"] = str(usuario.get("_id", ""))
        session["email"] = usuario.get("email", "")
        session["username"] = (
            usuario.get("username") or usuario.get("nombre") or "admin"
        )
        session["role"] = "admin"
        session["logged_in"] = True
        session["login_time"] = datetime.utcnow().isoformat()
        session["client_ip"] = request.remote_addr
        session.modified = True

        # Registrar información para análisis
        logger.info(
            f"Acceso directo establecido para usuario: {session.get('username')} (ID: {session.get('user_id')})"
        )

        return jsonify(
            {
                "status": "success",
                "message": "Sesión de administrador establecida correctamente",
                "session": dict(session),
            }
        )

    except Exception as e:
        logger.error(f"Error en login_directo: {str(e)}\n{traceback.format_exc()}")
        from flask import abort

        abort(500, description=f"Error: {str(e)}")


# Ruta para verificar acceso de administrador
@diagnostico_bp.route("/admin_check")
@auth_required
def admin_check():
    """Verificar si el usuario tiene acceso de administrador"""
    if session.get("role") != "admin":
        return jsonify(
            {
                "status": "error",
                "message": "El usuario no tiene rol de administrador",
                "role": session.get("role"),
                "username": session.get("username"),
            }
        ), 403

    return jsonify(
        {
            "status": "success",
            "message": "El usuario tiene rol de administrador",
            "role": session.get("role"),
            "username": session.get("username"),
            "user_id": session.get("user_id"),
        }
    )


# Ruta para reparar la sesión
@diagnostico_bp.route("/fix_session")
def fix_session():
    """Intenta reparar problemas comunes de sesión"""
    try:
        # Verificar si hay información de usuario en la sesión
        user_id = session.get("user_id")
        if not user_id:
            return jsonify(
                {
                    "status": "error",
                    "message": "No hay usuario en la sesión para reparar",
                }
            )

        # Buscar el usuario en la base de datos
        users_collection = getattr(g, "users_collection", None)
        if users_collection is None and hasattr(g, "mongo"):
            users_collection = g.mongo.db.users

        try:
            usuario = users_collection.find_one({"_id": ObjectId(user_id)})
        except Exception as e:
            return jsonify(
                {"status": "error", "message": f"Error al buscar usuario: {str(e)}"}
            ), 500

        if not usuario:
            return jsonify(
                {
                    "status": "error",
                    "message": "Usuario no encontrado en la base de datos",
                }
            ), 404

        # Restaurar datos de sesión
        session["email"] = usuario.get("email", "")
        session["username"] = (
            usuario.get("username") or usuario.get("nombre") or "usuario"
        )
        session["role"] = usuario.get("role", "user")
        session["logged_in"] = True
        session["login_time"] = datetime.utcnow().isoformat()
        session["client_ip"] = request.remote_addr
        session.modified = True

        logger.info(
            f"Sesión reparada para usuario: {session.get('username')} (ID: {session.get('user_id')})"
        )

        return jsonify(
            {
                "status": "success",
                "message": "Sesión reparada correctamente",
                "session": dict(session),
            }
        )

    except Exception as e:
        logger.error(f"Error al reparar sesión: {str(e)}\n{traceback.format_exc()}")
        return jsonify({"status": "error", "message": f"Error: {str(e)}"}), 500
