# Script: admin_passwords.py
# Descripción: Rutas administrativas para gestión de contraseñas temporales.
# Autor: EDF Developer

import logging
from datetime import datetime

from flask import current_app, flash, jsonify, redirect, render_template, request, session, url_for
from werkzeug.security import generate_password_hash

from app.database import get_users_collection
from app.decorators import admin_required

logger = logging.getLogger(__name__)


def register_admin_password_routes(admin_bp) -> None:
    """Registra rutas de gestión de contraseñas sobre el blueprint admin existente."""

    @admin_bp.route("/password-management")
    @admin_required
    def password_management():
        """
        Panel de gestión de contraseñas temporales para administradores.
        """
        try:
            users_collection = get_users_collection()
            if users_collection is None:
                flash("Error: No se pudo acceder a la colección de usuarios", "error")
                return redirect(url_for("admin.dashboard_admin"))

            # Obtener usuarios con contraseñas temporales
            temp_password_users = list(
                users_collection.find(
                    {
                        "$or": [
                            {"temp_password": True},
                            {"must_change_password": True},
                            {"password_reset_required": True},
                        ]
                    }
                )
            )

            # Obtener todos los usuarios para estadísticas
            all_users = list(users_collection.find({}))

            # Preparar datos para el template
            temp_users_data = []
            for user in temp_password_users:
                # Generar contraseña temporal actual (patrón conocido)
                temp_pass = f"{user.get('username', 'user')}123"

                temp_users_data.append(
                    {
                        "id": str(user.get("_id")),
                        "username": user.get("username", "N/A"),
                        "email": user.get("email", "N/A"),
                        "nombre": user.get("nombre", user.get("name", "N/A")),
                        "role": user.get("role", "user"),
                        "temp_password": temp_pass,
                        "temp_password_flag": user.get("temp_password", False),
                        "must_change_password": user.get("must_change_password", False),
                        "password_reset_required": user.get(
                            "password_reset_required", False
                        ),
                        "temp_password_pattern": user.get(
                            "temp_password_pattern", temp_pass
                        ),
                        "temp_password_updated_at": user.get("temp_password_updated_at"),
                        "flags_cleared_at": user.get("flags_cleared_at"),
                        "last_login": user.get("last_login"),
                    }
                )

            # Estadísticas
            stats = {
                "total_users": len(all_users),
                "temp_password_users": len(temp_password_users),
                "percentage": (
                    round((len(temp_password_users) / len(all_users) * 100), 1)
                    if all_users
                    else 0
                ),
                "admin_users": len([u for u in all_users if u.get("role") == "admin"]),
                "regular_users": len(
                    [u for u in all_users if u.get("role", "user") == "user"]
                ),
            }

            # Obtener usuarios normales (sin contraseñas temporales)
            normal_users = list(
                users_collection.find(
                    {
                        "$and": [
                            {"temp_password": {"$ne": True}},
                            {"must_change_password": {"$ne": True}},
                            {"password_reset_required": {"$ne": True}},
                        ]
                    }
                )
            )

            normal_users_data = []
            for user in normal_users:
                normal_users_data.append(
                    {
                        "id": str(user.get("_id")),
                        "username": user.get("username", "N/A"),
                        "email": user.get("email", "N/A"),
                        "name": user.get("nombre", user.get("name", "N/A")),
                        "role": user.get("role", "user"),
                        "verified": user.get("verified", False),
                        "last_login": user.get("last_login"),
                    }
                )

            return render_template(
                "admin/password_management.html",
                temp_users=temp_users_data,
                normal_users=normal_users_data,
                stats=stats,
            )

        except Exception as e:
            logger.error(f"Error en password_management: {str(e)}", exc_info=True)
            flash(f"Error al cargar gestión de contraseñas: {str(e)}", "error")
            return redirect(url_for("admin.dashboard_admin"))


    @admin_bp.route("/password-management/reset/<user_id>", methods=["POST"])
    @admin_required
    def reset_user_password(user_id):
        """
        Generar nueva contraseña temporal para un usuario específico.
        """
        try:
            from bson import ObjectId

            users_collection = get_users_collection()
            if users_collection is None:
                return jsonify(
                    {"success": False, "error": "Error de conexión a base de datos"}
                )

            # Buscar el usuario
            user = users_collection.find_one({"_id": ObjectId(user_id)})
            if not user:
                return jsonify({"success": False, "error": "Usuario no encontrado"})

            username = user.get("username", "user")
            new_temp_password = f"{username}123"

            # Actualizar contraseña y flags
            result = users_collection.update_one(
                {"_id": ObjectId(user_id)},
                {
                    "$set": {
                        "password": generate_password_hash(
                            new_temp_password, method="pbkdf2:sha256"
                        ),
                        "temp_password": True,
                        "must_change_password": True,
                        "password_reset_required": True,
                        "temp_password_updated_at": datetime.utcnow().isoformat(),
                        "temp_password_pattern": new_temp_password,
                        "password_type": "werkzeug",
                        "admin_reset_by": session.get("username", "admin"),
                        "admin_reset_at": datetime.utcnow().isoformat(),
                    }
                },
            )

            if result.modified_count > 0:
                logger.info(
                    f"Contraseña temporal restablecida para {username} por admin {session.get('username')}"
                )
                return jsonify(
                    {
                        "success": True,
                        "message": f"Contraseña temporal restablecida para {username}",
                        "new_password": new_temp_password,
                    }
                )
            else:
                return jsonify(
                    {"success": False, "error": "No se pudo actualizar la contraseña"}
                )

        except Exception as e:
            logger.error(f"Error reseteando contraseña: {str(e)}", exc_info=True)
            return jsonify({"success": False, "error": f"Error interno: {str(e)}"})


    @admin_bp.route("/password-management/clear-flags/<user_id>", methods=["POST"])
    @admin_required
    def clear_user_flags(user_id):
        """
        Limpiar flags de contraseña temporal de un usuario.
        """
        try:
            from bson import ObjectId

            users_collection = get_users_collection()
            if users_collection is None:
                return jsonify(
                    {"success": False, "error": "Error de conexión a base de datos"}
                )

            # Buscar el usuario
            user = users_collection.find_one({"_id": ObjectId(user_id)})
            if not user:
                return jsonify({"success": False, "error": "Usuario no encontrado"})

            username = user.get("username", "user")

            # Limpiar flags
            result = users_collection.update_one(
                {"_id": ObjectId(user_id)},
                {
                    "$set": {
                        "temp_password": False,
                        "must_change_password": False,
                        "password_reset_required": False,
                        "flags_cleared_at": datetime.utcnow().isoformat(),
                        "flags_cleared_by": session.get("username", "admin"),
                        "flags_cleared_manually": True,
                    }
                },
            )

            if result.modified_count > 0:
                logger.info(
                    f"Flags limpiados para {username} por admin {session.get('username')}"
                )
                return jsonify(
                    {"success": True, "message": f"Flags limpiados para {username}"}
                )
            else:
                return jsonify(
                    {"success": False, "error": "No se pudieron limpiar los flags"}
                )

        except Exception as e:
            logger.error(f"Error limpiando flags: {str(e)}", exc_info=True)
            return jsonify({"success": False, "error": f"Error interno: {str(e)}"})


    @admin_bp.route("/password-management/bulk-action", methods=["POST"])
    @admin_required
    def bulk_password_action():
        """
        Acciones masivas sobre usuarios con contraseñas temporales.
        """
        try:
            action = request.json.get("action") if request.json else None
            user_ids = request.json.get("user_ids", []) if request.json else []

            if not action or not user_ids:
                return jsonify(
                    {"success": False, "error": "Acción o usuarios no especificados"}
                )

            users_collection = get_users_collection()
            if users_collection is None:
                return jsonify(
                    {"success": False, "error": "Error de conexión a base de datos"}
                )

            results = []

            if action == "clear_all_flags":
                for user_id in user_ids:
                    try:
                        from bson import ObjectId

                        result = users_collection.update_one(
                            {"_id": ObjectId(user_id)},
                            {
                                "$set": {
                                    "temp_password": False,
                                    "must_change_password": False,
                                    "password_reset_required": False,
                                    "flags_cleared_at": datetime.utcnow().isoformat(),
                                    "flags_cleared_by": session.get("username", "admin"),
                                    "bulk_action": True,
                                }
                            },
                        )
                        results.append(
                            {"user_id": user_id, "success": result.modified_count > 0}
                        )
                    except Exception as e:
                        results.append(
                            {"user_id": user_id, "success": False, "error": str(e)}
                        )

            elif action == "reset_all_passwords":
                for user_id in user_ids:
                    try:
                        from bson import ObjectId

                        user = users_collection.find_one({"_id": ObjectId(user_id)})
                        if user:
                            username = user.get("username", "user")
                            new_temp_password = f"{username}123"

                            result = users_collection.update_one(
                                {"_id": ObjectId(user_id)},
                                {
                                    "$set": {
                                        "password": generate_password_hash(
                                            new_temp_password, method="pbkdf2:sha256"
                                        ),
                                        "temp_password": True,
                                        "must_change_password": True,
                                        "password_reset_required": True,
                                        "temp_password_updated_at": datetime.utcnow().isoformat(),
                                        "temp_password_pattern": new_temp_password,
                                        "admin_reset_by": session.get("username", "admin"),
                                        "bulk_action": True,
                                    }
                                },
                            )
                            results.append(
                                {"user_id": user_id, "success": result.modified_count > 0}
                            )
                    except Exception as e:
                        results.append(
                            {"user_id": user_id, "success": False, "error": str(e)}
                        )

            successful = len([r for r in results if r.get("success")])
            total = len(results)

            logger.info(
                f"Acción masiva '{action}' por admin {session.get('username')}: {successful}/{total} exitosos"
            )

            return jsonify(
                {
                    "success": True,
                    "message": f"Acción completada: {successful}/{total} usuarios procesados",
                    "results": results,
                }
            )

        except Exception as e:
            logger.error(f"Error en acción masiva: {str(e)}", exc_info=True)
            return jsonify({"success": False, "error": f"Error interno: {str(e)}"})


    @admin_bp.route("/assign-temp-password/<user_id>", methods=["POST"])
    @admin_required
    def assign_temp_password(user_id):
        """
        Asignar contraseña temporal a un usuario normal.
        """
        try:
            from bson import ObjectId
            from werkzeug.security import generate_password_hash

            from app.models.database import get_users_collection

            users_collection = get_users_collection()
            if users_collection is None:
                return jsonify(
                    {"success": False, "error": "No se pudo acceder a la base de datos"}
                )

            # Buscar el usuario
            user = users_collection.find_one({"_id": ObjectId(user_id)})
            if not user:
                return jsonify({"success": False, "error": "Usuario no encontrado"})

            username = user.get("username")
            if not username:
                return jsonify(
                    {"success": False, "error": "Usuario sin nombre de usuario válido"}
                )

            # Generar contraseña temporal con patrón conocido
            temp_password = f"{username}123"
            hashed_password = generate_password_hash(temp_password, method="pbkdf2:sha256")

            # Actualizar usuario con flags temporales
            from datetime import datetime

            result = users_collection.update_one(
                {"_id": ObjectId(user_id)},
                {
                    "$set": {
                        "password": hashed_password,
                        "temp_password": True,
                        "must_change_password": True,
                        "password_reset_required": True,
                        "temp_password_pattern": temp_password,
                        "temp_password_updated_at": datetime.now().isoformat(),
                        "temp_password_assigned_by": session.get("username", "admin"),
                        "temp_password_reason": "Acceso sin correo - Asignación manual por administrador",
                    }
                },
            )

            if result.modified_count > 0:
                logger.info(
                    f"Contraseña temporal asignada a {username} por admin {session.get('username')}"
                )
                return jsonify(
                    {
                        "success": True,
                        "message": f"Contraseña temporal asignada correctamente a {username}",
                        "temp_password": temp_password,
                    }
                )
            else:
                return jsonify(
                    {"success": False, "error": "No se pudo actualizar el usuario"}
                )

        except Exception as e:
            logger.error(f"Error asignando contraseña temporal: {str(e)}", exc_info=True)
            return jsonify({"success": False, "error": f"Error interno: {str(e)}"})


    @admin_bp.route("/test-modal-functions")
    def test_modal_functions():
        """
        Página de test para verificar que las funciones de modal funcionen correctamente.
        """
        try:
            return render_template("admin/test_modal_functions.html")
        except Exception as e:
            current_app.logger.error(f"Error en test_modal_functions: {e}")
            return f"Error: {str(e)}", 500

