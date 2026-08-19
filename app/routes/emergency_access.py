# Script: emergency_access.py
# Descripción: Rutas de acceso de emergencia (DESHABILITADAS EN PRODUCCIÓN)
# ADVERTENCIA: Este módulo está DESHABILITADO en producción.
# Todas las rutas requieren FLASK_ENV=development y token de emergencia válido.

"""
Rutas de acceso de emergencia (SOLO DESARROLLO)
En producción, estas rutas están completamente deshabilitadas.
"""

import logging
import os
from datetime import datetime

from flask import Blueprint, flash, redirect, session, url_for

logger = logging.getLogger(__name__)
emergency_bp = Blueprint("emergency", __name__)


def is_development_mode():
    """Verifica que estamos en desarrollo y tiene token de emergencia válido"""
    flask_env = os.getenv("FLASK_ENV", "production").lower()
    emergency_token = os.getenv("EMERGENCY_TOKEN", "")

    if flask_env != "development":
        logger.error("🔴 ACCESO DENEGADO: No en modo desarrollo")
        return False

    if not emergency_token:
        logger.error("🔴 ACCESO DENEGADO: EMERGENCY_TOKEN no configurado")
        return False

    return True


@emergency_bp.route("/user_login_bypass")
def user_login_bypass():
    """
    DEPRECATED: Esta ruta está deshabilitada en producción.
    Solo funciona en desarrollo con token válido.
    """
    if not is_development_mode():
        logger.error("🔴 Intento de bypass de usuario en producción")
        return "Acceso denegado", 403

    token = os.getenv("EMERGENCY_TOKEN", "")
    provided_token = session.pop("_emergency_token", None)

    if provided_token != token:
        logger.warning("🔴 Token de emergencia inválido")
        flash("Token de emergencia inválido", "error")
        return redirect(url_for("auth.login"))

    try:
        logger.warning("⚠️ SOLO DESARROLLO: Sesión de usuario bypass establecida")
        session.clear()
        session.permanent = True
        session["user_id"] = "dev_user_test"
        session["email"] = "dev@test.local"
        session["username"] = "dev_user"
        session["role"] = "user"
        session["logged_in"] = True
        session.modified = True

        flash("Sesión de desarrollo establecida (SOLO TEST)", "warning")
        return redirect("/")
    except Exception as e:
        logger.error(f"Error en bypass: {str(e)}")
        return redirect(url_for("auth.login"))


@emergency_bp.route("/admin_login_bypass")
def admin_login_bypass():
    """
    DEPRECATED: Esta ruta está deshabilitada en producción.
    Solo funciona en desarrollo con token válido.
    """
    if not is_development_mode():
        logger.error("🔴 Intento de bypass de admin en producción")
        return "Acceso denegado", 403

    token = os.getenv("EMERGENCY_TOKEN", "")
    provided_token = session.pop("_emergency_token", None)

    if provided_token != token:
        logger.warning("🔴 Token de emergencia inválido")
        flash("Token de emergencia inválido", "error")
        return redirect(url_for("auth.login"))

    try:
        logger.warning("⚠️ SOLO DESARROLLO: Sesión de admin bypass establecida")
        session.clear()
        session.permanent = True
        session["user_id"] = "dev_admin_test"
        session["email"] = "dev@admin.local"
        session["username"] = "dev_admin"
        session["role"] = "admin"
        session["logged_in"] = True
        session.modified = True

        flash("Sesión de admin desarrollo establecida (SOLO TEST)", "warning")
        return redirect("/admin/")
    except Exception as e:
        logger.error(f"Error en bypass admin: {str(e)}")
        return redirect(url_for("auth.login"))
