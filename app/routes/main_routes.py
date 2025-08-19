# app/routes/main_routes.py

from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    session,
    flash,
    current_app,
    request,
    g,
)
from app.decorators import login_required  # type: ignore[attr-defined]
from bson.objectid import ObjectId
import logging
from werkzeug.routing import BuildError
import os
from werkzeug.utils import secure_filename
import secrets
from datetime import datetime
import openpyxl
from openpyxl import Workbook
import csv
import uuid
from app.database import get_mongo_db
from app import notifications
from app.utils.image_utils import get_images_for_template, get_raw_images_for_edit

main_bp = Blueprint("main", __name__)
logger = logging.getLogger(__name__)


@main_bp.route("/")
def index():
    # Redirigir a welcome si no está logueado
    if "user_id" not in session:
        return redirect(url_for("main.welcome"))
    return redirect(url_for("main.dashboard_user"))


@main_bp.route("/welcome")
def welcome():
    return render_template("welcome.html")


@main_bp.route("/contacto", methods=["GET", "POST"])
def contacto():
    if request.method == "POST":
        # Obtener datos del formulario
        nombre = request.form.get("nombre", "").strip()
        email = request.form.get("email", "").strip()
        asunto = request.form.get("asunto", "").strip()
        mensaje = request.form.get("mensaje", "").strip()

        # Validación básica
        if not all([nombre, email, asunto, mensaje]):
            flash("Todos los campos son obligatorios.", "error")
            return render_template("contacto.html")

        # Aquí podrías enviar el email o guardar en base de datos
        # Por ahora solo mostramos un mensaje de éxito
        flash(
            f"¡Gracias {nombre}! Tu mensaje ha sido enviado correctamente. Te contactaremos pronto.",
            "success",
        )
        logger.info(
            f"Formulario de contacto enviado - Nombre: {nombre}, Email: {email}, Asunto: {asunto}"
        )

        # Redirigir para evitar reenvío del formulario
        return redirect(url_for("main.contacto"))

    # GET request - mostrar formulario
    return render_template("contacto.html")


@main_bp.route("/dashboard_user")
def dashboard_user():
    # Protección: requerir login
    if not session.get("username") and not session.get("user_id"):
        flash("Debe iniciar sesión para acceder al dashboard de usuario", "warning")
        return redirect(url_for("auth.login", next=request.url))
    if session.get("role") == "admin":
        flash("Eres administrador. Redirigido a tu panel de administración.", "info")
        return redirect(url_for("admin.dashboard_admin"))

    # =========================================================================
    # VERIFICACIÓN CRÍTICA: DETECTAR CONTRASEÑA TEMPORAL
    # =========================================================================
    user_id = session.get("user_id")
    if user_id:
        try:
            from bson import ObjectId
            from app.models.database import get_users_collection

            users_collection = get_users_collection()
            user = users_collection.find_one({"_id": ObjectId(user_id)})

            if user:
                # Verificar si tiene contraseña temporal
                has_temp_password = (
                    user.get("temp_password", False)
                    or user.get("must_change_password", False)
                    or user.get("password_reset_required", False)
                )

                if has_temp_password:
                    # Usuario con contraseña temporal - redirigir INMEDIATAMENTE
                    session["temp_reset_user_id"] = str(user.get("_id"))
                    session["temp_reset_email"] = user.get("email", "")
                    session["temp_reset_username"] = user.get("username", "")

                    flash(
                        "ATENCIÓN: Tu cuenta usa una contraseña temporal. Debes crear una nueva contraseña para usar el sistema completo.",
                        "error",
                    )
                    return redirect(url_for("auth.temp_password_reset"))

        except Exception as e:
            print(f"[ERROR] Error verificando contraseña temporal: {e}")
            # Continuar normal si hay error, no bloquear el acceso
    # Acceso solo a datos propios
    username = session.get("username")
    email = session.get("email")
    nombre = session.get("nombre", username)
    posibles = set([username, email, nombre])
    posibles = {v for v in posibles if v}
    db = get_mongo_db()
    print(f"[DEBUG] db: {db}")
    print(f"[DEBUG] posibles: {posibles}")
    if db is None:
        flash(
            "No se pudo acceder a la base de datos. Contacte con el administrador.",
            "error",
        )
        return render_template(
            "error.html",
            mensaje="No se pudo conectar a la base de datos. Contacte con el administrador.",
        )
    try:
        tablas = []
        catalogos = []
        # Unificar criterio: buscar por todos los campos posibles
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
        try:
            tablas = list(g.spreadsheets_collection.find(query).sort("created_at", -1))
            print(f"[DEBUG] tablas: {tablas}")
        except Exception as e:
            print(f"[ERROR] Consulta a spreadsheets falló: {e}")
            tablas = []
        try:
            catalogos = list(g.catalogs_collection.find(query).sort("created_at", -1))
            print(f"[DEBUG] catalogos: {catalogos}")
        except Exception as e:
            print(f"[ERROR] Consulta a catalogs falló: {e}")
            catalogos = []
        print(
            f"[DASHBOARD_USER] Tablas encontradas: {len(tablas)} | Catálogos encontrados: {len(catalogos)}"
        )

        # Refuerzo: normalizar y serializar campos
        def safe_str(val):
            if isinstance(val, datetime):
                return val.strftime("%Y-%m-%d %H:%M:%S")
            return str(val) if val is not None else ""

        current_app.logger.info(
            f"[DEBUG_TABLAS] Procesando {len(tablas)} tablas encontradas"
        )
        for t in tablas:
            current_app.logger.info(
                f"[DEBUG_TABLA_INDIVIDUAL] Procesando tabla: {t.get('name', 'Sin nombre')}"
            )
            t["tipo"] = "spreadsheet"
            # Unificación: sincronizar 'rows' y 'data'
            if "rows" in t and t["rows"] is not None:
                t["data"] = t["rows"]
            elif "data" in t and t["data"] is not None:
                t["rows"] = t["data"]
            else:
                t["data"] = []
                t["rows"] = []
            t["row_count"] = len(t["rows"])
            t["_id"] = safe_str(t.get("_id"))
            t["created_at"] = safe_str(t.get("created_at"))
            t["owner"] = (
                t.get("owner")
                or t.get("created_by")
                or t.get("owner_name")
                or t.get("email")
                or t.get("username")
                or t.get("name")
                or ""
            )
            t["name"] = t.get("name", "")
            # 🖼️ Miniatura: priorizar miniatura personalizada, luego buscar automáticamente
            current_app.logger.info(
                f"[DEBUG_MINIATURA] Procesando tabla: {t.get('name', 'Sin nombre')}"
            )

            # 1. Verificar si tiene miniatura personalizada configurada
            if t.get("miniatura") and t["miniatura"].strip():
                current_app.logger.info(
                    f"[MINIATURA_CUSTOM] Usando miniatura personalizada: {t['miniatura']}"
                )
                # Ya está configurada, no hacer nada más
                continue

            # 2. Si no tiene miniatura personalizada, buscar automáticamente
            t["miniatura"] = ""

            # Buscar en todas las filas hasta encontrar una imagen
            for row in t.get("data", []):
                if not isinstance(row, dict):
                    continue

                imagen_encontrada = None

                # 1. Verificar campo "Imagen" (URLs externas como Unsplash)
                if row.get("Imagen") and row["Imagen"].startswith("http"):
                    imagen_encontrada = row["Imagen"]

                # 2. Si no hay imagen externa, buscar en campos de imágenes locales
                if not imagen_encontrada:
                    # Verificar campos de imágenes locales
                    for campo in ["imagenes", "images", "imagen_data"]:
                        if campo in row and row[campo]:
                            imgs = (
                                row[campo]
                                if isinstance(row[campo], list)
                                else [row[campo]]
                            )
                            for img in imgs:
                                if img and img != "N/A" and not img.startswith("http"):
                                    # Verificar si S3 está habilitado
                                    use_s3 = (
                                        os.environ.get("USE_S3", "false").lower()
                                        == "true"
                                    )
                                    if use_s3:
                                        from app.utils.s3_utils import get_s3_url

                                        s3_url = get_s3_url(img)
                                        if s3_url:
                                            imagen_encontrada = s3_url
                                        else:
                                            imagen_encontrada = url_for(
                                                "static", filename=f"uploads/{img}"
                                            )
                                    else:
                                        imagen_encontrada = url_for(
                                            "static", filename=f"uploads/{img}"
                                        )
                                    break
                        if imagen_encontrada:
                            break

                # Si encontramos una imagen, salir del bucle
                if imagen_encontrada:
                    t["miniatura"] = imagen_encontrada
                    current_app.logger.info(
                        f"[MINIATURA] Encontrada para tabla {t.get('name', 'Sin nombre')}: {imagen_encontrada}"
                    )
                    break

            # Si no se encontró ninguna imagen, dejar vacío (se mostrará "—")
            if not t["miniatura"]:
                current_app.logger.info(
                    f"[MINIATURA] No se encontró imagen para tabla {t.get('name', 'Sin nombre')}"
                )
        for c in catalogos:
            c["tipo"] = "catalog"
            # Unificación: sincronizar 'rows' y 'data'
            if "rows" in c and c["rows"] is not None:
                c["data"] = c["rows"]
            elif "data" in c and c["data"] is not None:
                c["rows"] = c["data"]
            else:
                c["data"] = []
                c["rows"] = []
            c["row_count"] = len(c["rows"])
            c["_id"] = safe_str(c.get("_id"))
            c["created_at"] = safe_str(c.get("created_at"))
            c["owner"] = (
                c.get("owner")
                or c.get("created_by")
                or c.get("owner_name")
                or c.get("email")
                or c.get("username")
                or c.get("name")
                or ""
            )
            c["name"] = c.get("name", "")
            # Miniatura: primera imagen de la primera fila
            c["miniatura"] = ""
            if c["data"] and isinstance(c["data"][0], dict):
                row = c["data"][0]
                imagenes = []
                if "imagenes" in row and row["imagenes"]:
                    imagenes = (
                        row["imagenes"]
                        if isinstance(row["imagenes"], list)
                        else [row["imagenes"]]
                    )
                elif "images" in row and row["images"]:
                    imagenes = (
                        row["images"]
                        if isinstance(row["images"], list)
                        else [row["images"]]
                    )
                elif "imagen" in row and row["imagen"]:
                    imagenes = (
                        row["imagen"]
                        if isinstance(row["imagen"], list)
                        else [row["imagen"]]
                    )
                if imagenes:
                    img = imagenes[0]
                    if img.startswith("http"):
                        c["miniatura"] = img
                    else:
                        # Verificar si S3 está habilitado
                        use_s3 = os.environ.get("USE_S3", "false").lower() == "true"
                        if use_s3:
                            from app.utils.s3_utils import get_s3_url

                            s3_url = get_s3_url(img)
                            if s3_url:
                                c["miniatura"] = s3_url
                            else:
                                c["miniatura"] = url_for(
                                    "static", filename=f"uploads/{img}"
                                )
                        else:
                            # Usar URL local directamente
                            c["miniatura"] = url_for(
                                "static", filename=f"uploads/{img}"
                            )
        registros = tablas + catalogos
        current_app.logger.info(
            f"[DEBUG_REGISTROS] Total registros a enviar al template: {len(registros)}"
        )
        for i, reg in enumerate(registros):
            current_app.logger.info(
                f"[DEBUG_REG_{i}] Nombre: {reg.get('name')}, Tipo: {reg.get('tipo')}, Miniatura: {reg.get('miniatura', 'NO_SET')}"
            )

        if not registros:
            flash("No tienes catálogos ni tablas asociados a tu usuario.", "info")
            return render_template("dashboard_unificado.html", registros=[])
        return render_template("dashboard_unificado.html", registros=registros)
    except Exception as e:
        print(f"[ERROR][DASHBOARD_USER] {e}")
        flash("Error al cargar tus catálogos/tablas.", "error")
        return render_template("dashboard_unificado.html", registros=[])


@main_bp.route("/editar/<id>", methods=["GET", "POST"])
def editar(id):
    # Eliminar verificaciones de sesión y permisos
    # if "username" not in session:
    #     return redirect(url_for("auth.login"))
    if "selected_table" not in session:
        # Si no hay tabla seleccionada, usar el ID proporcionado para buscar la tabla
        try:
            table_info = g.spreadsheets_collection.find_one(  # type: ignore
                {"_id": ObjectId(id)}
            )
            if table_info:
                selected_table = table_info.get("filename")
                session["selected_table"] = selected_table
            else:
                flash("Tabla no encontrada.", "error")
                return redirect(url_for("main.tables"))
        except Exception as e:
            logger.error(f"Error al buscar tabla por ID: {str(e)}")
            flash("Error al buscar la tabla.", "error")
            return redirect(url_for("main.tables"))
    else:
        selected_table = session["selected_table"]
        table_info = g.spreadsheets_collection.find_one(  # type: ignore
            {"filename": selected_table}
        )
        if not table_info:
            flash("Tabla no encontrada.", "error")
            return redirect(url_for("main.tables"))
    # Control de acceso: solo admin o dueño puede editar
    if session.get("role") != "admin" and table_info.get("owner") != session.get(
        "username"
    ):
        flash("No tiene permisos para editar esta tabla", "error")
        return redirect(url_for("main.tables"))

    if request.method == "POST":
        nuevo_nombre = request.form.get("nombre", "").strip()
        nuevos_headers = [
            h.strip() for h in request.form.get("headers", "").split(",") if h.strip()
        ]
        update = {}
        if nuevo_nombre:
            update["name"] = nuevo_nombre
        if nuevos_headers:
            update["headers"] = nuevos_headers
        if update:
            g.spreadsheets_collection.update_one(
                {"filename": selected_table}, {"$set": update}
            )
            flash("Tabla actualizada correctamente.", "success")
        else:
            flash("No se detectaron cambios.", "info")
        return redirect(url_for("main.ver_tabla", table_id=id))

    # GET: mostrar formulario de edición
    return render_template("editar_tabla.html", table=table_info)


@main_bp.route("/ver_tabla/<table_id>")
@login_required
def ver_tabla(table_id):
    try:
        table = g.spreadsheets_collection.find_one({"_id": ObjectId(table_id)})

        # Asegurarse de que el propietario esté disponible
        if "owner" not in table and "owner_name" in table:
            table["owner"] = table["owner_name"]
        elif "owner" not in table and "created_by" in table:
            table["owner"] = table["created_by"]
        elif "owner" not in table:
            table["owner"] = "Usuario desconocido"

        current_app.logger.info(
            f"[DEBUG][VISIONADO] Propietario de la tabla: {table.get('owner')}"
        )
        current_app.logger.info(
            f"[DEBUG][VISIONADO] Campos de la tabla: {list(table.keys())}"
        )

        # Asegurarse de que los datos estén disponibles
        if "data" not in table and "rows" in table:
            table["data"] = table["rows"]
            current_app.logger.info(
                f"[DEBUG][VISIONADO] Usando 'rows' como 'data', filas: {len(table['data'])}"
            )
        elif "data" not in table:
            table["data"] = []
            current_app.logger.info(
                "[DEBUG][VISIONADO] No se encontraron datos en la tabla"
            )
        if not table:
            flash("Tabla no encontrada.", "error")
            return redirect(url_for("main.dashboard_user"))

        # Log de sesión y permisos
        current_app.logger.info(f"[DEBUG][VISIONADO] Sesión: {dict(session)}")
        current_app.logger.info(
            f"[DEBUG][VISIONADO] table.owner: {table.get('owner')}, session.username: {session.get('username')}, session.role: {session.get('role')}"
        )

        # Normalizar el campo owner si está vacío o es usuario_predeterminado
        username = session.get("username")
        role = session.get("role", "user")

        if (
            "owner" not in table
            or not table["owner"]
            or table["owner"] == "usuario_predeterminado"
        ):
            # Buscar el propietario en otros campos
            if "created_by" in table and table["created_by"]:
                table["owner"] = table["created_by"]
                current_app.logger.info(
                    f"[DEBUG][VISIONADO] Usando created_by como owner: {table['owner']}"
                )
            elif "username" in table and table["username"]:
                table["owner"] = table["username"]
                current_app.logger.info(
                    f"[DEBUG][VISIONADO] Usando username como owner: {table['owner']}"
                )
            else:
                # Si no hay información de propietario, asignar al usuario actual
                g.spreadsheets_collection.update_one(
                    {"_id": ObjectId(table_id)}, {"$set": {"owner": username}}
                )
                table["owner"] = username
                current_app.logger.info(
                    f"[DEBUG][VISIONADO] Actualizado propietario de tabla {table_id} a {username}"
                )

        # Verificar permisos: solo el propietario o admin puede ver la tabla
        if role != "admin" and table.get("owner") != username:
            mensaje = (
                f"No tiene permisos para ver esta tabla. "
                f"(owner={table.get('owner')}, username={username}, role={role})"
            )
            current_app.logger.warning(f"[DEBUG][VISIONADO] {mensaje}")
            flash(mensaje, "warning")
            return redirect(url_for("main.tables"))

        # Si llegamos aquí, el usuario tiene permisos para ver la tabla
        # Procesar las imágenes en cada fila usando función unificada
        for i, row in enumerate(table.get("data", [])):
            if not isinstance(row, dict):
                current_app.logger.warning(
                    f"[VISIONADO] Fila {i} ignorada por no ser un dict: {row}"
                )
                continue

            current_app.logger.info(f"[DEBUG][VISIONADO] Procesando fila {i}: {row}")

            # Usar función unificada para obtener URLs de imágenes
            image_data = get_images_for_template(row)
            row.update(image_data)  # Añade imagen_urls, num_imagenes, tiene_imagenes

            current_app.logger.info(
                f"[DEBUG][VISIONADO] URLs de imágenes para fila {i}: {row.get('imagen_urls', [])}"
            )
            current_app.logger.info(
                f"[DEBUG][VISIONADO] Total de imágenes en fila {i}: {len(row.get('imagen_urls', []))}"
            )

        return render_template("ver_tabla.html", table=table)
    except BuildError as e:
        logger.error(f"BuildError en ver_tabla: {str(e)}", exc_info=True)
        flash("Error interno: ruta no encontrada o mal configurada.", "danger")
        return render_template(
            "error.html", error="Error interno: ruta no encontrada o mal configurada."
        )
    except Exception as e:
        logger.error(f"Error inesperado en ver_tabla: {str(e)}", exc_info=True)
        flash("Error interno inesperado.", "danger")
        return redirect(url_for("main.dashboard_user"))


@main_bp.route("/select_table/<table_id>")
def select_table(table_id):
    # Verificar que el usuario ha iniciado sesión
    if not session.get("username"):
        flash("Debe iniciar sesión para acceder a las tablas", "warning")
        return redirect(url_for("auth.login"))

    # Obtener información del usuario actual
    username = session.get("username")
    role = session.get("role", "user")

    try:
        # Obtener la tabla
        table = g.spreadsheets_collection.find_one({"_id": ObjectId(table_id)})
        if not table:
            flash("Tabla no encontrada.", "error")
            return redirect(url_for("main.tables"))

        # Verificar permisos: administradores pueden ver todas las tablas, usuarios solo las suyas
        if role != "admin":
            # Normalizar el campo owner si está vacío o es usuario_predeterminado
            if (
                "owner" not in table
                or not table["owner"]
                or table["owner"] == "usuario_predeterminado"
            ):
                if "created_by" in table and table["created_by"]:
                    table["owner"] = table["created_by"]
                elif "username" in table and table["username"]:
                    table["owner"] = table["username"]
                else:
                    # Si no hay información de propietario, asignar al usuario actual
                    g.spreadsheets_collection.update_one(
                        {"_id": ObjectId(table_id)}, {"$set": {"owner": username}}
                    )
                    table["owner"] = username
                    logger.info(
                        f"Actualizado propietario de tabla {table_id} a {username}"
                    )

            # Verificar si el usuario actual es el propietario
            if table["owner"] != username:
                logger.warning(
                    f"Usuario {username} intentó acceder a tabla {table_id} propiedad de {table['owner']}"
                )
                flash("No tiene permisos para ver esta tabla.", "warning")
                return redirect(url_for("main.tables"))

        # Guardar información de la tabla en la sesión
        session["selected_table"] = table.get("filename", "")
        session["selected_table_id"] = str(table["_id"])
        session["selected_table_name"] = table.get("name", "Sin nombre")

        logger.info(
            f"Usuario {username} seleccionó tabla {table.get('name')} (ID: {table_id})"
        )
        return redirect(url_for("main.ver_tabla", table_id=table_id))

    except Exception as e:
        logger.error(f"Error al seleccionar tabla {table_id}: {str(e)}", exc_info=True)
        flash(f"Error al acceder a la tabla: {str(e)}", "error")
        return redirect(url_for("main.tables"))


@main_bp.route("/perfil")
def perfil():
    # Verificar si el usuario está autenticado
    if "user_id" not in session:
        flash("Debe iniciar sesión para ver su perfil", "warning")
        return redirect(url_for("auth.login"))

    try:
        # Obtener la colección de usuarios
        users_collection = getattr(g, "users_collection", None)
        if users_collection is None:
            # Importar mongo desde app.extensions
            from app.extensions import mongo

            users_collection = mongo.db.users  # type: ignore

        # Obtener datos del usuario actual
        user_data = users_collection.find_one({"_id": ObjectId(session["user_id"])})
        if not user_data:
            flash("Usuario no encontrado", "error")
            return redirect(url_for("main.dashboard_user"))

        # Crear objeto User para tener acceso a foto_perfil_url
        from app.models.user import User

        user = User(user_data)

        # Asegurar que existe la imagen de perfil predeterminada
        if current_app.static_folder is None:
            flash("Error de configuración del servidor", "error")
            return redirect(url_for("main.dashboard_user"))

        default_profile_path = os.path.join(
            current_app.static_folder, "default_profile.png"
        )
        if not os.path.exists(default_profile_path):
            try:
                # Importar la función para crear la imagen predeterminada
                from app.crear_imagen_perfil_default import crear_imagen_perfil_default

                crear_imagen_perfil_default()
                logger.info("Imagen de perfil predeterminada creada correctamente")
            except Exception as e:
                logger.error(
                    f"Error al crear imagen predeterminada: {str(e)}", exc_info=True
                )

        return render_template("perfil.html", user=user)
    except Exception as e:
        logger.error(f"Error al cargar perfil: {str(e)}", exc_info=True)
        flash("Error al cargar los datos del perfil", "error")
        return redirect(url_for("main.dashboard_user"))


@main_bp.route("/editar_perfil", methods=["GET", "POST"])
def editar_perfil():
    if "user_id" not in session:
        flash("Debe iniciar sesión para editar su perfil", "warning")
        return redirect(url_for("auth.login"))

    # Obtener la colección de usuarios
    users_collection = getattr(g, "users_collection", None)
    if users_collection is None:
        # Importar mongo desde app.extensions
        from app.extensions import mongo

        users_collection = mongo.db.users

    # Obtener datos del usuario actual
    try:
        user_data = users_collection.find_one({"_id": ObjectId(session["user_id"])})
        if not user_data:
            flash("Usuario no encontrado", "error")
            return redirect(url_for("main.dashboard_user"))

        # Crear objeto User para tener acceso a foto_perfil_url
        from app.models.user import User

        user = User(user_data)
    except Exception as e:
        logger.error(f"Error al obtener datos del usuario: {str(e)}", exc_info=True)
        flash("Error al cargar los datos del usuario", "error")
        return redirect(url_for("main.dashboard_user"))

    if request.method == "POST":
        # Obtener datos del formulario
        nombre = request.form.get("nombre")
        email = request.form.get("email")

        # Datos para cambio de contraseña
        password_actual = request.form.get("password_actual")
        password_nuevo = request.form.get("password_nuevo")
        password_confirmacion = request.form.get("password_confirmacion")

        # Actualizar en la base de datos
        update_data = {}
        if nombre:
            update_data["nombre"] = nombre
        if email:
            update_data["email"] = email

        # Procesar cambio de contraseña si se proporcionaron los campos necesarios
        if password_actual and password_nuevo and password_confirmacion:
            # Verificar que la contraseña actual sea correcta
            from werkzeug.security import check_password_hash, generate_password_hash

            if not check_password_hash(user.password_hash, password_actual):
                flash("La contraseña actual es incorrecta.", "error")
                return render_template("editar_perfil.html", user=user)

            # Verificar que las nuevas contraseñas coincidan
            if password_nuevo != password_confirmacion:
                flash("Las nuevas contraseñas no coinciden.", "error")
                return render_template("editar_perfil.html", user=user)

            # Verificar que la nueva contraseña tenga al menos 8 caracteres
            if len(password_nuevo) < 8:
                flash("La nueva contraseña debe tener al menos 8 caracteres.", "error")
                return render_template("editar_perfil.html", user=user)

            # Actualizar la contraseña
            update_data["password"] = generate_password_hash(password_nuevo)

        # Asegurarse de que existe la carpeta de uploads
        if current_app.static_folder is None:
            flash("Error de configuración del servidor", "error")
            return redirect(url_for("main.dashboard_user"))

        uploads_folder = os.path.join(current_app.static_folder, "uploads")

        # Crear la carpeta si no existe
        os.makedirs(uploads_folder, exist_ok=True)
        # Asegurar que existe la imagen de perfil predeterminada
        default_profile_path = os.path.join(
            current_app.static_folder, "default_profile.png"
        )
        if not os.path.exists(default_profile_path):
            try:
                # Importar la función para crear la imagen predeterminada
                from app.crear_imagen_perfil_default import crear_imagen_perfil_default

                crear_imagen_perfil_default()
                logger.info("Imagen de perfil predeterminada creada correctamente")
            except Exception as e:
                logger.error(
                    f"Error al crear imagen predeterminada: {str(e)}", exc_info=True
                )

        # Procesar la imagen de perfil si se ha subido una nueva
        if "foto" in request.files:
            profile_image = request.files["foto"]
            if profile_image and profile_image.filename != "":
                try:
                    # Guardar la imagen
                    filename = secure_filename(
                        f"{uuid.uuid4().hex}_{profile_image.filename}"
                    )
                    filepath = os.path.join(uploads_folder, filename)
                    profile_image.save(filepath)

                    # Subir a S3 si está habilitado
                    use_s3 = os.environ.get("USE_S3", "false").lower() == "true"
                    if use_s3:
                        try:
                            from app.utils.s3_utils import upload_file_to_s3

                            logger.info(f"Subiendo foto de perfil a S3: {filename}")
                            result = upload_file_to_s3(filepath, filename)
                            if result["success"]:
                                logger.info(
                                    f"Foto de perfil subida a S3: {result['url']}"
                                )
                                # Eliminar el archivo local después de subirlo a S3
                                os.remove(filepath)
                                logger.info(
                                    f"Foto de perfil eliminada del servidor local después de subirla a S3: {filename}"
                                )
                            else:
                                logger.error(
                                    f"Error al subir foto de perfil a S3: {result.get('error')}"
                                )
                        except Exception as e:
                            logger.error(
                                f"Error al procesar subida de foto de perfil a S3: {str(e)}",
                                exc_info=True,
                            )
                    # Actualizar el campo foto_perfil en el usuario
                    update_data["foto_perfil"] = filename
                    logger.info(f"Imagen de perfil guardada: {filename}")
                except Exception as e:
                    logger.error(
                        f"Error al guardar imagen de perfil: {str(e)}", exc_info=True
                    )
                    flash(f"Error al guardar la imagen de perfil: {str(e)}", "error")

        # Actualizar el usuario en la base de datos
        from app.extensions import mongo

        mongo.db.users.update_one(
            {"_id": ObjectId(session["user_id"])}, {"$set": update_data}
        )

        # Mostrar mensaje específico si se cambió la contraseña
        if "password" in update_data:
            flash("Perfil y contraseña actualizados correctamente.", "success")
            # Actualizar la sesión para reflejar los cambios
            if "email" in update_data:
                session["email"] = update_data["email"]
            if "nombre" in update_data and update_data["nombre"]:
                session["username"] = update_data["nombre"]
            # Redirigir al login para que el usuario inicie sesión con la nueva contraseña
            session.clear()
            flash("Por favor, inicie sesión con su nueva contraseña.", "info")
            return redirect(url_for("auth.login"))
        else:
            flash("Perfil actualizado correctamente.", "success")
            # Actualizar la sesión para reflejar los cambios
            if "email" in update_data:
                session["email"] = update_data["email"]
            if "nombre" in update_data and update_data["nombre"]:
                session["username"] = update_data["nombre"]
            return redirect(url_for("main.perfil"))

    # Para peticiones GET, mostrar el formulario con los datos actuales
    return render_template("editar_perfil.html", user=user)


@main_bp.route("/editar_fila/<tabla_id>/<int:fila_index>", methods=["GET", "POST"])
@login_required
def editar_fila(tabla_id, fila_index):
    print(f"🔥🔥🔥 EDITAR_FILA EJECUTADO: tabla_id={tabla_id}, fila_index={fila_index}")
    current_app.logger.error(
        f"🔥🔥🔥 EDITAR_FILA EJECUTADO: tabla_id={tabla_id}, fila_index={fila_index}"
    )
    current_app.logger.info(
        f"[DEBUG] Valores recibidos: tabla_id={tabla_id}, fila_index={fila_index}"
    )

    # 🔥 OBTENER INFO FRESCA USANDO LA MISMA LÓGICA QUE VER_TABLA 🔥
    current_app.logger.info(
        f"[DEBUG_EDIT] Recargando datos frescos desde MongoDB para tabla {tabla_id}"
    )

    # USAR EXACTAMENTE LA MISMA LÓGICA QUE VER_TABLA
    table_info = g.spreadsheets_collection.find_one({"_id": ObjectId(tabla_id)})
    if not table_info:
        flash("Tabla no encontrada.", "error")
        return redirect(url_for("main.tables"))

    # Asegurarse de que el propietario esté disponible (igual que ver_tabla)
    if "owner" not in table_info and "owner_name" in table_info:
        table_info["owner"] = table_info["owner_name"]
    elif "owner" not in table_info and "created_by" in table_info:
        table_info["owner"] = table_info["created_by"]
    elif "owner" not in table_info:
        table_info["owner"] = "Usuario desconocido"

    # Asegurarse de que los datos estén disponibles (igual que ver_tabla)
    if "data" not in table_info and "rows" in table_info:
        table_info["data"] = table_info["rows"]
        current_app.logger.info(
            f"[DEBUG_EDIT] Usando 'rows' como 'data', filas: {len(table_info['data'])}"
        )
    elif "data" not in table_info:
        table_info["data"] = []
        current_app.logger.info("[DEBUG_EDIT] No se encontraron datos en la tabla")

    # 🚨 NO SOBRESCRIBIR DATA CON ROWS - data tiene las imágenes actualizadas
    current_app.logger.info(
        f"[DEBUG_EDIT] ANTES sincronización - data tiene {len(table_info.get('data', []))} filas, rows tiene {len(table_info.get('rows', []))} filas"
    )

    # Solo sincronizar si data está vacío pero rows tiene datos
    if (
        not table_info.get("data") or len(table_info.get("data", [])) == 0
    ) and table_info.get("rows"):
        current_app.logger.info("[DEBUG_EDIT] Copiando rows → data (data estaba vacío)")
        table_info["data"] = table_info["rows"]
    elif table_info.get("data") and (
        not table_info.get("rows") or len(table_info.get("rows", [])) == 0
    ):
        current_app.logger.info("[DEBUG_EDIT] Copiando data → rows (rows estaba vacío)")
        table_info["rows"] = table_info["data"]
    else:
        current_app.logger.info("[DEBUG_EDIT] PRESERVANDO data original con imágenes")

    table_info["row_count"] = len(table_info.get("data", []))

    # Verificar permisos: solo el propietario o admin puede editar filas
    username = session.get("username")
    role = session.get("role", "user")

    # Obtener el propietario de la tabla (puede estar en diferentes campos)
    owner = (
        table_info.get("owner")
        or table_info.get("created_by")
        or table_info.get("owner_name")
    )

    current_app.logger.info(
        f"[DEBUG] Verificando permisos: role={role}, username={username}, owner={owner}"
    )

    if role != "admin" and owner != username:
        current_app.logger.warning(
            f"[DEBUG] Permiso denegado: {username} intentando editar tabla de {owner}"
        )
        flash("No tienes permisos para editar esta fila.", "warning")
        return redirect(url_for("main.ver_tabla", table_id=tabla_id))

    # Obtener la fila específica del array de datos
    data_length = len(table_info.get("data", []))
    current_app.logger.info(
        f"[DEBUG] fila_index={fila_index}, data_length={data_length}, num_rows={table_info.get('num_rows', 'N/A')}"
    )
    current_app.logger.info(f"[DEBUG] table_info.keys(): {list(table_info.keys())}")

    if not table_info.get("data") or fila_index >= data_length:
        current_app.logger.error(
            f"[DEBUG] Fila no encontrada: índice {fila_index} >= longitud {data_length}"
        )
        flash("Fila no encontrada.", "error")
        return redirect(url_for("main.ver_tabla", table_id=tabla_id))

    # Obtener la fila específica - usar "data" que tiene imágenes completas
    fila = table_info["data"][fila_index]
    current_app.logger.info(
        f"[DEBUG_EDIT] Datos completos de fila {fila_index}: {fila}"
    )

    # 🔥 DEBUG ADICIONAL: Verificar qué contiene cada campo de imagen 🔥
    current_app.logger.info(
        f"[DEBUG_EDIT] fila.get('images'): {fila.get('images')} (tipo: {type(fila.get('images'))})"
    )
    current_app.logger.info(
        f"[DEBUG_EDIT] fila.get('imagenes'): {fila.get('imagenes')} (tipo: {type(fila.get('imagenes'))})"
    )
    current_app.logger.info(
        f"[DEBUG_EDIT] fila.get('imagen_data'): {fila.get('imagen_data')} (tipo: {type(fila.get('imagen_data'))})"
    )
    current_app.logger.info(
        f"[DEBUG_EDIT] Campos de imagen disponibles: imagenes={fila.get('imagenes')}, imagen_data={fila.get('imagen_data')}, images={fila.get('images')}"
    )

    # 🔥🔥🔥 PROCESAMIENTO MANUAL DE IMÁGENES UNIFICADAS 🔥🔥🔥
    imagenes_unificadas = []

    # Recopilar de fila.images
    if fila.get("images") and isinstance(fila["images"], list):
        for img in fila["images"]:
            if (
                img
                and img != "N/A"
                and not img.startswith("http")
                and img not in imagenes_unificadas
            ):
                imagenes_unificadas.append(img)

    # Recopilar de fila.imagenes
    if fila.get("imagenes") and isinstance(fila["imagenes"], list):
        for img in fila["imagenes"]:
            if (
                img
                and img != "N/A"
                and not img.startswith("http")
                and img not in imagenes_unificadas
            ):
                imagenes_unificadas.append(img)

    # Recopilar de fila.imagen_data
    if fila.get("imagen_data") and isinstance(fila["imagen_data"], list):
        for img in fila["imagen_data"]:
            if (
                img
                and img != "N/A"
                and not img.startswith("http")
                and img not in imagenes_unificadas
            ):
                imagenes_unificadas.append(img)

    # 🆕 RECOPILAR DE FILA.IMAGEN (CAMPO STRING) - PARA IMÁGENES UNSPLASH
    imagen_individual = fila.get("Imagen", "")
    if (
        imagen_individual
        and imagen_individual != "N/A"
        and imagen_individual.startswith("http")
    ):
        current_app.logger.info(
            f"[DEBUG_EDIT] Imagen externa encontrada: {imagen_individual}"
        )
        # Las imágenes externas (Unsplash) no se pueden eliminar, pero necesitamos mostrarlas
        # Para eso, creamos un campo especial para mostrar sin opción de eliminar

    # Preparar contexto para el template con imágenes unificadas
    fila["_imagenes_unificadas"] = imagenes_unificadas
    fila["_imagen_externa"] = (
        imagen_individual
        if imagen_individual and imagen_individual.startswith("http")
        else None
    )
    current_app.logger.error(
        f"[DEBUG_EDIT] IMÁGENES UNIFICADAS: {len(imagenes_unificadas)} → {imagenes_unificadas}"
    )
    current_app.logger.error(
        f"[DEBUG_EDIT] TEMPLATE CONTEXT: Todos los keys de fila = {list(fila.keys())}"
    )
    headers = table_info.get("headers", [])

    if request.method == "POST":
        update_data = {}
        for header in headers:
            if header != "Número" and header != "Imagenes":
                # Usamos notación de diccionario para manejar campos con espacios
                # En lugar de usar dot notation directamente en la clave
                campo_valor = request.form.get(header, "").strip()
                data_key = f"data.{fila_index}"

                # Si el campo no existe en update_data, creamos un diccionario vacío
                if data_key not in update_data:
                    update_data[data_key] = {}

                # Ahora agregamos el campo al diccionario
                update_data[data_key][header] = campo_valor

        # 🆕 PROCESAR ESPECÍFICAMENTE EL CAMPO 'Imagen' (URL EXTERNA)
        imagen_url = request.form.get("Imagen", "").strip()
        data_key = f"data.{fila_index}"
        if data_key not in update_data:
            update_data[data_key] = {}
        update_data[data_key]["Imagen"] = imagen_url
        current_app.logger.info(
            f"[DEBUG_EDIT] Actualizando campo Imagen: '{imagen_url}'"
        )

        # Procesar imágenes a eliminar
        imagenes_a_eliminar = request.form.get("imagenes_a_eliminar", "")
        if imagenes_a_eliminar:
            try:
                import json

                imagenes_a_eliminar = json.loads(imagenes_a_eliminar)
                logger.info(f"Imágenes a eliminar: {imagenes_a_eliminar}")

                # Asegurarse de que fila tenga el campo 'imagenes'
                if "imagenes" not in fila:
                    fila["imagenes"] = []
                    logger.info("Inicializando campo 'imagenes' en la fila")

                # Verificar si imagenes es un número entero (contador) en lugar de una lista
                if isinstance(fila.get("imagenes"), int):
                    logger.info(f"Campo 'imagenes' es un entero: {fila['imagenes']}")
                    # Buscar imágenes reales en otros campos
                    if "imagen_data" in fila:
                        fila["imagenes"] = fila["imagen_data"]
                        logger.info(
                            f"Usando 'imagen_data' como fuente de imágenes: {fila['imagenes']}"
                        )
                    else:
                        fila["imagenes"] = []
                        logger.info(
                            "No se encontraron imágenes reales, inicializando lista vacía"
                        )

                # Asegurarse de que imagenes sea una lista
                if not isinstance(fila["imagenes"], list):
                    fila["imagenes"] = [fila["imagenes"]] if fila["imagenes"] else []
                    logger.info(
                        f"Convertido campo 'imagenes' a lista: {fila['imagenes']}"
                    )

                if isinstance(imagenes_a_eliminar, list):
                    # Eliminar las imágenes del servidor y de S3
                    if current_app.static_folder is None:
                        logger.error(
                            "Error de configuración del servidor: static_folder es None"
                        )
                        flash("Error de configuración del servidor", "error")
                        return redirect(url_for("main.tables"))
                    ruta_uploads = os.path.join(current_app.static_folder, "uploads")
                    use_s3 = os.environ.get("USE_S3", "false").lower() == "true"

                    for img_a_eliminar in imagenes_a_eliminar:
                        try:
                            # Eliminar de S3 si está habilitado
                            if use_s3:
                                from app.utils.s3_utils import delete_file_from_s3

                                delete_file_from_s3(img_a_eliminar)
                                logger.info(f"Imagen eliminada de S3: {img_a_eliminar}")

                            # Eliminar del servidor local
                            ruta_img = os.path.join(ruta_uploads, img_a_eliminar)
                            if os.path.exists(ruta_img):
                                os.remove(ruta_img)
                                logger.info(
                                    f"Imagen eliminada del servidor local: {img_a_eliminar}"
                                )
                        except Exception as e:
                            logger.error(
                                f"Error al eliminar imagen: {str(e)}", exc_info=True
                            )

                    # Actualizar la lista de imágenes en la fila
                    imagenes_actualizadas = [
                        img
                        for img in fila.get("imagenes", [])
                        if img not in imagenes_a_eliminar
                    ]
                    update_data[f"data.{fila_index}.imagenes"] = imagenes_actualizadas
                    logger.info(
                        f"Lista de imágenes actualizada: {imagenes_actualizadas}"
                    )

                    # Actualizar también el campo imagen_data si existe
                    if "imagen_data" in fila:
                        update_data[f"data.{fila_index}.imagen_data"] = (
                            imagenes_actualizadas
                        )
                        logger.info(
                            "Campo 'imagen_data' actualizado con la misma lista de imágenes"
                        )

                    # Si no quedan imágenes, establecer el contador a 0
                    if not imagenes_actualizadas and isinstance(
                        fila.get("imagenes"), int
                    ):
                        update_data[f"data.{fila_index}.imagenes"] = 0
                        logger.info("No quedan imágenes, contador establecido a 0")
            except Exception as e:
                logger.error(f"Error al procesar imágenes a eliminar: {str(e)}")

        # Procesar nuevas imágenes si existen
        nuevas_imagenes = []
        if "imagenes" in request.files:
            archivos = request.files.getlist("imagenes")
            # Limitar a máximo 3 imágenes
            archivos = archivos[:3] if len(archivos) > 3 else archivos

            logger.info(f"Procesando {len(archivos)} nuevas imágenes")

            for archivo in archivos:
                if archivo and archivo.filename.strip():
                    # Generar nombre seguro y único para el archivo
                    nombre_seguro = secure_filename(archivo.filename)
                    extension = os.path.splitext(nombre_seguro)[1].lower()
                    nombre_unico = f"{uuid.uuid4().hex}{extension}"

                    # Verificar que sea una imagen válida
                    if extension.lower() not in [".jpg", ".jpeg", ".png", ".gif"]:
                        logger.warning(f"Extensión no válida para imagen: {extension}")
                        continue

                    # Guardar la imagen en la carpeta de uploads
                    if current_app.static_folder is None:
                        logger.error(
                            "Error de configuración del servidor: static_folder es None"
                        )
                        continue
                    ruta_uploads = os.path.join(current_app.static_folder, "uploads")
                    if not os.path.exists(ruta_uploads):
                        os.makedirs(ruta_uploads)
                        logger.info(f"Carpeta de uploads creada: {ruta_uploads}")

                    ruta_completa = os.path.join(ruta_uploads, nombre_unico)
                    archivo.save(ruta_completa)
                    logger.info(f"Imagen guardada localmente: {ruta_completa}")

                    # Subir a S3 si está habilitado
                    use_s3 = os.environ.get("USE_S3", "false").lower() == "true"
                    logger.info(f"USE_S3: {use_s3}")
                    if use_s3:
                        try:
                            from app.utils.s3_utils import upload_file_to_s3

                            logger.info(f"Subiendo imagen a S3: {nombre_unico}")

                            result = upload_file_to_s3(ruta_completa, nombre_unico)
                            if result["success"]:
                                logger.info(f"Imagen subida a S3: {result['url']}")
                                # Eliminar el archivo local después de subirlo a S3
                                os.remove(ruta_completa)
                                logger.info(
                                    f"Imagen eliminada del servidor local después de subirla a S3: {nombre_unico}"
                                )
                            else:
                                logger.error(
                                    f"Error al subir imagen a S3: {result.get('error')}"
                                )
                        except Exception as e:
                            logger.error(
                                f"Error al procesar subida a S3: {str(e)}",
                                exc_info=True,
                            )

                    nuevas_imagenes.append(nombre_unico)

        # Si hay nuevas imágenes, actualizar la lista en la base de datos
        if nuevas_imagenes:
            logger.info(f"Nuevas imágenes a guardar: {nuevas_imagenes}")

            # Verificar si el campo imagenes es un número entero (contador)
            if "imagenes" in fila and isinstance(fila["imagenes"], int):
                logger.info(f"Campo 'imagenes' es un entero: {fila['imagenes']}")
                # Si es un contador, actualizar el campo imagen_data
                if "imagen_data" in fila and isinstance(fila["imagen_data"], list):
                    # Añadir las nuevas imágenes a imagen_data
                    update_data[f"data.{fila_index}.imagen_data"] = (
                        fila["imagen_data"] + nuevas_imagenes
                    )
                    # Actualizar el contador
                    update_data[f"data.{fila_index}.imagenes"] = len(
                        fila["imagen_data"]
                    ) + len(nuevas_imagenes)
                    logger.info(
                        f"Actualizando contador de imágenes a {update_data[f'data.{fila_index}.imagenes']}"
                    )
                else:
                    # Crear el campo imagen_data
                    update_data[f"data.{fila_index}.imagen_data"] = nuevas_imagenes
                    # Actualizar el contador
                    update_data[f"data.{fila_index}.imagenes"] = len(nuevas_imagenes)
                    logger.info(
                        f"Creando campo imagen_data con {len(nuevas_imagenes)} imágenes"
                    )
            else:
                # Si ya se actualizaron las imágenes por eliminación, agregar las nuevas a las restantes
                if f"data.{fila_index}.imagenes" in update_data:
                    update_data[f"data.{fila_index}.imagenes"] = (
                        update_data[f"data.{fila_index}.imagenes"] + nuevas_imagenes
                    )
                    logger.info(
                        f"Añadiendo nuevas imágenes a la lista actualizada: {update_data[f'data.{fila_index}.imagenes']}"
                    )
                else:
                    # Si ya hay imágenes, añadir las nuevas
                    if "imagenes" in fila and isinstance(fila["imagenes"], list):
                        update_data[f"data.{fila_index}.imagenes"] = (
                            fila["imagenes"] + nuevas_imagenes
                        )
                        logger.info(
                            f"Añadiendo nuevas imágenes a la lista existente: {fila['imagenes'] + nuevas_imagenes}"
                        )
                    else:
                        # Si no hay imágenes previas, crear la lista
                        update_data[f"data.{fila_index}.imagenes"] = nuevas_imagenes
                        logger.info(
                            f"Creando nueva lista de imágenes: {nuevas_imagenes}"
                        )

                # Actualizar también imagen_data si existe
                if "imagen_data" in fila:
                    if isinstance(fila["imagen_data"], list):
                        update_data[f"data.{fila_index}.imagen_data"] = (
                            fila["imagen_data"] + nuevas_imagenes
                        )
                    else:
                        update_data[f"data.{fila_index}.imagen_data"] = nuevas_imagenes
                    logger.info(
                        "Actualizando campo imagen_data con las mismas imágenes"
                    )

        # Preparar la actualización para MongoDB
        mongo_update = {}

        # Manejar los campos principales
        for key, value in update_data.items():
            if isinstance(value, dict):
                # Si es un diccionario, lo manejamos con $set en campos individuales
                for subkey, subvalue in value.items():
                    # Escapar los nombres de campos que tienen caracteres especiales
                    mongo_update[f"{key}.{subkey}"] = subvalue
            else:
                # Si no es un diccionario, lo manejamos directamente
                mongo_update[key] = value

        current_app.logger.info(f"Actualizando documento con datos: {mongo_update}")

        # Actualizar la fila en la base de datos
        g.spreadsheets_collection.update_one(
            {"_id": ObjectId(tabla_id)}, {"$set": mongo_update}
        )

        flash("Fila actualizada correctamente.", "success")

        # Calcular la página donde está la fila editada
        filas_por_pagina = 10
        pagina_fila = (fila_index // filas_por_pagina) + 1

        current_app.logger.info(f"[REDIRECT] Fila {fila_index} → Página {pagina_fila}")

        # Construir URL con parámetros de forma más robusta
        from urllib.parse import urlencode

        base_url = url_for("main.ver_tabla", table_id=tabla_id)
        params = {"page": pagina_fila}
        fragment = f"fila-{fila_index + 1}"  # Mostrar número de fila desde 1
        redirect_url = f"{base_url}?{urlencode(params)}#{fragment}"

        current_app.logger.info(f"[REDIRECT] URL final: {redirect_url}")

        return redirect(redirect_url)

    return render_template(
        "editar_fila.html",
        fila=fila,
        headers=headers,
        catalog=table_info,
        tabla_id=tabla_id,
        fila_index=fila_index,
    )


@main_bp.route("/agregar_fila/<tabla_id>", methods=["GET", "POST"])
def agregar_fila(tabla_id):
    current_app.logger.info(
        f"[AGREGAR_FILA] Iniciando agregar_fila para tabla_id: {tabla_id}, método: {request.method}"
    )

    # Verificar sesión
    if not session.get("logged_in") or "username" not in session:
        flash("Debe iniciar sesión para agregar filas", "warning")
        return redirect(url_for("auth.login"))

    try:
        # Obtener la tabla
        tabla = g.spreadsheets_collection.find_one({"_id": ObjectId(tabla_id)})
        if not tabla:
            flash("Tabla no encontrada", "error")
            return redirect(url_for("main.dashboard_user"))

        # Verificar permisos: solo el propietario o admin puede agregar filas
        username = session.get("username")
        role = session.get("role", "user")

        # Obtener el propietario de la tabla (puede estar en diferentes campos)
        owner = tabla.get("owner") or tabla.get("created_by") or tabla.get("owner_name")

        current_app.logger.info(
            f"[DEBUG] Verificando permisos para agregar fila: role={role}, username={username}, owner={owner}"
        )

        if role != "admin" and owner != username:
            current_app.logger.warning(
                f"[DEBUG] Permiso denegado para agregar fila: {username} intentando modificar tabla de {owner}"
            )
            flash("No tiene permisos para agregar filas a esta tabla", "warning")
            return redirect(url_for("main.ver_tabla", table_id=tabla_id))

        if request.method == "POST":
            # Obtener datos del formulario
            nueva_fila = {}
            for header in tabla.get("headers", []):
                nueva_fila[header] = request.form.get(header, "")

            # Procesar imágenes si existen
            imagenes = []
            if "imagenes" in request.files:
                archivos = request.files.getlist("imagenes")
                # Limitar a máximo 3 imágenes
                archivos = archivos[:3] if len(archivos) > 3 else archivos

                logger.info(f"Procesando {len(archivos)} imágenes para nueva fila")

                for archivo in archivos:
                    if archivo and archivo.filename.strip():
                        # Generar nombre seguro y único para el archivo
                        nombre_seguro = secure_filename(archivo.filename)
                        extension = os.path.splitext(nombre_seguro)[1].lower()
                        nombre_unico = f"{uuid.uuid4().hex}{extension}"

                        # Verificar que sea una imagen válida
                        if extension.lower() not in [".jpg", ".jpeg", ".png", ".gif"]:
                            logger.warning(
                                f"Extensión no válida para imagen: {extension}"
                            )
                            continue

                        # Guardar la imagen en la carpeta de uploads
                        if current_app.static_folder is None:
                            logger.error(
                                "Error de configuración del servidor: static_folder es None"
                            )
                            continue
                        ruta_uploads = os.path.join(
                            current_app.static_folder, "uploads"
                        )
                        if not os.path.exists(ruta_uploads):
                            os.makedirs(ruta_uploads)
                            logger.info(f"Carpeta de uploads creada: {ruta_uploads}")

                        ruta_completa = os.path.join(ruta_uploads, nombre_unico)
                        archivo.save(ruta_completa)
                        logger.info(f"Imagen guardada localmente: {ruta_completa}")

                        # Subir a S3 si está habilitado
                        use_s3 = os.environ.get("USE_S3", "false").lower() == "true"
                        logger.info(f"USE_S3: {use_s3}")
                        if use_s3:
                            try:
                                from app.utils.s3_utils import upload_file_to_s3

                                logger.info(f"Subiendo imagen a S3: {nombre_unico}")
                                result = upload_file_to_s3(ruta_completa, nombre_unico)
                                if result["success"]:
                                    logger.info(f"Imagen subida a S3: {result['url']}")
                                    # Eliminar el archivo local después de subirlo a S3
                                    os.remove(ruta_completa)
                                    logger.info(
                                        f"Imagen eliminada del servidor local después de subirla a S3: {nombre_unico}"
                                    )
                                else:
                                    logger.error(
                                        f"Error al subir imagen a S3: {result.get('error')}"
                                    )
                            except Exception as e:
                                logger.error(
                                    f"Error al procesar subida a S3: {str(e)}",
                                    exc_info=True,
                                )

                        imagenes.append(nombre_unico)

                logger.info(f"Total de imágenes procesadas: {len(imagenes)}")

            # Agregar las imágenes a la fila
            if imagenes:
                nueva_fila["imagenes"] = imagenes
                # También guardar en imagen_data para compatibilidad
                nueva_fila["imagen_data"] = imagenes
                logger.info(f"Imágenes agregadas a la nueva fila: {imagenes}")
                # Agregar contador de imágenes para compatibilidad con vistas antiguas
                nueva_fila["num_imagenes"] = len(imagenes)

            # Agregar la fila a la tabla (actualizar tanto data como rows para compatibilidad)
            result = g.spreadsheets_collection.update_one(
                {"_id": ObjectId(tabla_id)},
                {
                    "$push": {"data": nueva_fila, "rows": nueva_fila},
                    "$inc": {"num_rows": 1},
                    "$set": {"updated_at": datetime.utcnow()},
                },
            )

            current_app.logger.info(
                f"[AGREGAR_FILA] Resultado de la actualización: matched_count={result.matched_count}, modified_count={result.modified_count}"
            )

            if result.modified_count > 0:
                flash("Fila agregada correctamente", "success")
                current_app.logger.info(
                    f"[AGREGAR_FILA] Fila agregada exitosamente, redirigiendo a ver_tabla"
                )
            else:
                flash("Error al agregar la fila", "error")
                current_app.logger.error(f"[AGREGAR_FILA] No se pudo agregar la fila")

            return redirect(url_for("main.ver_tabla", table_id=tabla_id))

        # Para peticiones GET, mostrar el formulario
        return render_template("agregar_fila_tabla.html", tabla=tabla)
    except Exception as e:
        logger.error(f"Error al agregar fila: {str(e)}", exc_info=True)
        flash(f"Error al agregar fila: {str(e)}", "error")
        return redirect(url_for("main.dashboard_user"))


@main_bp.route("/tables", methods=["GET", "POST"])
def tables():
    """Redirige las solicitudes de la antigua ruta /tables a la nueva ruta /catalogs.
    Esta función mantiene la compatibilidad con enlaces antiguos.
    """

    flash("La funcionalidad de Tablas ha sido integrada en Catálogos", "info")

    # Redirigir a la lista de catálogos
    return redirect(url_for("catalogs.list"))


@main_bp.route("/ver_tabla/<table_id>", methods=["GET"])
def ver_tabla_redirect(table_id):
    """Redirige las solicitudes de la antigua ruta /ver_tabla a la nueva ruta /catalogs/view.
    Esta función mantiene la compatibilidad con enlaces antiguos.
    """
    current_app.logger.info(
        f"Redirigiendo desde /ver_tabla/{table_id} a /catalogs/view/{table_id}"
    )
    flash("La vista de Tablas ha sido integrada en Catálogos", "info")

    # Redirigir a la vista de catálogo
    return redirect(url_for("catalogs.view", catalog_id=table_id))

    # COMENTADO: Conflicto con la función editar_fila principal
    # @main_bp.route("/editar_fila/<tabla_id>/<int:fila_index>", methods=["GET", "POST"])
    # def editar_fila_redirect(tabla_id, fila_index):
    #     """Redirige las solicitudes de la antigua ruta /editar_fila a la nueva ruta /catalogs/edit_row.
    #     Esta función mantiene la compatibilidad con enlaces antiguos.
    #     """
    #     current_app.logger.info(
    #         f"Redirigiendo desde /editar_fila/{tabla_id}/{fila_index} a /catalogs/edit_row/{tabla_id}/{fila_index}"
    #     )
    #     flash("La edición de filas ahora se realiza en Catálogos", "info")
    #
    #     # Redirigir a la edición de fila en catálogos
    #     return redirect(
    #         url_for("catalogs.edit_row", catalog_id=tabla_id, row_index=fila_index)
    #     )

    # Método POST: Crear nueva tabla
    try:
        table_name = request.form.get("table_name", "").strip()
        import_file = request.files.get("import_table")

        # Validar nombre de tabla
        if not table_name:
            flash("El nombre de la tabla es obligatorio.", "error")
            return redirect(url_for("main.tables"))

        # Comprobar duplicados para el mismo usuario
        owner = session.get("username")
        if g.spreadsheets_collection.find_one({"owner": owner, "name": table_name}):
            flash("Ya existe una tabla con ese nombre.", "error")
            return redirect(url_for("main.tables"))

        # Procesar archivo importado o crear tabla nueva
        if import_file and import_file.filename:
            try:
                ext = os.path.splitext(import_file.filename)[1].lower()
                unique_id = uuid.uuid4().hex
                filename = f"table_{unique_id}{ext}"

                # Asegurarse de que existe la carpeta de uploads
                if "UPLOAD_FOLDER" not in current_app.config:
                    flash(
                        "Error en la configuración del servidor. Contacte al administrador.",
                        "danger",
                    )
                    return redirect(url_for("main.tables"))

                filepath = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
                import_file.save(filepath)

                # Procesar archivo según su tipo
                headers = None
                rows = []

                if ext in [".xlsx", ".xlsm", ".xltx", ".xltm"]:
                    try:
                        wb = openpyxl.load_workbook(filepath)
                        hoja = wb.active
                        headers = list(
                            next(hoja.iter_rows(min_row=1, max_row=1, values_only=True))
                        )
                        for row in hoja.iter_rows(min_row=2, values_only=True):
                            if any(row):
                                rows.append(
                                    {
                                        h: (row[i] if i < len(row) else "")
                                        for i, h in enumerate(headers)
                                    }
                                )
                        wb.close()
                    except Exception as e:
                        flash(f"Error al leer el archivo Excel: {str(e)}", "error")
                        return redirect(url_for("main.tables"))
                elif ext == ".csv":
                    try:
                        with open(filepath, newline="", encoding="utf-8") as csvfile:
                            reader = csv.reader(csvfile)
                            headers = list(next(reader, None))
                            for row in reader:
                                if any(row):
                                    rows.append(
                                        {
                                            h: (row[i] if i < len(row) else "")
                                            for i, h in enumerate(headers)
                                        }
                                    )
                    except Exception as e:
                        flash(f"Error al leer el archivo CSV: {str(e)}", "error")
                        return redirect(url_for("main.tables"))
                else:
                    flash(
                        "Formato de archivo no soportado. Solo se permiten archivos .xlsx, .xlsm, .xltx, .xltm o .csv",
                        "error",
                    )
                    return redirect(url_for("main.tables"))

                if not headers or not any(headers):
                    flash(
                        "El archivo importado no contiene encabezados válidos.", "error"
                    )
                    return redirect(url_for("main.tables"))

                # Insertar la tabla en la base de datos
                result = g.spreadsheets_collection.insert_one(
                    {
                        "owner": session.get("username"),
                        "name": table_name,
                        "filename": filename,
                        "headers": headers,
                        "created_at": datetime.utcnow(),
                        "created_by": session["username"],
                        "data": rows,
                        "num_rows": len(rows),
                    }
                )

                session["selected_headers"] = headers
                return redirect(
                    url_for("main.ver_tabla", table_id=str(result.inserted_id))
                )

            except Exception as e:
                logger.error(f"Error al procesar archivo: {str(e)}", exc_info=True)
                flash(f"Error al procesar el archivo: {str(e)}", "error")
                return redirect(url_for("main.tables"))
        else:
            # Crear tabla nueva desde encabezados ingresados manualmente
            headers_str = request.form.get("table_headers", "").strip()
            headers = (
                [h.strip() for h in headers_str.split(",") if h.strip()]
                if headers_str
                else ["Número", "Descripción", "Peso", "Valor"]
            )

            if not headers or not any(headers):
                flash("Debes ingresar al menos un encabezado.", "error")
                return redirect(url_for("main.tables"))

            try:
                file_id = secrets.token_hex(8)
                filename = f"table_{file_id}.xlsx"

                # Asegurarse de que existe la carpeta de uploads
                if "UPLOAD_FOLDER" not in current_app.config:
                    flash(
                        "Error en la configuración del servidor. Contacte al administrador.",
                        "danger",
                    )
                    return redirect(url_for("main.tables"))

                filepath = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)

                wb = Workbook()
                hoja = wb.active
                hoja.append(headers)
                wb.save(filepath)
                wb.close()

                result = g.spreadsheets_collection.insert_one(
                    {
                        "owner": session.get("username"),
                        "name": table_name,
                        "filename": filename,
                        "headers": headers,
                        "created_at": datetime.utcnow(),
                        "created_by": session["username"],
                        "data": [],
                        "num_rows": 0,
                    }
                )

                session["selected_headers"] = headers
                return redirect(
                    url_for("main.ver_tabla", table_id=str(result.inserted_id))
                )
            except Exception as e:
                logger.error(f"Error al crear tabla manual: {str(e)}", exc_info=True)
                flash(f"Error al crear la tabla: {str(e)}", "error")
                return redirect(url_for("main.tables"))
    except Exception as e:
        logger.error(f"Error general en tables: {str(e)}", exc_info=True)
        flash(
            "Error al procesar la solicitud. Por favor, inténtelo de nuevo.", "danger"
        )
        return redirect(url_for("main.tables"))


@main_bp.route("/editar_tabla/<id>", methods=["GET", "POST"])
def editar_tabla(id):
    # Verificar sesión
    if "username" not in session:
        flash("Debe iniciar sesión para realizar esta acción", "warning")
        return redirect(url_for("auth.login"))

    try:
        # Obtener la tabla
        table = g.spreadsheets_collection.find_one({"_id": ObjectId(id)})

        if not table:
            flash("Tabla no encontrada.", "error")
            return redirect(url_for("main.dashboard_user"))

        # Verificar permisos: solo el propietario puede editar la tabla
        if session.get("role") != "admin" and table.get("owner") != session.get(
            "username"
        ):
            flash("No tiene permisos para editar esta tabla.", "error")
            return redirect(url_for("main.dashboard_user"))

        if request.method == "POST":
            current_app.logger.info("🔥🔥🔥 [EDITAR_TABLA] POST recibido")
            current_app.logger.info(f"[EDITAR_TABLA] Form data: {dict(request.form)}")

            # Obtener los datos del formulario
            new_name = request.form.get("name", "").strip()
            headers_str = request.form.get("headers", "").strip()
            nueva_miniatura = request.form.get("miniatura", "").strip()

            current_app.logger.info(
                f"[EDITAR_TABLA] Datos procesados: name='{new_name}', headers='{headers_str}', miniatura='{nueva_miniatura}'"
            )

            # Validar los datos
            if not new_name:
                flash("El nombre de la tabla no puede estar vacío.", "error")
                return render_template("editar_tabla.html", table=table)

            # Procesar los encabezados
            new_headers = [h.strip() for h in headers_str.split(",") if h.strip()]

            if not new_headers:
                flash("Debe proporcionar al menos un encabezado.", "error")
                return render_template("editar_tabla.html", table=table)

            # Verificar si los encabezados han cambiado
            old_headers = table.get("headers", [])

            # Actualizar la tabla en la base de datos
            update_data = {"name": new_name, "headers": new_headers}

            # Procesar la miniatura personalizada
            if nueva_miniatura:
                update_data["miniatura"] = nueva_miniatura
                current_app.logger.info(
                    f"[MINIATURA_CUSTOM] Configurada miniatura personalizada: {nueva_miniatura}"
                )
            else:
                # Si se envía vacío, eliminar el campo de miniatura personalizada
                # (se usará la automática en dashboard_user)
                update_data["miniatura"] = ""
                current_app.logger.info(
                    "[MINIATURA_CUSTOM] Miniatura personalizada eliminada, se usará automática"
                )

            # 🔥 PRIMERO: Siempre actualizar nombre, headers y miniatura
            basic_update = {
                "name": new_name,
                "headers": new_headers,
                "miniatura": nueva_miniatura if nueva_miniatura else "",
            }
            g.spreadsheets_collection.update_one(
                {"_id": ObjectId(id)}, {"$set": basic_update}
            )
            current_app.logger.info(
                f"[UPDATE_BASIC] Actualizados: name={new_name}, headers={new_headers}, miniatura={nueva_miniatura}"
            )

            # Si los encabezados cambiaron, actualizar los datos
            if set(old_headers) != set(new_headers):
                # Crear un mapeo de viejos a nuevos encabezados para los que coinciden
                header_map = {}
                for old_h in old_headers:
                    if old_h in new_headers:
                        header_map[old_h] = old_h

                # Actualizar los datos con los nuevos encabezados
                data = table.get("data", [])
                new_data = []

                for row in data:
                    new_row = {}
                    # Mantener los campos que coinciden
                    for old_h, new_h in header_map.items():
                        if old_h in row:
                            new_row[new_h] = row[old_h]

                    # Añadir campos para los nuevos encabezados
                    for h in new_headers:
                        if h not in new_row:
                            new_row[h] = ""

                    # Mantener campos especiales como 'imagenes'
                    if "imagenes" in row:
                        new_row["imagenes"] = row["imagenes"]

                    new_data.append(new_row)

                update_data["data"] = new_data

                # Manejar actualización de imágenes
                nuevas_imagenes = request.files.getlist("imagenes")
                if nuevas_imagenes:
                    logger.info(f"Nuevas imágenes a guardar: {nuevas_imagenes}")

                    # Verificar si el campo imagenes es un número entero (contador)
                    if "imagenes" in row and isinstance(row["imagenes"], int):
                        # Si es un contador, actualizar el campo imagen_data
                        if "imagen_data" in row and isinstance(
                            row["imagen_data"], list
                        ):
                            # Añadir las nuevas imágenes a imagen_data
                            update_data["imagen_data"] = row["imagen_data"] + [
                                img.filename for img in nuevas_imagenes
                            ]
                            # Actualizar el contador
                            update_data["imagenes"] = len(row["imagen_data"]) + len(
                                nuevas_imagenes
                            )
                            logger.info(
                                f"Actualizando contador de imágenes a {update_data['imagenes']}"
                            )
                        else:
                            # Crear el campo imagen_data
                            update_data["imagen_data"] = [
                                img.filename for img in nuevas_imagenes
                            ]
                            # Actualizar el contador
                            update_data["imagenes"] = len(nuevas_imagenes)
                            logger.info(
                                f"Creando campo imagen_data con {len(nuevas_imagenes)} imágenes"
                            )
                    else:
                        # Si ya hay imágenes, añadir las nuevas
                        if "imagenes" in row and isinstance(row["imagenes"], list):
                            update_data["imagenes"] = row["imagenes"] + [
                                img.filename for img in nuevas_imagenes
                            ]
                            logger.info(
                                f"Añadiendo nuevas imágenes a la lista existente: {update_data['imagenes']}"
                            )
                        else:
                            # Si no hay imágenes previas, crear la lista
                            update_data["imagenes"] = [
                                img.filename for img in nuevas_imagenes
                            ]
                            logger.info(
                                f"Creando nueva lista de imágenes: {nuevas_imagenes}"
                            )

                        # Actualizar también imagen_data si existe
                        if "imagen_data" in row:
                            if isinstance(row["imagen_data"], list):
                                update_data["imagen_data"] = row["imagen_data"] + [
                                    img.filename for img in nuevas_imagenes
                                ]
                            else:
                                update_data["imagen_data"] = [
                                    img.filename for img in nuevas_imagenes
                                ]
                            logger.info(
                                "Actualizando campo imagen_data con las mismas imágenes"
                            )

                # Actualizar la tabla
                g.spreadsheets_collection.update_one(
                    {"_id": ObjectId(id)}, {"$set": update_data}
                )

                # Los headers cambiaron, se actualizó todo
                pass

            # 🎯 SIEMPRE redirigir después de actualizar (con o sin cambio de headers)
            flash("Tabla actualizada correctamente.", "success")
            current_app.logger.info(f"[EDITAR_TABLA] ✅ Redirigiendo a dashboard_user")
            return redirect(url_for("main.dashboard_user"))

        # GET: Mostrar formulario de edición
        return render_template("editar_tabla.html", table=table)

    except Exception as e:
        logger.error(f"Error en editar_tabla: {str(e)}", exc_info=True)
        flash(f"Error al editar la tabla: {str(e)}", "error")
        return redirect(url_for("main.dashboard_user"))


@main_bp.route("/delete_row/<tabla_id>/<int:fila_index>", methods=["POST"])
def delete_row(tabla_id, fila_index):
    """Eliminar una fila específica de una tabla"""
    current_app.logger.info(
        f"[DELETE_ROW] Eliminando fila {fila_index} de tabla {tabla_id}"
    )

    # Verificar sesión
    if "username" not in session:
        flash("Debe iniciar sesión para realizar esta acción", "warning")
        return redirect(url_for("auth.login"))

    # Obtener info de la tabla
    table_info = g.spreadsheets_collection.find_one({"_id": ObjectId(tabla_id)})
    if not table_info:
        flash("Tabla no encontrada.", "error")
        return redirect(url_for("main.tables"))

    # Verificar permisos: solo el propietario o admin puede eliminar filas
    username = session.get("username")
    role = session.get("role", "user")
    owner = (
        table_info.get("owner")
        or table_info.get("created_by")
        or table_info.get("owner_name")
    )

    if role != "admin" and owner != username:
        flash("No tienes permisos para eliminar filas de esta tabla.", "warning")
        return redirect(url_for("main.ver_tabla", table_id=tabla_id))

    # Sincronizar 'rows' y 'data'
    if "rows" in table_info and table_info["rows"] is not None:
        table_info["data"] = table_info["rows"]
    elif "data" in table_info and table_info["data"] is not None:
        table_info["rows"] = table_info["data"]
    else:
        table_info["data"] = []
        table_info["rows"] = []

    current_rows = table_info.get("data", [])
    current_app.logger.info(f"[DELETE_ROW] Filas actuales: {len(current_rows)}")

    # Verificar que el índice sea válido
    if fila_index < 0 or fila_index >= len(current_rows):
        flash(f"Índice de fila inválido: {fila_index}.", "danger")
        current_app.logger.error(
            f"[DELETE_ROW] Índice inválido: {fila_index} >= {len(current_rows)}"
        )
        return redirect(url_for("main.ver_tabla", table_id=tabla_id))

    try:
        # Eliminar la fila
        deleted_row = current_rows.pop(fila_index)
        current_app.logger.info(f"[DELETE_ROW] Fila eliminada: {deleted_row}")

        # Actualizar en base de datos
        result = g.spreadsheets_collection.update_one(
            {"_id": ObjectId(tabla_id)},
            {
                "$set": {
                    "data": current_rows,
                    "rows": current_rows,
                    "num_rows": len(current_rows),
                    "updated_at": datetime.utcnow(),
                }
            },
        )

        if result.matched_count > 0 and result.modified_count > 0:
            flash("Fila eliminada correctamente", "success")
            current_app.logger.info(
                f"[DELETE_ROW] Fila eliminada exitosamente. Filas restantes: {len(current_rows)}"
            )
        else:
            flash("No se pudo eliminar la fila.", "warning")

    except Exception as e:
        current_app.logger.error(f"[DELETE_ROW] Error: {str(e)}")
        flash(f"Error al eliminar fila: {str(e)}", "danger")

    return redirect(url_for("main.ver_tabla", table_id=tabla_id))


@main_bp.route("/delete_table/<table_id>", methods=["POST"])
def delete_table(table_id):
    # Verificar sesión
    if "username" not in session:
        flash("Debe iniciar sesión para realizar esta acción", "warning")
        return redirect(url_for("auth.login"))

    # Verificar permisos: solo el propietario o admin puede eliminar la tabla
    username = session.get("username")
    role = session.get("role", "user")

    # Primero, obtener la tabla
    table = g.spreadsheets_collection.find_one({"_id": ObjectId(table_id)})

    if not table:
        flash("Tabla no encontrada.", "warning")
        return redirect(url_for("main.tables"))

    # Obtener el propietario de la tabla (puede estar en diferentes campos)
    owner = table.get("owner") or table.get("created_by") or table.get("owner_name")

    current_app.logger.info(
        f"[DEBUG] Verificando permisos para eliminar tabla: role={role}, username={username}, owner={owner}"
    )

    # Verificar permisos
    if role != "admin" and owner != username:
        current_app.logger.warning(
            f"[DEBUG] Permiso denegado para eliminar tabla: {username} intentando eliminar tabla de {owner}"
        )
        flash("No tiene permisos para eliminar esta tabla.", "warning")
        return redirect(url_for("main.tables"))

    if not table:
        flash("Tabla no encontrada o no tiene permisos para eliminarla.", "error")
        return redirect(url_for("main.tables"))

    # Eliminar archivo físico solo si existe el campo 'filename'
    filename = table.get("filename")
    if filename:
        filepath = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
        if os.path.exists(filepath):
            os.remove(filepath)

    g.spreadsheets_collection.delete_one({"_id": ObjectId(table_id)})

    if filename and session.get("selected_table") == filename:
        session.pop("selected_table", None)

    flash("Tabla eliminada exitosamente.", "success")
    return redirect(url_for("main.tables"))


@main_bp.route("/guia-rapida")
def guia_rapida():
    """Guía rápida de uso para usuarios normales"""
    return render_template("guia_rapida.html")


@main_bp.route("/soporte", methods=["GET", "POST"])
def soporte():
    if request.method == "POST":
        nombre = request.form.get("nombre", "")
        email = request.form.get("email", "")
        mensaje = request.form.get("mensaje", "")
        # Enviar email real a soporte
        subject = f"[Soporte] Mensaje de {nombre} ({email})"
        body_html = f"""
        <h3>Nuevo mensaje de soporte recibido</h3>
        <ul>
            <li><strong>Nombre:</strong> {nombre}</li>
            <li><strong>Email:</strong> {email}</li>
        </ul>
        <p><strong>Mensaje:</strong></p>
        <div style='white-space: pre-line; border:1px solid #eee; padding:10px; background:#f9f9f9;'>{mensaje}</div>
        <hr>
        <small>Este mensaje fue enviado desde el formulario de soporte de la aplicación.</small>
        """
        # Destinatario: el correo de soporte configurado
        recipients = ["admin@edefrutos2025.xyz"]
        ok = notifications.send_email(subject, body_html, recipients)
        if ok:
            flash(
                "Tu mensaje ha sido enviado. El equipo de soporte te contactará pronto.",
                "success",
            )
        else:
            flash(
                "No se pudo enviar el mensaje. Intenta más tarde o contacta por email.",
                "danger",
            )
        return redirect(url_for("main.guia_rapida"))
    return render_template("soporte.html")
