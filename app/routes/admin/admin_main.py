# Script: admin_main.py
# Descripción: [Explica brevemente qué hace el script]
# Uso: python3 admin_main.py [opciones]
# Requiere: [librerías externas, si aplica]
# Variables de entorno: [si aplica]
# Autor: [Tu nombre o equipo] - 2025-07-29

"""
Main admin routes and core functionality.
"""
from flask import Blueprint, render_template, redirect, url_for, flash, session, request
from app.routes.maintenance_routes import admin_required

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route("/scripts-tools")
def scripts_tools_overview():
    """
    Overview of available scripts and tools.
    Requires admin login.
    """
    # Verificar si el usuario está logueado y es admin usando session
    if "user_id" not in session or not session.get("logged_in", False):
        flash("Debes iniciar sesión para acceder.", "warning")
        return redirect(url_for("auth.login", next=request.url))
    # Verificar si el usuario tiene rol de admin
    if session.get("role") != "admin":
        flash("No tienes permisos para acceder a esta sección.", "danger")
        return redirect(url_for("main.dashboard_user"))

    def list_dir_names(path):
        import os
        base = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
        full = os.path.join(base, path)
        if not os.path.isdir(full):
            return []
        items = []
        for name in sorted(os.listdir(full)):
            if name.startswith("."):
                continue
            items.append(
                name + ("/" if os.path.isdir(os.path.join(full, name)) else "")
            )
        return items

    scripts_list = list_dir_names("scripts")
    tests_list = list_dir_names("tests")
    tools_list = list_dir_names("tools")
    return render_template(
        "admin/scripts_tools_overview.html",
        scripts_list=scripts_list,
        tests_list=tests_list,
        tools_list=tools_list,
    )