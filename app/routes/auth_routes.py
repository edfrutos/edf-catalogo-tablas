# app/routes/auth_routes.py

import logging
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
    current_app,
    jsonify,
    g,
)
from flask_login import login_user
from app.models.user import User
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Message
from app.extensions import mail
from app.models import (
    get_users_collection,
    get_resets_collection,
    find_user_by_email_or_name,
    find_reset_token,
    update_user_password,
    mark_token_as_used,
)
import secrets
from datetime import datetime, timedelta
import hashlib
import base64
import traceback
import bcrypt
import os
import sys

logger = logging.getLogger(__name__)
auth_bp = Blueprint("auth", __name__)

def get_users_collection_safe():
    """
    Obtiene la colección 'users' desde el contexto g de forma segura.
    Lanza RuntimeError si no está inicializada.
    """
    users_collection = getattr(g, "users_collection", None)
    if users_collection is None:
        if hasattr(g, "mongo") and g.mongo is not None and hasattr(g.mongo, "db") and hasattr(g.mongo.db, "users"):
            users_collection = g.mongo.db.users
        else:
            raise RuntimeError("La colección 'users' no está inicializada en el contexto g")
    return users_collection

def verify_password(password, stored_password, password_type=None):
    """Verifica una contraseña contra su hash almacenado."""
    try:
        # Convertir a string si es bytes
        if isinstance(stored_password, bytes):
            stored_password = stored_password.decode("utf-8")

        # Detectar tipo de hash directamente del prefijo del hash almacenado
        if stored_password.startswith("scrypt:"):
            detected_type = "scrypt"
        elif stored_password.startswith(("$2a$", "$2b$", "$2y$")):
            detected_type = "bcrypt"
        else:
            detected_type = "werkzeug"

        # Si no se pasa password_type o no concuerda con lo detectado, usamos el detectado
        if not password_type or password_type.lower() != detected_type:
            if password_type and password_type.lower() != detected_type:
                logger.warning(
                    "Incongruencia entre password_type='%s' y hash detectado='%s'. Se usará '%s'",
                    password_type,
                    detected_type,
                    detected_type,
                )
            password_type = detected_type

        if password_type == "scrypt":
            # Primero probar con check_password_hash (compatible con formato scrypt de Werkzeug)
            try:
                if check_password_hash(stored_password, password):
                    logger.debug("Verificación scrypt vía Werkzeug exitosa")
                    return True
            except Exception as e:
                logger.debug(
                    "check_password_hash no aplicable para este hash scrypt: %s", str(e)
                )

        elif password_type == "bcrypt":
            try:
                return bcrypt.checkpw(
                    password.encode("utf-8"), stored_password.encode("utf-8")
                )
            except Exception as e:
                logger.error("Error verificando contraseña bcrypt: %s", str(e))
                return False

        elif password_type == "werkzeug":
            # No es necesario convertir a bytes, check_password_hash maneja pbkdf2 y scrypt
            return check_password_hash(stored_password, password)

        else:
            logger.warning("Tipo de contraseña desconocido: %s", password_type)
            return False

    except Exception as e:
        logger.error("Error general en verificación de contraseña: %s", str(e))
        return False


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    # Redirección automática si ya está autenticado
    if session.get("logged_in"):
        if session.get("role") == "admin":
            return redirect("/admin/")
        else:
            return redirect(url_for("main.dashboard_user"))
    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "").strip()

        logger.info(f"Intentando registrar usuario: {email}")

        if not nombre or not email or not password:
            flash("Todos los campos son obligatorios.", "error")
            return redirect(url_for("auth.register"))

        # Verificar si el email ya existe
        users_collection = get_users_collection_safe()
        if users_collection.find_one({"email": email}):
            logger.warning(f"Email ya registrado: {email}")
            flash("Ese email ya está registrado.", "error")
            return redirect(url_for("auth.register"))

        # Generar hash de contraseña usando Werkzeug
        hashed_password = generate_password_hash(
            password,
            method="scrypt",
            salt_length=16,
        )

        # Crear documento de usuario
        nuevo_usuario = {
            "nombre": nombre,
            "email": email,
            "password": hashed_password,
            "created_at": datetime.utcnow(),
            "role": "user",
            "updated_at": datetime.utcnow().isoformat(),
            "failed_attempts": 0,
            "last_ip": "",
            "last_login": None,
            "locked_until": None,
            "num_tables": 0,
            "password_updated_at": datetime.utcnow().isoformat(),
            "tables_updated_at": None,
        }

        # Insertar en la colección users
        try:
            result = users_collection.insert_one(nuevo_usuario)
            logger.info(f"Usuario registrado correctamente: {email}")

            # Si llegamos aquí, la autenticación fue exitosa
            session["user_id"] = str(result.inserted_id)
            session["email"] = nuevo_usuario["email"]
            session["logged_in"] = True
            session["role"] = nuevo_usuario.get("role", "user")
            session.permanent = True  # Hacer la sesión permanente

            # Actualizar último inicio de sesión
            users_collection.update_one(
                {"_id": result.inserted_id},
                {
                    "$set": {"ultimo_login": datetime.utcnow()},
                    "$inc": {"login_count": 1},
                },
                upsert=True,
            )

            logger.info(f"Usuario {email} ha iniciado sesión exitosamente")

            # Manejar redirección después de login
            next_page = request.args.get("next")
            if next_page:
                logger.info(f"Redirigiendo a la página solicitada: {next_page}")
                return redirect(next_page)

            # Redirigir según el rol si no hay página de destino
            if session.get("role") == "admin":
                return redirect(url_for("admin.dashboard_admin"))
            else:
                return redirect(url_for("main.dashboard_user"))

        except Exception as e:
            logger.error(f"Error registrando usuario: {str(e)}")
            flash("Error interno del servidor. Por favor intenta nuevamente.", "error")
            return redirect(url_for("auth.register"))

    return render_template("register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    # Redirección automática si ya está autenticado
    if session.get("logged_in"):
        if session.get("role") == "admin":
            return redirect("/admin/")
        else:
            return redirect(url_for("main.dashboard_user"))
    try:
        if request.method == "GET":
            logger.debug("Mostrando formulario de login")
            return render_template("login.html")

        logger.info("=== INICIO DE INTENTO DE LOGIN ===")
        # Permitir formularios que envíen el nombre del campo como 'login_input' o simplemente 'email'
        raw_input = request.form.get("login_input") or request.form.get("email") or ""
        logger.info(f"Valor recibido en formulario (sin normalizar): '{raw_input}'")
        email = raw_input.strip().lower()
        password = request.form.get("password", "").strip()

        logger.info(f"Datos recibidos - Email: {email}")

        if not email or not password:
            flash("Email y contraseña son requeridos.", "error")
            return redirect(url_for("auth.login"))

        # Obtener la colección de usuarios
        users_collection = get_users_collection_safe()

        # Buscar usuario por email o username usando función existente
        logger.info(f"Buscando usuario con identificador: {email}")
        usuario = find_user_by_email_or_name(email)
        if usuario:
            logger.info(f"Usuario encontrado: {usuario.get('email', usuario.get('username', ''))}")
        else:
            # Loguear todos los usernames almacenados para depuración
            try:
                users_collection = get_users_collection_safe()
                usernames = users_collection.distinct("username")
                logger.warning(f"Usernames almacenados en la base de datos: {usernames}")
            except Exception as e:
                logger.error(f"Error obteniendo usernames para depuración: {e}")
            logger.warning(f"Usuario no encontrado: {email}")
            flash("Credenciales inválidas.", "error")
            return redirect(url_for("auth.login"))

        logger.info(f"Usuario encontrado: {email}")

        # Verificar contraseña
        password_result = verify_password(
            password, usuario["password"], usuario.get("password_type")
        )

        # Para admin@example.com, permitir acceso directo con admin123 (bypass de seguridad temporal)
        if email == "admin@example.com" and password == "admin123":
            logger.warning("Acceso directo permitido para el administrador")
            password_result = True

        if password_result:
            from flask_login import login_user
            # Limpiar intentos fallidos
            users_collection.update_one(
                {"_id": usuario["_id"]},
                {
                    "$set": {
                        "failed_attempts": 0,
                        "locked_until": None,
                        "last_login": datetime.utcnow().isoformat(),
                        "last_ip": request.remote_addr,
                    }
                },
            )

            # Limpiar la sesión anterior si existe
            session.clear()
            session.permanent = True

            # Usar login_user para establecer el usuario autenticado en Flask-Login
            login_user(User(usuario))

            # Guardar datos clave en la sesión
            session["usuario"] = str(usuario.get("_id"))
            session["username"] = usuario.get("username", "")
            session["nombre"] = usuario.get("nombre", "")
            session["email"] = usuario.get("email", "")
            session["role"] = usuario.get("role", "")
            session["user_id"] = str(usuario.get("_id"))
            session["logged_in"] = True

            logger.info(f"Sesión iniciada exitosamente para {usuario.get('email')}")

            # Redirigir según el rol
            if usuario.get("role") == "admin":
                logger.info("Redirigiendo a panel de administración")
                response = redirect(url_for("admin.dashboard_admin"))
            else:
                logger.info("Redirigiendo a dashboard principal")
                response = redirect(url_for("main.dashboard_user"))

            logger.info(f"Login exitoso para: {email}")
            return response

        else:
            logger.warning(f"Contraseña inválida para usuario: {email}")
            flash("Credenciales inválidas.", "error")
            return redirect(url_for("auth.login"))

    except Exception as e:
        logger.error(f"Error en login: {str(e)}\n{traceback.format_exc()}")
        flash("Ha ocurrido un error al procesar la solicitud.", "error")
        return render_template("login.html")


# Ruta para login directo de pruebas - ¡SOLO PARA DEPURACIÓN!
@auth_bp.route("/login_directo")
def login_directo():
    try:
        logger.info("===== ACCESO DIRECTO PARA DEPURACIÓN =====")

        # Buscar usuario admin
        users_collection = get_users_collection_safe()
        usuario = users_collection.find_one({"email": "admin@example.com"})
        if not usuario:
            logger.warning("No se encontró el usuario admin para login directo")
            flash("No se encontró el usuario administrador", "error")
            return redirect(url_for("auth.login"))

        # Establecer sesión directamente
        session.clear()
        session.permanent = True
        session["user_id"] = str(usuario["_id"])
        session["email"] = usuario["email"]
        session["username"] = usuario.get("username", "administrator")
        session["role"] = usuario.get("role", "admin")
        session["logged_in"] = True
        session.modified = True

        # Registro detallado
        logger.info(f"Datos de sesión establecidos por acceso directo: {dict(session)}")

        # Redirigir al panel de administración
        response = redirect(url_for("admin.dashboard_admin"))
        return response

    except Exception as e:
        logger.error(f"Error en login_directo: {str(e)}\n{traceback.format_exc()}")
        flash("Error al procesar el acceso directo", "error")
        return redirect(url_for("auth.login"))


@auth_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        usuario_input = request.form.get("usuario", "").strip()
        logger.info("Solicitud de recuperación para: %s", usuario_input)

        if not usuario_input:
            flash("Debes ingresar tu nombre o correo.", "error")
            return redirect(url_for("auth.forgot_password"))

        # Obtener la colección de usuarios
        users_collection = get_users_collection_safe()

        # Buscar el usuario por email o nombre
        try:
            user = find_user_by_email_or_name(usuario_input)
            logger.debug("Resultado de búsqueda para %s: %s", usuario_input, user)
        except Exception as e:
            logger.exception("Error al buscar el usuario")
            flash(
                "Ocurrió un error al buscar el usuario. Por favor, inténtalo de nuevo.",
                "error",
            )
            return redirect(url_for("auth.forgot_password"))

        if not user:
            logger.warning("Usuario no encontrado: %s", usuario_input)
            flash(
                "No se encontró ningún usuario con ese nombre o email. Verifica que esté correctamente escrito.",
                "error",
            )
            return redirect(url_for("auth.forgot_password"))

        token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(minutes=30)

        get_resets_collection().insert_one(
            {
                "user_id": user["_id"],
                "token": token,
                "expires_at": expires_at,
                "used": False,
            }
        )

        reset_link = url_for("auth.reset_password", token=token, _external=True)
        msg = Message("Recuperación de contraseña", recipients=[user["email"]])
        msg.sender = "no-reply@edefrutos.xyz"
        msg.body = (
            f"Hola {user.get('nombre', 'usuario')},\n\n"
            f"Para restablecer tu contraseña, haz clic en el siguiente enlace:\n"
            f"{reset_link}\n\nEste enlace caduca en 30 minutos."
        )
        try:
            mail.send(msg)
            logger.info("Email de recuperación enviado a: %s", user["email"])
        except Exception as e:
            logger.exception("Error al enviar el email de recuperación")
            flash(
                "No se pudo enviar el email. Contacte con el administrador.", "danger"
            )

        flash("Se ha enviado un enlace de recuperación a tu email.", "info")
        return redirect(url_for("auth.login"))

    return render_template("forgot_password.html")


@auth_bp.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    try:
        # Verificar token
        users_collection = get_users_collection_safe()
        reset_info = get_resets_collection().find_one({"token": token, "used": False})
        if not reset_info:
            flash("Token inválido o expirado.", "error")
            return redirect(url_for("auth.login"))

        if request.method == "POST":
            new_pass = request.form.get("password", "").strip()
            if not new_pass:
                flash("Contraseña obligatoria.", "error")
                return render_template("reset_password_form.html", token=token)

            # Generar nuevo hash de contraseña usando Werkzeug
            hashed_password = generate_password_hash(
                new_pass,
                method="scrypt",
                salt_length=16,
            )

            # Actualizar contraseña del usuario
            users_collection.update_one(
                {"_id": reset_info["user_id"]},
                {
                    "$set": {
                        "password": hashed_password,
                        "password_updated_at": datetime.utcnow().isoformat(),
                    }
                },
            )

            # Marcar token como usado
            get_resets_collection().update_one(
                {"_id": reset_info["_id"]}, {"$set": {"used": True}}
            )

            logger.info(
                f"Contraseña restablecida para usuario ID: '{reset_info['user_id']}'"
            )
            flash(
                "Contraseña restablecida exitosamente. Puedes iniciar sesión.",
                "success",
            )
            return redirect(url_for("auth.login"))

        return render_template("reset_password_form.html", token=token)

    except Exception as e:
        logger.error(f"Error en reset de contraseña: {str(e)}")
        flash("Error interno del servidor. Por favor intenta nuevamente.", "error")
        return redirect(url_for("auth.login"))


@auth_bp.route("/logout")
def logout():
    usuario = session.get("usuario")
    logger.info("Usuario cerró sesión: %s", usuario)

    # Limpiar la sesión
    session.clear()

    # Configurar la respuesta para eliminar las cookies
    response = redirect(url_for("auth.login"))

    # Eliminar explícitamente la cookie de sesión
    response.delete_cookie(current_app.config.get("SESSION_COOKIE_NAME", "session"))

    # Eliminar otras cookies que puedan estar relacionadas con la autenticación
    response.delete_cookie("remember_token")

    # Establecer Cache-Control para evitar que el navegador almacene en caché la página
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"

    flash("Has cerrado sesión correctamente", "info")
    return response


@auth_bp.route("/debug_secret_key")
def debug_secret_key():
    if "user_id" not in session:
        return "No autorizado", 401
    return jsonify(
        {
            "SECRET_KEY": str(current_app.secret_key),
            "SESSION_COOKIE_NAME": current_app.config.get("SESSION_COOKIE_NAME"),
            "pid": os.getpid(),
            "session": dict(session),
        }
    )
