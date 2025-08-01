# app/admin_routes.py
from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from app.models import get_users_collection
from app.database import get_mongo_db
from bson.objectid import ObjectId
from app.decorators import admin_required  # type: ignore[attr-defined]

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


def check_admin():
    """
    Verifica si el usuario está logueado y es admin usando session

    Returns:
        bool: True si el usuario es admin, False en caso contrario
    """
    if "user_id" not in session or not session.get("logged_in", False):
        return False
    # Verificar si el usuario tiene rol de admin
    if session.get("role") != "admin":
        return False
    return True


def get_catalogs_collection():
    """Obtiene la colección de catálogos desde la base de datos"""
    db = get_mongo_db()
    return db["spreadsheets"] if db is not None else None


# -------------------------------------------
# DASHBOARD ADMINISTRATIVO
# -------------------------------------------
# @admin_bp.route("/admin/maintenance/dashboard")
# def admin_dashboard():
#     if not check_admin():
#         flash("Acceso no autorizado.", "error")
#         return redirect(url_for("main.home"))
#     return render_template("admin/maintenance/dashboard.html")


# -------------------------------------------
# GESTIÓN DE USUARIOS
# -------------------------------------------
@admin_bp.route("/users")
@admin_required
def admin_users():
    if not check_admin():
        flash("Acceso no autorizado.", "error")
        return redirect(url_for("main.home"))
    usuarios = list(get_users_collection().find())
    return render_template("admin/users.html", usuarios=usuarios)


@admin_bp.route("/user/<user_id>/role", methods=["GET", "POST"])
def admin_user_role(user_id):
    if not check_admin():
        flash("Acceso no autorizado.", "error")
        return redirect(url_for("admin.admin_users"))
    usuario = get_users_collection().find_one({"_id": ObjectId(user_id)})
    if not usuario:
        flash("Usuario no encontrado.", "error")
        return redirect(url_for("admin.admin_users"))
    if request.method == "POST":
        nuevo_rol = request.form.get("rol", "").strip()
        get_users_collection().update_one(
            {"_id": ObjectId(user_id)}, {"$set": {"rol": nuevo_rol}}
        )
        flash("Rol actualizado exitosamente.", "success")
        return redirect(url_for("admin.admin_users"))
    return render_template("admin/user_role.html", usuario=usuario)


# -------------------------------------------
# GESTIÓN DE CATÁLOGOS
# -------------------------------------------
@admin_bp.route("/catalogs")
def admin_catalogs():
    if not check_admin():
        flash("Acceso no autorizado.", "error")
        return redirect(url_for("main.home"))

    catalog_collection = get_catalogs_collection()
    if catalog_collection is None:
        flash("Error de conexión a la base de datos.", "error")
        return redirect(url_for("main.home"))

    catalogos = list(catalog_collection.find())
    return render_template("admin/catalogs.html", catalogos=catalogos)


# -------------------------------------------
# OTRAS FUNCIONES ADMINISTRATIVAS
# -------------------------------------------
@admin_bp.route("/duplicate_users")
def admin_duplicate_users():
    if not check_admin():
        flash("Acceso no autorizado.", "error")
        return redirect(url_for("main.home"))

    duplicates = get_users_collection().aggregate(
        [
            {
                "$group": {
                    "_id": "$email",
                    "count": {"$sum": 1},
                    "docs": {"$push": "$$ROOT"},
                }
            },
            {"$match": {"count": {"$gt": 1}}},
        ]
    )
    return render_template("admin/duplicate_users.html", duplicates=list(duplicates))


@admin_bp.route("/suspicious_users")
def admin_suspicious_users():
    if not check_admin():
        flash("Acceso no autorizado.", "error")
        return redirect(url_for("main.home"))

    suspicious = get_users_collection().find({"last_login": {"$exists": False}})
    return render_template("admin/suspicious_users.html", usuarios=list(suspicious))


@admin_bp.route("/security_dashboard")
def admin_security_dashboard():
    if not check_admin():
        flash("Acceso no autorizado.", "error")
        return redirect(url_for("main.home"))

    total_usuarios = get_users_collection().count_documents({})
    usuarios_sin_2fa = get_users_collection().count_documents(
        {"2fa_enabled": {"$ne": True}}
    )
    return render_template(
        "admin/security_dashboard.html",
        total_usuarios=total_usuarios,
        usuarios_sin_2fa=usuarios_sin_2fa,
    )
