# Script: admin_catalog_routes.py
# Descripción: Rutas administrative visualización, edición y eliminación de catálogos.
# Autor: EDF Developer

import logging
import os
from datetime import datetime
from typing import Any, Dict

from bson import ObjectId
from flask import current_app, flash, jsonify, redirect, render_template, request, url_for

from app.database import get_mongo_db
from app.decorators import admin_required
from app.routes.s3_utils import get_s3_url
from app.utils.catalog_utils import get_catalog_rows, normalize_catalog_rows


logger = logging.getLogger(__name__)


def register_admin_catalog_routes(admin_bp) -> None:
    """Registra rutas administrativas de catálogos sobre el blueprint admin."""

    @admin_bp.route("/catalogo/<collection_source>/<catalog_id>")
    @admin_required
    def ver_catalogo_unificado(collection_source: str, catalog_id: str):
        logger.info(
            f"[ADMIN] Entrando en ver_catalogo_unificado con collection_source={collection_source}, catalog_id={catalog_id}"
        )
        try:
            db = get_mongo_db()
            if db is None:
                flash("Error: No se pudo acceder a la base de datos", "error")
                return redirect(url_for("admin.dashboard_admin"))
            collection = db[collection_source]

            try:
                catalog = collection.find_one({"_id": ObjectId(catalog_id)})
            except Exception as e:
                logger.error(
                    f"[ADMIN] Error al convertir catalog_id a ObjectId: {catalog_id}, error: {e}"
                )
                flash("ID de catálogo inválido", "error")
                return redirect(url_for("admin.dashboard_admin"))

            if not catalog:
                logger.warning(
                    f"[ADMIN] Catálogo no encontrado en {collection_source} para id={catalog_id}"
                )
                flash("Catálogo no encontrado", "warning")
                return render_template(
                    "admin/ver_catalogo.html", catalog=None, error="Catálogo no encontrado"
                )

            # --- Start of Refactoring ---

            def get_final_url(file_identifier):
                if not isinstance(file_identifier, str) or not file_identifier.strip():
                    return None, None

                filename = file_identifier.split("/")[-1]

                if file_identifier.startswith("http"):
                    if "s3.amazonaws.com" in file_identifier:
                        return f"/admin/s3/{filename}", filename
                    return file_identifier, filename

                if file_identifier.startswith("/"):
                    return file_identifier, filename

                s3_url = get_s3_url(file_identifier)
                if s3_url:
                    return f"/admin/s3/{filename}", filename

                return f"/static/uploads/{file_identifier}", filename

            if "data" in catalog and catalog["data"]:
                for i, row in enumerate(catalog["data"]):
                    if not isinstance(row, dict):
                        logger.warning(
                            f"[ADMIN] Fila {i} ignorada por no ser un dict: {row}"
                        )
                        continue

                    # 1. Consolidate and process documents
                    processed_documents = []
                    seen_documents = set()
                    doc_fields = [k for k in row if k.lower().startswith("document")]

                    for field in doc_fields:
                        doc_values = row.get(field)
                        if not doc_values:
                            continue

                        doc_list = (
                            [doc_values] if isinstance(doc_values, str) else doc_values
                        )

                        if isinstance(doc_list, list):
                            for doc_item in doc_list:
                                if (
                                    doc_item
                                    and isinstance(doc_item, str)
                                    and doc_item.strip() not in seen_documents
                                ):
                                    doc_item_clean = doc_item.strip()
                                    seen_documents.add(doc_item_clean)
                                    url, filename = get_final_url(doc_item_clean)
                                    if url and filename:
                                        ext = (
                                            filename.split(".")[-1].lower()
                                            if "." in filename
                                            else "link"
                                        )
                                        processed_documents.append(
                                            {
                                                "url": url,
                                                "name": ext.upper(),
                                                "filename": filename,
                                            }
                                        )

                    row["processed_documents"] = processed_documents

                    # 2. Consolidate and process images
                    processed_images = []
                    seen_images = set()
                    image_fields = [
                        k for k in row if k.lower() in ["images", "imagenes", "imagen"]
                    ]

                    for field in image_fields:
                        img_values = row.get(field)
                        if not img_values:
                            continue

                        img_list = (
                            [img_values] if isinstance(img_values, str) else img_values
                        )

                        if isinstance(img_list, list):
                            for img_item in img_list:
                                if (
                                    img_item
                                    and isinstance(img_item, str)
                                    and img_item.strip() not in seen_images
                                ):
                                    img_item_clean = img_item.strip()
                                    seen_images.add(img_item_clean)
                                    url, _ = get_final_url(img_item_clean)
                                    if url:
                                        processed_images.append(url)

                    row["imagen_urls"] = processed_images

                    # 3. Process Multimedia
                    if "Multimedia" in row and row["Multimedia"]:
                        media_item = row["Multimedia"]
                        url, filename = get_final_url(media_item)
                        row["multimedia_url"] = url
                        row["multimedia_filename"] = filename if filename else ""

            # --- End of Refactoring ---

            catalog["collection_source"] = collection_source
            catalog["_id_str"] = str(catalog["_id"])

            if "created_at" in catalog and catalog["created_at"]:
                if isinstance(catalog["created_at"], str):
                    catalog["created_at_formatted"] = catalog["created_at"]
                else:
                    catalog["created_at_formatted"] = catalog["created_at"].strftime(
                        "%d/%m/%Y %H:%M"
                    )
            else:
                catalog["created_at_formatted"] = "Fecha desconocida"

            normalize_catalog_rows(catalog)

            logger.info(
                f"[ADMIN] Mostrando catálogo desde {collection_source}: {catalog.get('name', 'Sin nombre')}"
            )
            return_url = request.args.get("return_url") or request.referrer

            if return_url and "editar-fila" in return_url:
                user_id = None
                if "created_by_id" in catalog and catalog["created_by_id"]:
                    user_id = str(catalog["created_by_id"])
                elif "created_by" in catalog and catalog["created_by"]:
                    user = db.users.find_one(
                        {
                            "$or": [
                                {"email": catalog["created_by"]},
                                {"username": catalog["created_by"]},
                            ]
                        }
                    )
                    if user:
                        user_id = str(user["_id"])

                if user_id:
                    return_url = url_for(
                        "admin.ver_catalogos_usuario_por_id", user_id=user_id
                    )
                else:
                    return_url = url_for("admin.dashboard_admin")
            elif not return_url:
                user_id = None
                if "created_by_id" in catalog and catalog["created_by_id"]:
                    user_id = str(catalog["created_by_id"])
                elif "created_by" in catalog and catalog["created_by"]:
                    user = db.users.find_one(
                        {
                            "$or": [
                                {"email": catalog["created_by"]},
                                {"username": catalog["created_by"]},
                            ]
                        }
                    )
                    if user:
                        user_id = str(user["_id"])

                if user_id:
                    return_url = url_for(
                        "admin.ver_catalogos_usuario_por_id", user_id=user_id
                    )
                else:
                    return_url = url_for("admin.dashboard_admin")

            return render_template(
                "admin/ver_catalogo.html",
                catalog=catalog,
                error=None,
                collection_source=collection_source,
                return_url=return_url,
            )
        except (AttributeError, KeyError, TypeError, ValueError) as e:
            logger.error(f"Error en ver_catalogo_unificado: {str(e)}", exc_info=True)
            flash(f"Error al cargar el catálogo: {str(e)}", "error")
            return redirect(url_for("admin.dashboard_admin"))


    @admin_bp.route(
        "/catalogo/<collection_source>/<catalog_id>/editar", methods=["GET", "POST"]
    )
    @admin_required
    def editar_catalogo_admin(collection_source: str, catalog_id: str):
        logger.info(
            f"[ADMIN] Entrando en editar_catalogo_admin con collection_source={collection_source}, catalog_id={catalog_id}"
        )
        try:
            db = get_mongo_db()
            if db is None:
                flash("Error: No se pudo acceder a la base de datos", "error")
                return redirect(url_for("admin.dashboard_admin"))
            collection = db[collection_source]
            catalog = collection.find_one({"_id": ObjectId(catalog_id)})
            if not catalog:
                logger.warning(
                    f"[ADMIN] Catálogo no encontrado en {collection_source} para id={catalog_id}"
                )
                flash("Catálogo no encontrado", "warning")
                return redirect(url_for("admin.dashboard_admin"))

            # Añadir información sobre la colección de origen
            catalog["collection_source"] = collection_source
            catalog["_id_str"] = str(catalog["_id"])

            if request.method == "POST":
                name = request.form.get("name")
                description = request.form.get("description", "")
                headers_raw = request.form.get("headers")
                nueva_miniatura = request.form.get("miniatura", "").strip()

                # Manejar subida de archivo de miniatura
                miniatura_file = request.files.get("miniatura_file")
                if miniatura_file and miniatura_file.filename:
                    try:
                        # Verificar que sea una imagen válida
                        if not miniatura_file.filename.lower().endswith(
                            (".png", ".jpg", ".jpeg", ".gif", ".webp")
                        ):
                            flash(
                                "El archivo debe ser una imagen (PNG, JPG, JPEG, GIF, WEBP).",
                                "error",
                            )
                            return render_template(
                                "admin/editar_catalogo.html", catalog=catalog
                            )

                        # Importar utilidades de imagen y S3
                        import uuid

                        from app.utils.image_utils import upload_image_to_s3

                        # Generar nombre único para el archivo
                        file_extension = miniatura_file.filename.split(".")[-1].lower()
                        unique_filename = f"miniatura_{uuid.uuid4().hex}.{file_extension}"

                        # Subir a S3
                        s3_url = upload_image_to_s3(miniatura_file, unique_filename)

                        if s3_url:
                            nueva_miniatura = s3_url
                            current_app.logger.info(f"Miniatura subida a S3: {s3_url}")
                        else:
                            # Fallback: guardar localmente si S3 falla
                            import os

                            from app.routes.catalogs_routes import get_upload_dir

                            upload_dir = get_upload_dir()
                            file_path = os.path.join(upload_dir, unique_filename)
                            miniatura_file.save(file_path)
                            nueva_miniatura = url_for(
                                "static", filename=f"uploads/{unique_filename}"
                            )
                            current_app.logger.info(
                                f"Miniatura guardada localmente: {nueva_miniatura}"
                            )

                    except Exception as e:
                        current_app.logger.error(
                            f"Error al procesar archivo de miniatura: {str(e)}"
                        )
                        flash(f"Error al subir la imagen: {str(e)}", "error")
                        return render_template(
                            "admin/editar_catalogo.html", catalog=catalog
                        )

                update_data: Dict[str, Any] = {
                    "name": name,
                    "description": description,
                    "updated_at": datetime.utcnow(),
                }
                if headers_raw is not None:
                    headers = [h.strip() for h in headers_raw.split(",") if h.strip()]
                    update_data["headers"] = headers

                # Añadir miniatura si se proporcionó
                if nueva_miniatura:
                    update_data["miniatura"] = nueva_miniatura
                # Actualizar el catálogo en la colección correspondiente
                collection.update_one({"_id": ObjectId(catalog_id)}, {"$set": update_data})
                flash("Catálogo actualizado correctamente", "success")
                # Intentar obtener el ID del usuario para redirigir
                user_id = None
                if "created_by_id" in catalog and catalog["created_by_id"]:
                    user_id = str(catalog["created_by_id"])
                elif "created_by" in catalog and catalog["created_by"]:
                    # Buscar el usuario por email o username
                    user = db.users.find_one(
                        {
                            "$or": [
                                {"email": catalog["created_by"]},
                                {"username": catalog["created_by"]},
                            ]
                        }
                    )
                    if user:
                        user_id = str(user["_id"])
                if user_id:
                    return redirect(
                        url_for("admin.ver_catalogos_usuario_por_id", user_id=user_id)
                    )
                else:
                    return redirect(url_for("admin.dashboard_admin"))

            return render_template(
                "admin/editar_catalogo.html",
                catalog=catalog,
                collection_source=collection_source,
            )
        except (AttributeError, KeyError, TypeError, ValueError) as e:
            logger.error(f"Error en editar_catalogo_admin: {str(e)}", exc_info=True)
            flash(f"Error al editar el catálogo: {str(e)}", "error")
            return redirect(url_for("admin.dashboard_admin"))


    @admin_bp.route(
        "/catalogo/<collection_source>/<catalog_id>/editar-fila/<int:row_index>",
        methods=["GET", "POST"],
    )
    @admin_required
    def editar_fila_admin(collection_source: str, catalog_id: str, row_index: int):
        """
        Editar una fila específica de un catálogo desde la interfaz de administración
        """
        logger.info(
            f"[ADMIN] Entrando en editar_fila_admin con collection_source={collection_source}, catalog_id={catalog_id}, row_index={row_index}"
        )
        try:
            db = get_mongo_db()
            if db is None:
                flash("Error: No se pudo acceder a la base de datos", "error")
                return redirect(url_for("admin.dashboard_admin"))

            collection = db[collection_source]
            catalog = collection.find_one({"_id": ObjectId(catalog_id)})
            if not catalog:
                logger.warning(
                    f"[ADMIN] Catálogo no encontrado en {collection_source} para id={catalog_id}"
                )
                flash("Catálogo no encontrado", "warning")
                return redirect(url_for("admin.dashboard_admin"))

            # Asegurar que rows existe
            if "rows" not in catalog or not catalog["rows"]:
                catalog["rows"] = []

            # Verificar que el índice de fila es válido
            if row_index < 0 or row_index >= len(catalog["rows"]):
                flash("Índice de fila inválido", "error")
                return redirect(
                    url_for(
                        "admin.ver_catalogo_unificado",
                        collection_source=collection_source,
                        catalog_id=catalog_id,
                    )
                )

            row_data = get_catalog_rows(catalog)[row_index]
            logger.info(f"[ADMIN_EDIT_ROW] 🔍 row_data obtenido: {row_data}")
            logger.info(f"[ADMIN_EDIT_ROW] 📋 row_data tipo: {type(row_data)}")
            logger.info(
                f"[ADMIN_EDIT_ROW] 📋 row_data keys: {list(row_data.keys()) if isinstance(row_data, dict) else 'No es dict'}"
            )

            # Procesar campos de Documentación - crear campos individuales para el
            # template (igual que en ver_catalogo_unificado)
            if "Documentación" in row_data and isinstance(row_data["Documentación"], list):
                for i, doc in enumerate(row_data["Documentación"]):
                    if doc and doc.strip():  # Solo si el documento no está vacío
                        row_data[f"Documentación_{i}"] = doc.strip()
                        logger.debug(
                            f"[ADMIN_EDIT_ROW] Creado campo Documentación_{i} = {doc.strip()}"
                        )

            # Procesar imágenes - unificar campos 'images' e 'imagenes' (igual que en
            # ver_catalogo_unificado)
            from app.utils.s3_utils import get_s3_url

            # Procesar imágenes - unificar campos 'images' e 'imagenes'
            imagenes_a_procesar = []

            # Recopilar imágenes de ambos campos
            if "images" in row_data and row_data["images"]:
                if isinstance(row_data["images"], list):
                    imagenes_a_procesar.extend(row_data["images"])
                else:
                    imagenes_a_procesar.append(row_data["images"])

            if "imagenes" in row_data and row_data["imagenes"]:
                if isinstance(row_data["imagenes"], list):
                    imagenes_a_procesar.extend(row_data["imagenes"])
                else:
                    imagenes_a_procesar.append(row_data["imagenes"])

            # Unificar en el campo 'images' para consistencia
            if imagenes_a_procesar:
                row_data["images"] = imagenes_a_procesar
                # Eliminar el campo 'imagenes' para evitar duplicación
                if "imagenes" in row_data:
                    del row_data["imagenes"]

            # Procesar todas las imágenes recopiladas
            if imagenes_a_procesar:
                # Crear un array con las URLs de las imágenes
                row_data["imagen_urls"] = []
                for img in imagenes_a_procesar:
                    if (
                        img and len(img) > 5
                    ):  # Verificar que el nombre de la imagen es válido
                        # Verificar si ya es una URL completa
                        if (
                            img.startswith("/admin/s3/")
                            or img.startswith("/static/uploads/")
                            or img.startswith("/imagenes_subidas/")
                        ):
                            # Ya es una URL completa, usar directamente
                            row_data["imagen_urls"].append(img)
                            logger.debug(f"[ADMIN_EDIT_ROW] URL completa detectada: {img}")
                        else:
                            # Intentar obtener la URL de S3 primero
                            s3_url = get_s3_url(img)
                            if s3_url:
                                row_data["imagen_urls"].append(s3_url)
                                logger.debug(
                                    f"[ADMIN_EDIT_ROW] Imagen S3 encontrada: {img} -> {s3_url}"
                                )
                            else:
                                # Si no está en S3, usar la URL local
                                local_url = url_for("static", filename=f"uploads/{img}")
                                row_data["imagen_urls"].append(local_url)
                                logger.debug(
                                    f"[ADMIN_EDIT_ROW] Usando URL local para imagen: {img} -> {local_url}"
                                )

                # Asignar las URLs procesadas a _imagenes para la plantilla
                if "imagen_urls" in row_data:
                    row_data["_imagenes"] = row_data["imagen_urls"]
                    logger.info(
                        f"[ADMIN_EDIT_ROW] Procesadas {len(row_data['imagen_urls'])} imágenes para la fila"
                    )

            # Añadir información sobre la colección de origen
            catalog["collection_source"] = collection_source
            catalog["_id_str"] = str(catalog["_id"])

            if request.method == "POST":
                # Procesar campos normales y especiales
                # Inicializar updated_row con los datos existentes para preservar campos
                # no modificados
                updated_row: Dict[str, Any] = dict(row_data)
                logger.info(
                    f"[ADMIN_EDIT_ROW] 🔄 Inicializando updated_row con datos existentes: {updated_row}"
                )

                for header in catalog["headers"]:
                    if header == "Multimedia":
                        # Manejar campo Multimedia
                        multimedia_url = request.form.get(f"{header}_url", "").strip()
                        multimedia_file = request.files.get(f"{header}_file")

                        # Solo actualizar si se proporciona un nuevo valor
                        if multimedia_url:
                            updated_row[header] = multimedia_url
                            logger.info(
                                f"[ADMIN_EDIT_ROW] Multimedia URL actualizada: {multimedia_url}"
                            )
                        elif multimedia_file and multimedia_file.filename:
                            # Procesar archivo multimedia
                            import uuid  # noqa: I001

                            from werkzeug.utils import secure_filename

                            from app.routes.catalogs_routes import get_upload_dir

                            filename = secure_filename(
                                f"{uuid.uuid4().hex}_{multimedia_file.filename}"
                            )
                            upload_dir = get_upload_dir()
                            file_path = os.path.join(upload_dir, filename)
                            multimedia_file.save(file_path)

                            # Subir a S3 si está habilitado
                            use_s3 = os.environ.get("USE_S3", "false").lower() == "true"
                            if use_s3:
                                try:
                                    from app.utils.s3_utils import upload_file_to_s3_direct

                                    logger.info(f"Subiendo multimedia a S3: {filename}")
                                    # Leer el archivo y subirlo directamente a S3
                                    with open(file_path, "rb") as file_obj:
                                        from werkzeug.datastructures import FileStorage

                                        file_storage = FileStorage(
                                            stream=file_obj,
                                            filename=filename,
                                            content_type="application/octet-stream",
                                        )
                                        result = upload_file_to_s3_direct(
                                            file_storage, filename
                                        )

                                    if result["success"]:
                                        logger.info(
                                            f"Multimedia subida a S3: {result['url']}"
                                        )
                                        # Eliminar el archivo local después de subirlo a S3
                                        os.remove(file_path)
                                        updated_row[header] = result["url"]
                                    else:
                                        logger.error(
                                            f"Error subiendo multimedia a S3: {result['error']}"
                                        )
                                        # Si falla S3, mantener local
                                        updated_row[header] = filename
                                except Exception as e:
                                    logger.error(
                                        f"Error en proceso S3 para multimedia: {e}"
                                    )
                                    # Si falla S3, mantener local
                                    updated_row[header] = filename
                            else:
                                # Almacenamiento local
                                logger.info(f"Multimedia guardada localmente: {filename}")
                                updated_row[header] = filename

                            logger.info(
                                f"[ADMIN_EDIT_ROW] Multimedia archivo actualizado: {updated_row[header]}"
                            )
                        else:
                            # Mantener valor existente si no hay cambios
                            existing_multimedia = row_data.get(header, "")
                            updated_row[header] = existing_multimedia
                            logger.info(
                                f"[ADMIN_EDIT_ROW] Multimedia existente preservado: {existing_multimedia}"
                            )

                    elif header in ["Documentos", "Documentación"]:
                        # Manejar múltiples documentos por fila
                        documentos = []

                        # Obtener documentos existentes (si los hay)
                        logger.info(
                            f"[ADMIN_EDIT_ROW] 🔍 Obteniendo documentos existentes para {header}"
                        )
                        logger.info(f"[ADMIN_EDIT_ROW] 📋 row_data completo: {row_data}")
                        documentos_existentes = row_data.get(header, [])
                        logger.info(
                            f"[ADMIN_EDIT_ROW] 📄 documentos_existentes inicial: {documentos_existentes} (tipo: {type(documentos_existentes)})"
                        )

                        # Verificar el tipo de manera segura
                        if isinstance(documentos_existentes, str):
                            # Si es un string (formato antiguo), convertirlo a array
                            documentos_existentes = (
                                [documentos_existentes] if documentos_existentes else []
                            )
                            logger.info(
                                f"[ADMIN_EDIT_ROW] 🔄 Convertido string a array: {documentos_existentes}"
                            )
                        elif not hasattr(documentos_existentes, "__iter__") or isinstance(
                            documentos_existentes, str
                        ):
                            # Si no es iterable o es string, inicializar como lista vacía
                            documentos_existentes = []
                            logger.info(
                                f"[ADMIN_EDIT_ROW] 🔄 Inicializado como lista vacía: {documentos_existentes}"
                            )

                        logger.info(
                            f"[ADMIN_EDIT_ROW] 📄 documentos_existentes final: {documentos_existentes}"
                        )

                        # Obtener todos los documentos del formulario (URLs y archivos)
                        # Buscar campos con el patrón header_url_INDEX y header_file_INDEX
                        documento_urls = []
                        documento_files = []

                        # Buscar todos los campos que coincidan con el patrón
                        for key, value in request.form.items():
                            if key.startswith(f"{header}_url_") and value.strip():
                                documento_urls.append(value.strip())

                        for key, file in request.files.items():
                            if key.startswith(f"{header}_file_") and file.filename:
                                documento_files.append(file)

                        # Procesar URLs de documentos
                        for url in documento_urls:
                            if url and url.strip():
                                documentos.append(url.strip())

                        # Procesar archivos de documentos
                        for documento_file in documento_files:
                            if documento_file and documento_file.filename:
                                # Procesar archivo documento
                                import uuid  # noqa: I001

                                from werkzeug.utils import secure_filename

                                from app.routes.catalogs_routes import get_upload_dir

                                filename = secure_filename(
                                    f"{uuid.uuid4().hex}_{documento_file.filename}"
                                )
                                upload_dir = get_upload_dir()
                                file_path = os.path.join(upload_dir, filename)
                                documento_file.save(file_path)

                                # Subir a S3 si está habilitado
                                use_s3 = os.environ.get("USE_S3", "false").lower() == "true"
                                if use_s3:
                                    try:
                                        from app.utils.s3_utils import (
                                            upload_file_to_s3_direct,
                                        )

                                        logger.info(f"Subiendo documento a S3: {filename}")
                                        # Leer el archivo y subirlo directamente a S3
                                        with open(file_path, "rb") as file_obj:
                                            from werkzeug.datastructures import FileStorage

                                            file_storage = FileStorage(
                                                stream=file_obj,
                                                filename=filename,
                                                content_type="application/octet-stream",
                                            )
                                            result = upload_file_to_s3_direct(
                                                file_storage, filename
                                            )

                                        if result["success"]:
                                            logger.info(
                                                f"Documento subido a S3: {result['url']}"
                                            )
                                            # Eliminar el archivo local después de subirlo a
                                            # S3
                                            os.remove(file_path)
                                            documentos.append(result["url"])
                                        else:
                                            logger.error(
                                                f"Error subiendo documento a S3: {result['error']}"
                                            )
                                            # Si falla S3, mantener local
                                            documentos.append(filename)
                                    except Exception as e:
                                        logger.error(
                                            f"Error en proceso S3 para documento: {e}"
                                        )
                                        # Si falla S3, mantener local
                                        documentos.append(filename)
                                else:
                                    # Almacenamiento local
                                    logger.info(
                                        f"Documento guardado localmente: {filename}"
                                    )
                                    documentos.append(filename)

                        # Combinar documentos existentes con los nuevos
                        logger.info(
                            f"[ADMIN_EDIT_ROW] {header} - Documentos existentes: {documentos_existentes}"
                        )
                        logger.info(
                            f"[ADMIN_EDIT_ROW] {header} - Documentos nuevos: {documentos}"
                        )

                        if documentos_existentes and documentos:
                            # Hay documentos existentes Y nuevos: combinar
                            documentos = documentos_existentes + documentos
                            logger.info(
                                f"[ADMIN_EDIT_ROW] {header} - Combinando existentes + nuevos: {documentos}"
                            )
                        elif documentos_existentes and not documentos:
                            # Hay documentos existentes pero NO nuevos: preservar existentes
                            documentos = documentos_existentes
                            logger.info(
                                f"[ADMIN_EDIT_ROW] {header} - Preservando existentes: {documentos}"
                            )
                        else:
                            logger.info(
                                f"[ADMIN_EDIT_ROW] {header} - Sin documentos existentes ni nuevos: {documentos}"
                            )
                        # Si no hay documentos existentes ni nuevos, mantener lista vacía

                        # Almacenar como array de documentos con nombre único basado en el índice de la columna
                        # Encontrar el índice de esta columna específica
                        header_index = None
                        for i, h in enumerate(catalog.get("headers", [])):
                            if h == header:
                                if header_index is None:
                                    header_index = i
                                else:
                                    # Si ya encontramos una columna con este nombre, usar el
                                    # índice actual
                                    header_index = i
                                    break

                        # Usar el header original para mantener consistencia
                        # El unique_header solo se usa internamente, pero almacenamos con el
                        # header original
                        updated_row[header] = documentos
                        logger.info(
                            f"[ADMIN_EDIT_ROW] {header} documentos finales almacenados: {documentos}"
                        )
                    else:
                        # Campo normal - verificar si es un campo de archivo
                        field_value = request.form.get(header, "")

                        # Verificar si hay un archivo nuevo para este campo
                        file_field = request.files.get(f"{header}_file")

                        if file_field and file_field.filename:
                            # Hay un archivo nuevo, procesarlo
                            import uuid  # noqa: I001

                            from werkzeug.utils import secure_filename

                            from app.routes.catalogs_routes import get_upload_dir

                            filename = secure_filename(
                                f"{uuid.uuid4().hex}_{file_field.filename}"
                            )
                            upload_dir = get_upload_dir()
                            file_path = os.path.join(upload_dir, filename)
                            file_field.save(file_path)

                            # Subir a S3 si está habilitado
                            use_s3 = os.environ.get("USE_S3", "false").lower() == "true"
                            if use_s3:
                                try:
                                    from app.utils.s3_utils import upload_file_to_s3_direct

                                    logger.info(f"Subiendo archivo a S3: {filename}")
                                    # Leer el archivo y subirlo directamente a S3
                                    with open(file_path, "rb") as file_obj:
                                        from werkzeug.datastructures import FileStorage

                                        file_storage = FileStorage(
                                            stream=file_obj,
                                            filename=filename,
                                            content_type=(
                                                "image/jpeg"
                                                if header.lower() in ["imagen", "imagenes"]
                                                else "application/octet-stream"
                                            ),
                                        )
                                        result = upload_file_to_s3_direct(
                                            file_storage, filename
                                        )

                                    if result["success"]:
                                        logger.info(f"Archivo subido a S3: {result['url']}")
                                        # Eliminar el archivo local después de subirlo a S3
                                        os.remove(file_path)
                                        updated_row[header] = result["url"]
                                    else:
                                        logger.error(
                                            f"Error subiendo archivo a S3: {result['error']}"
                                        )
                                        # Si falla S3, mantener local
                                        updated_row[header] = filename
                                except Exception as e:
                                    logger.error(f"Error en proceso S3 para archivo: {e}")
                                    # Si falla S3, mantener local
                                    updated_row[header] = filename
                            else:
                                # Almacenamiento local
                                logger.info(f"Archivo guardado localmente: {filename}")
                                updated_row[header] = filename

                            logger.info(
                                f"[ADMIN_EDIT_ROW] {header} archivo actualizado: {updated_row[header]}"
                            )
                        elif field_value:
                            # Hay un valor de URL/texto nuevo
                            updated_row[header] = field_value
                            logger.info(
                                f"[ADMIN_EDIT_ROW] {header} valor actualizado: {field_value}"
                            )
                        else:
                            # No hay valor nuevo, preservar el existente
                            existing_value = row_data.get(header, "")
                            updated_row[header] = existing_value
                            logger.info(
                                f"[ADMIN_EDIT_ROW] {header} valor existente preservado: {existing_value}"
                            )

                # Manejar eliminación de documentos y multimedia
                deleted_documents = request.form.get("deleted_documents", "")
                deleted_multimedia = request.form.get("deleted_multimedia", "")

                if deleted_documents:
                    try:
                        import json

                        deleted_docs = json.loads(deleted_documents)
                        for deleted_doc in deleted_docs:
                            header = deleted_doc.get("header")
                            value = deleted_doc.get("value")
                            logger.info(
                                f"[ADMIN_EDIT_ROW] 🗑️ Procesando documento eliminado - Header: {header}, Value: {value}"
                            )
                            logger.info(
                                f"[ADMIN_EDIT_ROW] 📋 Estado actual de updated_row[{header}]: {updated_row.get(header)}"
                            )

                            if header in updated_row and updated_row[header]:
                                if hasattr(
                                    updated_row[header], "__iter__"
                                ) and not isinstance(updated_row[header], str):
                                    # Es una lista/array, remover de la lista
                                    original_count = len(updated_row[header])
                                    updated_row[header] = [
                                        doc for doc in updated_row[header] if doc != value
                                    ]
                                    new_count = len(updated_row[header])
                                    logger.info(
                                        f"[ADMIN_EDIT_ROW] ✅ Documento eliminado de lista - Original: {original_count}, Nuevo: {new_count}"
                                    )
                                    # Si queda vacía, mantener como lista vacía
                                    if not updated_row[header]:
                                        updated_row[header] = []
                                else:
                                    # Si es un valor único, eliminar la clave
                                    if updated_row[header] == value:
                                        updated_row[header] = ""
                                        logger.info(
                                            f"[ADMIN_EDIT_ROW] ✅ Documento único eliminado: {header}"
                                        )
                                    else:
                                        logger.warning(
                                            f"[ADMIN_EDIT_ROW] ❌ No se pudo eliminar documento único - Valor no coincide: {updated_row[header]} != {value}"
                                        )
                            else:
                                logger.warning(
                                    f"[ADMIN_EDIT_ROW] ❌ No se pudo eliminar documento - Header no encontrado o vacío: {header}"
                                )
                        logger.info(
                            f"[ADMIN_EDIT_ROW] Documentos eliminados: {deleted_docs}"
                        )
                    except Exception as e:
                        logger.error(
                            f"[ADMIN_EDIT_ROW] Error procesando documentos eliminados: {e}"
                        )

                if deleted_multimedia:
                    try:
                        import json

                        deleted_media = json.loads(deleted_multimedia)
                        logger.info(
                            f"[ADMIN_EDIT_ROW] 🗑️  Procesando multimedia eliminado: {deleted_media}"
                        )
                        logger.info(
                            f"[ADMIN_EDIT_ROW] 📋 Estado de updated_row antes de eliminar multimedia: {updated_row}"
                        )

                        for deleted_item in deleted_media:
                            header = deleted_item.get("header")
                            value = deleted_item.get("value")
                            logger.info(
                                f"[ADMIN_EDIT_ROW] 🎯 Eliminando multimedia - Header: {header}, Value: {value}"
                            )
                            if header in updated_row and updated_row[header] == value:
                                updated_row[header] = ""
                                logger.info(
                                    f"[ADMIN_EDIT_ROW] ✅ Multimedia eliminado correctamente: {header}"
                                )
                            else:
                                logger.warning(
                                    f"[ADMIN_EDIT_ROW] ❌ No se pudo eliminar multimedia - Header: {header}, Value: {value}, Current: {updated_row.get(header)}"
                                )

                        logger.info(
                            f"[ADMIN_EDIT_ROW] 📋 Estado de updated_row después de eliminar multimedia: {updated_row}"
                        )
                    except Exception as e:
                        logger.error(
                            f"[ADMIN_EDIT_ROW] ❌ Error procesando multimedia eliminado: {e}"
                        )

                # Manejo de imágenes (mantener compatibilidad)
                if "images" in request.files:
                    files = request.files.getlist("images")
                    from app.routes.catalogs_routes import (  # noqa: I001
                        allowed_image,
                        get_upload_dir,
                    )

                    upload_dir = get_upload_dir()
                    nuevas_imagenes = []
                    for file in files:
                        if file and file.filename and allowed_image(file.filename):
                            import uuid  # noqa: I001

                            from werkzeug.utils import secure_filename

                            filename = secure_filename(
                                f"{uuid.uuid4().hex}_{file.filename}"
                            )
                            file_path = os.path.join(upload_dir, filename)
                            file.save(file_path)

                            # Subir a S3 si está habilitado
                            use_s3 = os.environ.get("USE_S3", "false").lower() == "true"
                            if use_s3:
                                try:
                                    from app.utils.s3_utils import upload_file_to_s3_direct

                                    logger.info(f"Subiendo imagen a S3: {filename}")
                                    # Leer el archivo y subirlo directamente a S3
                                    with open(file_path, "rb") as file_obj:
                                        from werkzeug.datastructures import FileStorage

                                        file_storage = FileStorage(
                                            stream=file_obj,
                                            filename=filename,
                                            content_type="image/jpeg",
                                        )
                                        result = upload_file_to_s3_direct(
                                            file_storage, filename
                                        )

                                    if result["success"]:
                                        logger.info(f"Imagen subida a S3: {result['url']}")
                                        # Eliminar el archivo local después de subirlo a S3
                                        os.remove(file_path)
                                        nuevas_imagenes.append(result["url"])
                                    else:
                                        logger.error(
                                            f"Error subiendo imagen a S3: {result['error']}"
                                        )
                                        # Si falla S3, mantener local
                                        nuevas_imagenes.append(filename)
                                except Exception as e:
                                    logger.error(f"Error en proceso S3 para imagen: {e}")
                                    # Si falla S3, mantener local
                                    nuevas_imagenes.append(filename)
                            else:
                                # Almacenamiento local
                                nuevas_imagenes.append(filename)
                    if nuevas_imagenes:
                        existing_images = updated_row.get("images", [])
                        if isinstance(existing_images, list):
                            updated_row["images"] = existing_images + nuevas_imagenes
                        else:
                            updated_row["images"] = nuevas_imagenes

                # Eliminar imágenes seleccionadas
                delete_images = request.form.getlist("delete_images")
                if delete_images:
                    current_images = updated_row.get("images", [])
                    if isinstance(current_images, list):
                        updated_row["images"] = [
                            img for img in current_images if img not in delete_images
                        ]
                    else:
                        updated_row["images"] = []
                # Actualizar la fila en el catálogo
                catalog["rows"][row_index] = updated_row

                # Actualizar en la base de datos
                _ = collection.update_one(
                    {"_id": ObjectId(catalog_id)}, {"$set": {"rows": catalog["rows"]}}
                )

                flash("Fila actualizada correctamente", "success")
                return redirect(
                    url_for(
                        "admin.ver_catalogo_unificado",
                        collection_source=collection_source,
                        catalog_id=catalog_id,
                    )
                )

            # Renderizar formulario de edición
            return render_template(
                "admin/editar_fila.html", catalog=catalog, row=row_data, row_index=row_index
            )

        except Exception as e:
            logger.error(f"Error en editar_fila_admin: {str(e)}", exc_info=True)
            flash(f"Error al editar la fila: {str(e)}", "error")
            return redirect(url_for("admin.dashboard_admin"))


    @admin_bp.route("/admin/catalogo/<catalog_id>/get-images", methods=["GET"])
    @admin_required
    def get_catalog_images(catalog_id: str):
        """
        Obtiene las imágenes disponibles en un catálogo para la funcionalidad de miniatura automática
        """
        try:
            db = get_mongo_db()
            if db is None:
                return jsonify({"error": "No se pudo acceder a la base de datos"}), 500

            # Buscar en las colecciones principales
            catalog = None
            collections_to_check = ["spreadsheets", "catalogs"]

            for collection_name in collections_to_check:
                collection = db[collection_name]
                try:
                    catalog = collection.find_one({"_id": ObjectId(catalog_id)})
                    if catalog:
                        break
                except Exception as e:
                    current_app.logger.warning(
                        f"Error buscando en colección {collection_name}: {str(e)}"
                    )
                    continue

            if not catalog:
                return jsonify({"error": "Catálogo no encontrado"}), 404

            # Extraer imágenes de las filas del catálogo
            images = []
            data_to_search = get_catalog_rows(catalog)

            for row in data_to_search:
                if isinstance(row, dict):
                    # Buscar campos que contengan imágenes
                    for _key, value in row.items():
                        if isinstance(value, str) and any(
                            ext in value.lower()
                            for ext in [".jpg", ".jpeg", ".png", ".gif", ".webp", "http"]
                        ):
                            if value.startswith(("http://", "https://", "/")):
                                images.append(value)
                        elif isinstance(value, list):
                            for item in value:
                                if isinstance(item, str) and any(
                                    ext in item.lower()
                                    for ext in [
                                        ".jpg",
                                        ".jpeg",
                                        ".png",
                                        ".gif",
                                        ".webp",
                                        "http",
                                    ]
                                ):
                                    if item.startswith(("http://", "https://", "/")):
                                        images.append(item)

                    # Buscar específicamente en campo 'imagenes' si existe
                    if "imagenes" in row and isinstance(row["imagenes"], list):
                        for img in row["imagenes"]:
                            if isinstance(img, str) and img.startswith(
                                ("http://", "https://", "/")
                            ):
                                images.append(img)

            # Eliminar duplicados y limitar a 20 imágenes
            unique_images = list(dict.fromkeys(images))[:20]

            return jsonify({"images": unique_images})

        except Exception as e:
            current_app.logger.error(
                f"Error obteniendo imágenes del catálogo {catalog_id}: {str(e)}"
            )
            import traceback

            current_app.logger.error(f"Traceback completo: {traceback.format_exc()}")
            return jsonify({"error": "Error interno del servidor", "details": str(e)}), 500


    @admin_bp.route("/catalogo/<collection_source>/<catalog_id>/eliminar", methods=["POST"])
    @admin_required
    def eliminar_catalogo_admin(collection_source: str, catalog_id: str):
        try:
            logger.info(
                f"[ADMIN] Entrando en eliminar_catalogo_admin con collection_source={collection_source}, catalog_id={catalog_id}"
            )

            db = get_mongo_db()
            if db is None:
                flash("Error: No se pudo acceder a la base de datos", "error")
                return redirect(url_for("admin.dashboard_admin"))
            collection = db[collection_source]
            catalog = collection.find_one({"_id": ObjectId(catalog_id)})

            if not catalog:
                logger.warning(
                    f"[ADMIN] Catálogo no encontrado en {collection_source} para id={catalog_id}"
                )
                flash("Catálogo no encontrado", "warning")
                return redirect(url_for("admin.dashboard_admin"))

            # Eliminar el catálogo de la colección correspondiente
            result = collection.delete_one({"_id": ObjectId(catalog_id)})

            if result.deleted_count > 0:
                logger.info(
                    f"[ADMIN] Catálogo eliminado correctamente: {catalog_id} de {collection_source}"
                )
                flash("Catálogo eliminado correctamente", "success")
            else:
                logger.warning(
                    f"[ADMIN] No se pudo eliminar el catálogo: {catalog_id} de {collection_source}"
                )
                flash("No se pudo eliminar el catálogo", "warning")

            # Redirigir a la página anterior o al dashboard
            return redirect(request.referrer or url_for("admin.dashboard_admin"))
        except (AttributeError, KeyError, TypeError, ValueError) as e:
            logger.error(f"Error en eliminar_catalogo_admin: {str(e)}", exc_info=True)
            flash(f"Error al eliminar el catálogo: {str(e)}", "error")
            return redirect(url_for("admin.dashboard_admin"))


    @admin_bp.route("/catalogo/eliminar-multiple", methods=["POST"])
    @admin_required
    def eliminar_catalogos_multiple():
        """Elimina múltiples catálogos seleccionados."""
        try:
            logger.info("[ADMIN] Entrando en eliminar_catalogos_multiple")

            # Obtener los IDs de los catálogos a eliminar
            catalogos_data = request.json.get("catalogos", []) if request.json else []

            if not catalogos_data:
                return (
                    jsonify(
                        {
                            "success": False,
                            "message": "No se seleccionaron catálogos para eliminar",
                        }
                    ),
                    400,
                )

            db = get_mongo_db()
            if db is None:
                return (
                    jsonify(
                        {
                            "success": False,
                            "message": "Error: No se pudo acceder a la base de datos",
                        }
                    ),
                    500,
                )

            eliminados = []
            errores = []

            for catalogo_data in catalogos_data:
                try:
                    collection_source = catalogo_data.get("collection_source")
                    catalog_id = catalogo_data.get("catalog_id")

                    if not collection_source or not catalog_id:
                        errores.append(f"ID o colección inválidos: {catalog_id}")
                        continue

                    collection = db[collection_source]
                    catalog = collection.find_one({"_id": ObjectId(catalog_id)})

                    if not catalog:
                        errores.append(f"Catálogo no encontrado: {catalog_id}")
                        continue

                    # Eliminar el catálogo
                    result = collection.delete_one({"_id": ObjectId(catalog_id)})

                    if result.deleted_count > 0:
                        eliminados.append(
                            {
                                "id": catalog_id,
                                "name": catalog.get("name", "Sin nombre"),
                                "collection": collection_source,
                            }
                        )
                        logger.info(
                            f"[ADMIN] Catálogo eliminado: {catalog_id} de {collection_source}"
                        )
                    else:
                        errores.append(f"No se pudo eliminar: {catalog_id}")

                except Exception as e:
                    error_msg = f"Error eliminando {catalog_id}: {str(e)}"  # type: ignore
                    errores.append(error_msg)
                    logger.error(f"[ADMIN] {error_msg}")

            # Preparar respuesta
            response_data = {
                "success": True,
                "eliminados": eliminados,
                "total_eliminados": len(eliminados),
                "errores": errores,
                "total_errores": len(errores),
            }

            if eliminados:
                flash(f"Se eliminaron {len(eliminados)} catálogos correctamente", "success")
            if errores:
                flash(
                    f"Errores en {len(errores)} catálogos: {', '.join(errores[:3])}",
                    "warning",
                )

            return jsonify(response_data)

        except Exception as e:
            logger.error(
                f"[ADMIN] Error en eliminar_catalogos_multiple: {str(e)}", exc_info=True
            )
            return jsonify({"success": False, "message": f"Error interno: {str(e)}"}), 500

# Ruta movida a scripts_bp para evitar conflictos
    # @admin_bp.route("/tools")
    # @admin_required
    # def tools_dashboard():
    #     """
    #     Dashboard de herramientas y scripts del sistema.
    #     Requiere login de administrador.
    #     """
    #     return render_template('admin/tools_dashboard.html')
