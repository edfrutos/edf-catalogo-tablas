# Script: admin_user_routes.py
# Descripción: Rutas administrativas de gestión de usuarios.
# Autor: EDF Developer

import logging
import re
from datetime import datetime

from bson import ObjectId
from flask import flash, redirect, render_template, request, session, url_for
from werkzeug.security import generate_password_hash

from app.audit import audit_log
from app.database import get_users_collection
from app.decorators import admin_required


logger = logging.getLogger(__name__)


def register_ain_user_routes(admin_bp) -> None:
    """Registra rutas administrativas de usuarios sobre el blueprint admin."""

    @admin_bp.route("/usuarios")
    @admin_required
    def lista_usuarios():
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
                posibles = {
                    user.get("email"),
                    user.get("username"),
                    user.get("name"),
                    user.get("nombre"),
                }
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
                            f"[ADMIN] Usuario {user.get('email')} tiene {count} catálogos en {collection_name}"
                        )
                    except (AttributeError, KeyError, TypeError) as e:
                        logger.error(
                            f"Error al contar catálogos en {collection_name}: {str(e)}"
                        )
                user["num_catalogs"] = total_count
                logger.info(
                    f"[ADMIN] Usuario {user.get('email')} tiene un total de {total_count} catálogos"
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
            logger.error(f"Error en lista_usuarios: {str(e)}", exc_info=True)
            flash(f"Error al cargar la lista de usuarios: {str(e)}", "error")
            return redirect(url_for("admin.dashboard_admin"))

    @admin_bp.route("/usuarios/delete/<user_id>", methods=["POST"])
    @admin_required
    def eliminar_usuario(user_id: str):
        users_col = get_users_collection()
        if users_col is not None:
            users_col.delete_one({"_id": ObjectId(user_id)})
            flash("Usuario eliminado", "success")
        else:
            flash("Error: No se pudo acceder a la colección de usuarios", "error")
        return redirect(url_for("admin.lista_usuarios"))

    @admin_bp.route("/usuarios/edit/<user_id>", methods=["GET", "POST"])
    @admin_required
    def editar_usuario(user_id: str):
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
                        user_id=session.get("user_id"),
                        details={
                            "verified_user_email": user.get("email"),
                            "verified_by": session.get("username"),
                            "verified_user_name": user.get("nombre", "desconocido"),
                        },
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
                        {"email": {"$regex": f"^{re.escape(email)}$", "$options": "i"}}
                    )

                    if existing_user and str(existing_user.get("_id")) != user_id:
                        email_conflict = True
                        flash(
                            f"El correo electrónico {email} ya está en uso por otro usuario",
                            "error",
                        )
                        logger.warning(
                            f"Intento de actualizar usuario {user_id} con email duplicado: {email}"
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
                _ = users_col.update_one({"_id": ObjectId(user_id)}, {"$set": update_data})

                flash("Usuario actualizado correctamente", "success")
                return redirect(url_for("admin.lista_usuarios"))

            return render_template("admin/editar_usuario.html", usuario=user)
        except (AttributeError, KeyError, TypeError, ValueError) as e:
            logger.error(f"Error al editar usuario {user_id}: {str(e)}", exc_info=True)
            flash(f"Error al editar usuario: {str(e)}", "error")
            return redirect(url_for("admin.lista_usuarios"))

    @admin_bp.route("/usuarios/create", methods=["GET", "POST"])
    @admin_required
    def crear_usuario():
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

            # Aquí deberías implementar la lógica para hashear la contraseña
            # Por ahora, usaremos el password directamente
            user_data = {
                "nombre": nombre,
                "email": email,
                "password": password,  # En producción, hashea esto
                "role": role,
                "num_tables": 0,
                "tables_updated_at": None,
                "last_ip": "",
                "last_login": None,
                "updated_at": None,
                "failed_attempts": 0,
                "locked_until": None,
            }

            _ = users_col.insert_one(user_data)
            flash("Usuario creado exitosamente", "success")
            return redirect(url_for("admin.lista_usuarios"))

        return render_template("admin/crear_usuario.html")

    @admin_bp.route("/usuarios/bulk_upload", methods=["GET", "POST"])
    @admin_required
    def bulk_upload_usuarios():
        """Gestión de usuarios en masa mediante archivo CSV"""
        try:
            if request.method == "POST":
                if "csv_file" not in request.files:
                    flash("No se seleccionó ningún archivo", "error")
                    return redirect(request.url)

                file = request.files["csv_file"]
                if file.filename == "":
                    flash("No se seleccionó ningún archivo", "error")
                    return redirect(request.url)

                if not file.filename.endswith(  # pyright: ignore[reportOptionalMemberAccess]
                    ".csv"
                ):  # pyright: ignore[reportOptionalMemberAccess]
                    flash("El archivo debe ser un CSV", "error")
                    return redirect(request.url)

                # Procesar el archivo CSV
                import csv
                import io
                import random
                import string
                from datetime import datetime

                users_col = get_users_collection()
                if users_col is None:
                    flash("Error: No se pudo acceder a la colección de usuarios", "error")
                    return redirect(request.url)

                # Leer el archivo CSV con manejo de diferentes codificaciones
                file_content = file.read()
                csv_content = None

                # Intentar diferentes codificaciones
                encodings = [
                    "utf-8",
                    "utf-8-sig",
                    "latin-1",
                    "iso-8859-1",
                    "cp1252",
                    "windows-1252",
                ]

                for encoding in encodings:
                    try:
                        csv_content = file_content.decode(encoding)
                        break
                    except UnicodeDecodeError:
                        continue

                if csv_content is None:
                    flash(
                        "Error: No se pudo leer el archivo CSV. Verifique que el archivo esté en una codificación válida (UTF-8, ISO-8859-1, etc.)",
                        "error",
                    )
                    return redirect(request.url)

                csv_reader = csv.DictReader(io.StringIO(csv_content))

                # Validar que las columnas requeridas estén presentes
                required_columns = ["username", "email"]
                if not all(
                    col in (csv_reader.fieldnames or []) for col in required_columns
                ):
                    flash(
                        "El archivo CSV debe contener las columnas: username, email",
                        "error",
                    )
                    return redirect(request.url)

                # Procesar usuarios
                usuarios_procesados = []
                usuarios_exitosos = 0
                usuarios_duplicados = 0
                usuarios_error = 0

                for row_num, row in enumerate(
                    csv_reader, start=2
                ):  # Empezar en 2 porque la fila 1 es el encabezado
                    try:
                        username = row["username"].strip()
                        email = row["email"].strip()

                        # Validaciones básicas
                        if not username or not email:
                            usuarios_error += 1
                            usuarios_procesados.append(
                                {
                                    "row": row_num,
                                    "username": username,
                                    "email": email,
                                    "status": "error",
                                    "message": "Username y email son obligatorios",
                                }
                            )
                            continue

                        # Verificar si el usuario ya existe
                        existing_user = users_col.find_one(
                            {"$or": [{"email": email}, {"username": username}]}
                        )

                        if existing_user:
                            usuarios_duplicados += 1
                            usuarios_procesados.append(
                                {
                                    "row": row_num,
                                    "username": username,
                                    "email": email,
                                    "status": "duplicate",
                                    "message": "Usuario ya existe",
                                }
                            )
                            continue

                        # Generar contraseña temporal
                        temp_password = "".join(
                            random.choices(string.ascii_letters + string.digits, k=12)
                        )

                        # Crear el usuario
                        new_user = {
                            "username": username,
                            "email": email,
                            "password": generate_password_hash(
                                temp_password, method="pbkdf2:sha256"
                            ),
                            "role": "user",
                            "verified": True,
                            "created_at": datetime.utcnow(),
                            "temp_password": True,
                            "must_change_password": True,
                            "password_created_at": datetime.utcnow().isoformat(),
                        }

                        result = users_col.insert_one(new_user)

                        if result.inserted_id:
                            usuarios_exitosos += 1
                            usuarios_procesados.append(
                                {
                                    "row": row_num,
                                    "username": username,
                                    "email": email,
                                    "status": "success",
                                    "message": f"Usuario creado con contraseña temporal: {temp_password}",
                                    "temp_password": temp_password,
                                }
                            )
                        else:
                            usuarios_error += 1
                            usuarios_procesados.append(
                                {
                                    "row": row_num,
                                    "username": username,
                                    "email": email,
                                    "status": "error",
                                    "message": "Error al crear usuario en la base de datos",
                                }
                            )

                    except Exception as e:
                        usuarios_error += 1
                        usuarios_procesados.append(
                            {
                                "row": row_num,
                                "username": row.get("username", "N/A"),
                                "email": row.get("email", "N/A"),
                                "status": "error",
                                "message": f"Error de procesamiento: {str(e)}",
                            }
                        )

                # Mostrar resultados
                flash(
                    f"Procesamiento completado: {usuarios_exitosos} creados, {usuarios_duplicados} duplicados, {usuarios_error} errores",
                    "info",
                )

                return render_template(
                    "admin/bulk_upload_result.html",
                    usuarios_procesados=usuarios_procesados,
                    total_creados=usuarios_exitosos,
                    total_duplicados=usuarios_duplicados,
                    total_errores=usuarios_error,
                )

            return render_template("admin/bulk_upload.html")

        except Exception as e:
            logger.error(f"Error en bulk_upload_usuarios: {str(e)}", exc_info=True)
            flash(f"Error al procesar la carga masiva: {str(e)}", "error")
            return redirect(url_for("admin.lista_usuarios"))

    @admin_bp.route("/usuarios/download_template")
    @admin_required
    def download_csv_template():
        """Descargar plantilla CSV para carga masiva de usuarios"""
        try:
            import csv
            import io

            # Crear el contenido del CSV
            output = io.StringIO()
            writer = csv.writer(output)

            # Escribir encabezados
            writer.writerow(["username", "email"])

            # Escribir algunos ejemplos
            writer.writerow(["usuario1", "usuario1@ejemplo.com"])
            writer.writerow(["usuario2", "usuario2@ejemplo.com"])
            writer.writerow(["usuario3", "usuario3@ejemplo.com"])

            # Preparar la respuesta
            output.seek(0)

            from flask import Response

            return Response(
                output.getvalue(),
                mimetype="text/csv",
                headers={
                    "Content-Disposition": "attachment; filename=usuarios_template.csv"
                },
            )

        except Exception as e:
            logger.error(f"Error al generar plantilla CSV: {str(e)}", exc_info=True)
            flash(f"Error al generar la plantilla: {str(e)}", "error")
            return redirect(url_for("admin.bulk_upload_usuarios"))
