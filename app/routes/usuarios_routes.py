# Script: usuarios_routes.py
# Descripción: [Explica brevemente qué hace el script]
# Uso: python3 usuarios_routes.py [opciones]
# Requiere: [librerías externas, si aplica]
# Variables de entorno: [si aplica]
# Autor: EDF Developer - 2025-05-28

import logging  # noqa: F401
from datetime import datetime

from bson.objectid import ObjectId
from flask import (
    Blueprint,
    current_app,
    flash,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash  # noqa: F401

from app.decorators import admin_required

usuarios_bp = Blueprint("usuarios", __name__, url_prefix="/usuarios")

# @usuarios_bp.route('/login', methods=['GET', 'POST'])
# def login():
#     ...


@usuarios_bp.route("/register", methods=["GET", "POST"])
def register():
    users_collection = getattr(g, "users_collection", None)

    if request.method == "POST":
        if users_collection is None:
            flash("Error de conexión a la base de datos.", "danger")
            return redirect(url_for("usuarios.register"))
        import random  # noqa: E401
        import string

        email = request.form["email"]
        password = request.form["password"]
        hashed_pw = generate_password_hash(password)
        # Generar username único basado en el email
        base_username = email.split("@")[0]
        username = base_username
        # Si ya existe, añadir sufijo aleatorio
        while users_collection.find_one({"username": username}):
            sufijo = "".join(
                random.choices(string.ascii_lowercase + string.digits, k=4)
            )
            username = f"{base_username}_{sufijo}"

        if users_collection.find_one({"email": email}):
            flash("Este correo ya está registrado.", "warning")
        else:
            users_collection.insert_one(
                {"email": email, "password": hashed_pw, "username": username}
            )
            flash("Registro exitoso. Ya puedes iniciar sesión.", "success")
            return redirect(url_for("auth.login"))

    return render_template("auth/register.html")


# Ruta de logout movida a auth_routes.py para evitar duplicados


@usuarios_bp.route("/forgot", methods=["GET", "POST"])
def forgot():
    print(
        "[DEBUG][FORGOT] users_collection:",
        getattr(g, "users_collection", None),
    )
    users_collection = getattr(g, "users_collection", None)
    if request.method == "POST":
        if users_collection is None:
            flash("Error de conexión a la base de datos.", "danger")
            return redirect(url_for("usuarios.forgot"))
        email = request.form["email"]
        user = users_collection.find_one({"email": email})
        if user:
            flash("Si el correo existe, se enviarán instrucciones.", "info")
        else:
            flash("Correo no encontrado.", "warning")
    return render_template("auth/forgot.html")


@usuarios_bp.route("/edit", methods=["GET", "POST"])
def edit():
    print(
        "[DEBUG][EDIT] users_collection:",
        getattr(g, "users_collection", None),
    )
    users_collection = getattr(g, "users_collection", None)
    if "user_id" not in session:
        flash("Debes iniciar sesión.", "warning")
        return redirect(url_for("auth.login"))
    if users_collection is None:
        flash("Error de conexión a la base de datos.", "danger")
        return redirect(url_for("main.dashboard_user"))
    user = users_collection.find_one({"_id": session["user_id"]})

    if request.method == "POST":
        new_email = request.form["email"]
        users_collection.update_one(
            {"_id": user["_id"]}, {"$set": {"email": new_email}}
        )
        flash("Correo actualizado.", "success")
        return redirect(url_for("main.dashboard_user"))

    return render_template("auth/edit.html", user=user)


# Ruta eliminada - duplicada con admin_routes.py
# La funcionalidad de gestión de usuarios está en admin_routes.py


# NUEVO ENDPOINT: Forzar cambio de contraseña
@usuarios_bp.route("/force_password_change", methods=["GET", "POST"])
def force_password_change():
    user_id = session.get("force_password_user_id")
    if not user_id:
        flash("No hay usuario para cambio de contraseña.", "danger")
        return redirect(url_for("auth.login"))
    try:
        users_collection = getattr(g, "users_collection", None)
        if users_collection is None:
            flash("Error de conexión a la base de datos.", "danger")
            return redirect(url_for("auth.login"))
        user = users_collection.find_one({"_id": ObjectId(user_id)})
    except Exception as e:
        flash("ID de usuario inválido.", "danger")
        session.pop("force_password_user_id", None)
        return redirect(url_for("auth.login"))
    if not user:
        flash("Usuario no encontrado.", "danger")
        session.pop("force_password_user_id", None)
        return redirect(url_for("auth.login"))
    if request.method == "POST":
        new_password = request.form.get("new_password")
        confirm_password = request.form.get("confirm_password")
        # Validaciones básicas
        if not new_password or not confirm_password:
            flash("Debes completar ambos campos.", "danger")
            return render_template("force_password_change.html", user=user)
        if new_password != confirm_password:
            flash("Las contraseñas no coinciden.", "danger")
            return render_template("force_password_change.html", user=user)
        if (
            len(new_password) < 8
            or not any(c.isupper() for c in new_password)
            or not any(c.islower() for c in new_password)
            or not any(c.isdigit() for c in new_password)
        ):
            flash(
                "La contraseña debe tener al menos 8 caracteres, una mayúscula, una minúscula y un número.",
                "danger",
            )
            return render_template("force_password_change.html", user=user)
        # Guardar nueva contraseña y limpiar flags
        users_collection.update_one(
            {"_id": user["_id"]},
            {
                "$set": {
                    "password": generate_password_hash(
                        new_password, method="pbkdf2:sha256"
                    ),
                    "must_change_password": False,
                    "temp_password": False,
                    "password_reset_required": False,
                    "password_updated_at": datetime.utcnow().isoformat(),
                }
            },
        )
        session.pop("force_password_user_id", None)
        flash("Contraseña actualizada. Ya puedes iniciar sesión.", "success")
        return redirect(url_for("auth.login"))
    return render_template("force_password_change.html", user=user)
