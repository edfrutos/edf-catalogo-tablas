# Script: admin_users.py
# Descripción: [Explica brevemente qué hace el script]
# Uso: python3 admin_users.py [opciones]
# Requiere: [librerías externas, si aplica]
# Variables de entorno: [si aplica]
# Autor: [Tu nombre o equipo] - 2025-07-29

"""
User management routes for admin functionality.
"""
import logging
from datetime import datetime
from bson import ObjectId
from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from werkzeug.security import generate_password_hash
from app.database import get_users_collection, get_db
from app.routes.maintenance_routes import admin_required
from app.audit import audit_log

admin_users_bp = Blueprint('admin_users', __name__, url_prefix='/admin/users')
logger = logging.getLogger(__name__)

@admin_users_bp.route("/")
@admin_required
def lista_usuarios():
    """
    Lista todos los usuarios del sistema con sus estadísticas.
    """
    try:
        # Obtener el término de búsqueda
        q = request.args.get("q", "").strip()
        users_col = get_users_collection()
        if users_col is None:
            flash("Error: No se pudo acceder a la colección de usuarios", "error")
            return redirect(url_for("admin.dashboard_admin"))

        if q:
            # Búsqueda insensible a mayúsculas/minúsculas en email o nombre de usuario
            usuarios = list(
                users_col.find(
                    {
                        "$or": [
                            {"email": {"$regex": q, "$options": "i"}},
                            {"username": {"$regex": q, "$options": "i"}},
                            {"nombre": {"$regex": q, "$options": "i"}},
                        ]
                    }
                )
            )
        else:
            usuarios = list(users_col.find())

        # Ordenar usuarios por nombre alfabéticamente
        usuarios.sort(key=lambda u: u.get("nombre", "").lower())

        # Obtener catálogos para calcular cuántos tiene cada usuario
        from app.extensions import mongo

        collections_to_check = ["catalogs", "spreadsheets"]
        for user in usuarios:
            posibles = set(
                [
                    user.get("email"),
                    user.get("username"),
                    user.get("name"),
                    user.get("nombre"),
                ]
            )
            posibles = {v for v in posibles if v}
            total_count = 0
            for collection_name in collections_to_check:
                try:
                    if mongo and mongo.db is not None:
                        collection = mongo.db[collection_name]
                    else:
                        continue
                    query = {"$or": []}
                    for val in posibles:
                        query["$or"].extend(
                            [
                                {"created_by": val},
                                {"owner": val},
                                {"owner_name": val},
                                {"email": val},
                                {"username": val},
                                {"name": val},
                            ]
                        )
                    count = collection.count_documents(query)
                    total_count += count
                    logger.info(
                        "[ADMIN] Usuario %s tiene %s catálogos en %s",
                        user.get('email'),
                        count,
                        collection_name
                    )
                except (AttributeError, KeyError, TypeError) as e:
                    logger.error(
                        "Error al contar catálogos en %s: %s",
                        collection_name,
                        str(e)
                    )
            user["num_catalogs"] = total_count
            logger.info(
                "[ADMIN] Usuario %s tiene un total de %s catálogos",
                user.get('email'),
                total_count
            )

        # Calcular estadísticas
        stats = {
            "total": len(usuarios),
            "roles": {
                "admin": sum(1 for u in usuarios if u.get("role") == "admin"),
                "normal": sum(1 for u in usuarios if u.get("role") == "user"),
                "no_role": sum(1 for u in usuarios if not u.get("role")),
            },
        }
        return render_template("admin/users.html", usuarios=usuarios, stats=stats)
    except (AttributeError, KeyError, TypeError) as e:
        logger.error("Error en lista_usuarios: %s", str(e), exc_info=True)
        flash(f"Error al cargar la lista de usuarios: {str(e)}", "error")
        return redirect(url_for("admin.dashboard_admin"))

@admin_users_bp.route("/delete/<user_id>", methods=["POST"])
@admin_required
def eliminar_usuario(user_id):
    """
    Elimina un usuario del sistema.
    """
    users_col = get_users_collection()
    if users_col is not None:
        users_col.delete_one({"_id": ObjectId(user_id)})
        flash("Usuario eliminado", "success")
    else:
        flash("Error: No se pudo acceder a la colección de usuarios", "error")
    return redirect(url_for("admin.lista_usuarios"))

@admin_users_bp.route("/edit/<user_id>", methods=["GET", "POST"])
@admin_required
def editar_usuario(user_id):
    """
    Edita la información de un usuario.
    """
    try:
        users_col = get_users_collection()
        if users_col is None:
            flash("Error: No se pudo acceder a la colección de usuarios", "error")
            return redirect(url_for("admin.lista_usuarios"))
        user = users_col.find_one({"_id": ObjectId(user_id)})
        if not user:
            flash("Usuario no encontrado", "error")
            return redirect(url_for("admin.lista_usuarios"))

        if request.method == "POST":
            # Verificar si es una solicitud de verificación desde la página verify_users
            verified = request.form.get("verified")
            if verified == "true":
                users_col.update_one(
                    {"_id": ObjectId(user_id)},
                    {"$set": {"verified": True, "updated_at": datetime.now()}},
                )
                flash(
                    f"Usuario {user.get('nombre', 'desconocido')} ha sido verificado",
                    "success",
                )
                # Registrar en el log de auditoría
                audit_log(
                    "user_verified", 
                    user_id=session.get('user_id'),
                    details={
                        "verified_user_email": user.get('email'), 
                        "verified_by": session.get('username'),
                        "verified_user_name": user.get('nombre', 'desconocido')
                    }
                )
                return redirect(url_for("admin.verify_users"))

            # Procesamiento normal de edición de usuario
            nombre = request.form.get("nombre")
            email = request.form.get("email")
            role = request.form.get("role", "user")
            new_password = request.form.get("password")
            confirm_password = request.form.get("confirm_password")
            verified_status = request.form.get("verified_status") == "on"

            # Validar que el nombre y email no estén vacíos
            if not nombre or not email:
                flash("El nombre y el correo son requeridos", "error")
                return redirect(url_for("admin.editar_usuario", user_id=user_id))

            # Verificar si el email ya existe para otro usuario
            email_changed = email.lower() != user.get("email", "").lower()
            email_conflict = False

            if email_changed:
                # Buscar si el email ya existe para otro usuario
                existing_user = users_col.find_one(
                    {"email": {"$regex": f"^{email}$", "$options": "i"}}
                )

                if existing_user and str(existing_user.get("_id")) != user_id:
                    email_conflict = True
                    flash(
                        f"El correo electrónico {email} ya está en uso por otro usuario",
                        "error",
                    )
                    logger.warning(
                        "Intento de actualizar usuario %s con email duplicado: %s",
                        user_id,
                        email
                    )

            # Si se proporcionó una nueva contraseña
            if new_password:
                if new_password != confirm_password:
                    flash("Las contraseñas no coinciden", "error")
                    return redirect(url_for("admin.editar_usuario", user_id=user_id))

                # Verificar que la contraseña cumpla con los requisitos
                if len(new_password) < 8:
                    flash("La contraseña debe tener al menos 8 caracteres", "error")
                    return redirect(url_for("admin.editar_usuario", user_id=user_id))

                # Actualizar la contraseña
                password_hash = generate_password_hash(new_password)
                users_col.update_one(
                    {"_id": ObjectId(user_id)}, {"$set": {"password": password_hash}}
                )
                flash("Contraseña actualizada", "success")

            # Si hay conflicto de email, no actualizar nada más
            if email_conflict:
                return redirect(url_for("admin.editar_usuario", user_id=user_id))

            # Actualizar otros campos
            update_data = {
                "nombre": nombre,
                "role": role,
                "verified": verified_status,
                "updated_at": datetime.now(),
            }

            # Solo actualizar el email si ha cambiado
            if email_changed:
                update_data["email"] = email

            # Realizar la actualización
            users_col.update_one({"_id": ObjectId(user_id)}, {"$set": update_data})

            flash("Usuario actualizado correctamente", "success")
            return redirect(url_for("admin.lista_usuarios"))

        return render_template("admin/editar_usuario.html", usuario=user)
    except (AttributeError, KeyError, TypeError, ValueError) as e:
        logger.error("Error al editar usuario %s: %s", user_id, str(e), exc_info=True)
        flash(f"Error al editar usuario: {str(e)}", "error")
        return redirect(url_for("admin.lista_usuarios"))

@admin_users_bp.route("/create", methods=["GET", "POST"])
@admin_required
def crear_usuario():
    """
    Crea un nuevo usuario en el sistema.
    """
    if request.method == "POST":
        nombre = request.form.get("nombre")
        email = request.form.get("email")
        password = request.form.get("password")
        role = request.form.get("role", "user")

        if not all([nombre, email, password]):
            flash("Todos los campos son requeridos", "error")
            return render_template("admin/crear_usuario.html")

        users_col = get_users_collection()
        if users_col is None:
            flash("Error: No se pudo acceder a la colección de usuarios", "error")
            return render_template("admin/crear_usuario.html")

        existing_user = users_col.find_one({"email": email})

        if existing_user:
            flash("Ya existe un usuario con este email", "error")
            return render_template("admin/crear_usuario.html")

        user_data = {
            "nombre": nombre,
            "email": email,
            "password": generate_password_hash(password),
            "role": role,
            "num_tables": 0,
            "tables_updated_at": None,
            "last_ip": "",
            "last_login": None,
            "updated_at": None,
            "failed_attempts": 0,
            "locked_until": None,
            "created_at": datetime.now()
        }

        users_col.insert_one(user_data)
        flash("Usuario creado exitosamente", "success")
        return redirect(url_for("admin.lista_usuarios"))

    return render_template("admin/crear_usuario.html")