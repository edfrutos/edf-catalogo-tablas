# app/routes/admin_diagnostic.py

import logging
from flask import (
    Blueprint,
    render_template,
    session,
    request,
    current_app,
    flash,
    redirect,
    url_for,
    jsonify,
)
from app.auth_utils import admin_required
from datetime import datetime

logger = logging.getLogger(__name__)
admin_diagnostic_bp = Blueprint(
    "admin_diagnostic", __name__, url_prefix="/admin/diagnostic"
)


@admin_diagnostic_bp.route("/")
@admin_required
def admin_session_check():
    """Ruta para verificar el estado de la sesión de administrador"""
    try:
        # Recopilar información detallada de la sesión
        session_data = {
            "user_id": session.get("user_id"),
            "username": session.get("username"),
            "email": session.get("email"),
            "role": session.get("role"),
            "logged_in": session.get("logged_in"),
            "login_time": session.get("login_time"),
            "client_ip": session.get("client_ip"),
            "session_id": request.cookies.get(
                current_app.config.get("SESSION_COOKIE_NAME")
            ),
            "timestamp": datetime.utcnow().isoformat(),
        }

        # Verificar si todas las claves necesarias están presentes
        required_keys = ["user_id", "username", "email", "role", "logged_in"]
        missing_keys = [key for key in required_keys if not session.get(key)]

        # Verificar si el rol es correcto
        role_valid = session.get("role") == "admin"

        # Registrar información para análisis
        logger.info(f"Diagnóstico de sesión de administrador: {session_data}")

        return render_template(
            "admin/diagnostic.html",
            session_data=session_data,
            missing_keys=missing_keys,
            role_valid=role_valid,
            cookie_name=current_app.config.get("SESSION_COOKIE_NAME"),
            cookie_secure=current_app.config.get("SESSION_COOKIE_SECURE"),
            cookie_httponly=current_app.config.get("SESSION_COOKIE_HTTPONLY"),
            session_lifetime=current_app.config.get("PERMANENT_SESSION_LIFETIME"),
        )
    except Exception as e:
        logger.error(f"Error en diagnóstico de sesión de administrador: {str(e)}")
        flash("Error al procesar el diagnóstico de sesión", "error")
        return redirect(url_for("admin.dashboard_admin"))


@admin_diagnostic_bp.route("/api/check")
def admin_session_api_check():
    """API para verificar el estado de la sesión de administrador"""
    try:
        # Verificar si el usuario está autenticado y es administrador
        if "user_id" not in session or not session.get("logged_in"):
            return jsonify(
                {
                    "status": "error",
                    "message": "No autenticado",
                    "authenticated": False,
                    "admin": False,
                }
            )

        if session.get("role") != "admin":
            return jsonify(
                {
                    "status": "error",
                    "message": "No es administrador",
                    "authenticated": True,
                    "admin": False,
                }
            )

        # Si llegamos aquí, el usuario está autenticado y es administrador
        return jsonify(
            {
                "status": "success",
                "message": "Sesión de administrador válida",
                "authenticated": True,
                "admin": True,
                "username": session.get("username"),
                "email": session.get("email"),
            }
        )

    except Exception as e:
        logger.error(f"Error en API de diagnóstico: {str(e)}")
        return jsonify(
            {
                "status": "error",
                "message": f"Error interno: {str(e)}",
                "authenticated": False,
                "admin": False,
            }
        ), 500
