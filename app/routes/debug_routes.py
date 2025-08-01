# app/routes/debug_routes.py

import logging
import json
from datetime import datetime
from flask import (
    Blueprint,
    jsonify,
    session,
    request,
    current_app,
    render_template,
    flash,
    redirect,
    url_for,
    g,
)
from bson import json_util  # noqa: F401

logger = logging.getLogger(__name__)
debug_bp = Blueprint("debug", __name__, url_prefix="/debug")


@debug_bp.route("/session")
def debug_session():
    """Ruta para depurar el estado actual de la sesión"""
    # Solo permitir acceso en desarrollo o para usuarios admin
    if (
        current_app.config.get("ENV") != "development"
        and session.get("role") != "admin"
    ):
        flash("Acceso no autorizado", "error")
        return redirect(url_for("auth.login"))

    # Recopilar información de la sesión
    session_info = {
        "session_data": dict(session),
        "session_cookie_name": current_app.config.get("SESSION_COOKIE_NAME"),
        "session_cookie_secure": current_app.config.get("SESSION_COOKIE_SECURE"),
        "session_cookie_httponly": current_app.config.get("SESSION_COOKIE_HTTPONLY"),
        "session_cookie_samesite": current_app.config.get("SESSION_COOKIE_SAMESITE"),
        "permanent_session_lifetime": str(
            current_app.config.get("PERMANENT_SESSION_LIFETIME")
        ),
        "request_cookies": {k: v for k, v in request.cookies.items()},
        "request_headers": {k: v for k, v in request.headers.items()},
        "app_secret_key_type": type(current_app.secret_key).__name__,
        "app_secret_key_length": len(str(current_app.secret_key))
        if current_app.secret_key
        else 0,
        "timestamp": datetime.utcnow().isoformat(),
    }

    # Registrar información para análisis
    logger.info(
        f"Diagnóstico de sesión solicitado: {json.dumps(session_info, default=str)}"
    )

    return render_template("debug/session_info.html", session_info=session_info)


@debug_bp.route("/fix_session")
def fix_session():
    """Intenta reparar problemas comunes de sesión"""
    if (
        current_app.config.get("ENV") != "development"
        and session.get("role") != "admin"
    ):
        flash("Acceso no autorizado", "error")
        return redirect(url_for("auth.login"))

    # Verificar si hay información de usuario en la sesión
    user_id = session.get("user_id")
    if not user_id:
        flash("No hay usuario en la sesión para reparar", "warning")
        return redirect(url_for("debug.debug_session"))

    # Buscar el usuario en la base de datos
    users_collection = getattr(g, "users_collection", None)
    if users_collection is None:
        from app.extensions import mongo
        if mongo and mongo.db is not None:
            users_collection = mongo.db.users

    from bson import ObjectId

    try:
        usuario = users_collection.find_one({"_id": ObjectId(user_id)})
    except Exception as e:
        usuario = None
        logger.error(f"Error al buscar usuario para reparación de sesión: {str(e)}")

    if not usuario:
        flash("Usuario no encontrado en la base de datos", "error")
        return redirect(url_for("debug.debug_session"))

    # Restaurar datos de sesión
    session["email"] = usuario.get("email", "")
    session["username"] = usuario.get("username") or usuario.get("nombre") or "usuario"
    session["role"] = usuario.get("role", "user")
    session["logged_in"] = True
    session.modified = True

    flash("Sesión reparada correctamente", "success")
    logger.info(
        f"Sesión reparada para usuario: {session.get('username')} (ID: {session.get('user_id')})"
    )

    return redirect(url_for("debug.debug_session"))


@debug_bp.route("/test_admin")
def test_admin_access():
    """Prueba el acceso a rutas de administrador"""
    if session.get("role") != "admin":
        flash("Esta prueba requiere permisos de administrador", "warning")
        return redirect(url_for("auth.login"))

    # Verificar que todas las claves necesarias estén en la sesión
    required_keys = ["user_id", "email", "username", "role", "logged_in"]
    missing_keys = [key for key in required_keys if key not in session]

    if missing_keys:
        return jsonify(
            {
                "status": "error",
                "message": f"Faltan claves en la sesión: {', '.join(missing_keys)}",
                "session": dict(session),
            }
        )

    return jsonify(
        {
            "status": "success",
            "message": "Sesión de administrador válida",
            "session": dict(session),
            "admin_dashboard_url": url_for("admin.dashboard_admin"),
        }
    )
