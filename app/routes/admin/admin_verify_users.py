# Script: admin_verify_users.py
# Descripción: Rutas administrativas para verificación masiva de usuarios.
# Autor: EDF Developer

import logging

from bson import ObjectId
from flask import flash, redirect, render_template, request, url_for

from app.database import get_users_collection
from app.decorators import admin_required

logger = logging.getLogger(__name__)


def register_admin_verify_user_routes(admin_bp) -> None:
    """Registra rutas de verificación de usuarios sobre el blueprint admin existente."""

    @admin_bp.route("/verify-users")
    @admin_required
    def verify_users():
        try:
            users_col = get_users_collection()
            if users_col is None:
                flash("Error: No se pudo acceder a la colección de usuarios", "error")
                return redirect(url_for("maintenance.maintenance_dashboard"))
            usuarios = list(users_col.find())
            # Contar usuarios verificados y no verificados
            verified_count = sum(1 for user in usuarios if user.get("verified", False))
            unverified_count = len(usuarios) - verified_count
            # Estadísticas de usuarios
            stats = {
                "total": len(usuarios),
                "verified": verified_count,
                "unverified": unverified_count,
            }
            # Obtener usuarios no verificados para mostrarlos en la interfaz
            unverified_users = [
                user for user in usuarios if not user.get("verified", False)
            ]
            return render_template(
                "admin/verify_users.html", stats=stats, unverified_users=unverified_users
            )
        except (AttributeError, KeyError, TypeError, ValueError) as e:
            logger.error(f"Error en verify_users: {str(e)}", exc_info=True)
            flash(f"Error al verificar usuarios: {str(e)}", "error")
            return redirect(url_for("maintenance.maintenance_dashboard"))


    @admin_bp.route("/bulk_user_action", methods=["POST"])
    @admin_required
    def bulk_user_action():
        try:
            user_ids = request.form.getlist("user_ids")
            action = request.form.get("action")
            users_col = get_users_collection()
            if users_col is None:
                flash("Error: No se pudo acceder a la colección de usuarios", "error")
                return redirect(url_for("admin.verify_users"))
            if not user_ids or not action:
                flash("Debes seleccionar usuarios y una acción.", "warning")
                return redirect(url_for("admin.verify_users"))
            object_ids = [ObjectId(uid) for uid in user_ids if uid]
            if action == "verify":
                result = users_col.update_many(
                    {"_id": {"$in": object_ids}}, {"$set": {"verified": True}}
                )
                flash(f"{result.modified_count} usuarios verificados.", "success")
            elif action == "delete":
                result = users_col.delete_many({"_id": {"$in": object_ids}})
                flash(f"{result.deleted_count} usuarios eliminados.", "success")
            else:
                flash("Acción no reconocida.", "danger")
            return redirect(url_for("admin.verify_users"))
        except (AttributeError, KeyError, TypeError, ValueError) as e:
            logger.error(f"Error en bulk_user_action: {str(e)}", exc_info=True)
            flash(f"Error al procesar la acción masiva: {str(e)}", "danger")
            return redirect(url_for("admin.verify_users"))

