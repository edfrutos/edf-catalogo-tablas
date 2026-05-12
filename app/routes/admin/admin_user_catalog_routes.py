# Script: admin_user_catalog_routes.py
# Descripción: Rutas administrativas de catálogos asociados a usuarios.
# Autor: EDF Developer

import logging
from typing import Any, Dict

from bson import ObjectId
from flask import flash, redirect, render_template, url_for

from app.database import get_mongo_db, get_users_collection
from app.decorators import admin_required
from app.utils.catalog_utils import normalize_catalog_rows


logger = logging.getLogger(__name__)


def register_admin_user_catalog_routes(admin_bp) -> None:
    """Registra rutas administrativas de catálogos de usuario sobre el blueprint admin."""

    @admin_bp.route("/catalogos-usuario/<user_id>")
    @admin_required
    def ver_catalogos_usuario_por_id(user_id: str):
        try:
            # Verificar que el usuario existe
            users_col = get_users_collection()
            if users_col is None:
                flash("Error: No se pudo acceder a la colección de usuarios", "error")
                return redirect(url_for("admin.lista_usuarios"))
            usuario = users_col.find_one({"_id": ObjectId(user_id)})
            if not usuario:
                flash("Usuario no encontrado", "danger")
                return redirect(url_for("admin.lista_usuarios"))

            # Obtener todos los posibles identificadores del usuario
            user_email = usuario.get("email", "")
            username = usuario.get("username", "")
            nombre = usuario.get("name", "")
            posibles = {user_email, username, nombre}
            posibles = {v for v in posibles if v}
            logger.info(
                f"[ADMIN] Buscando catálogos para el usuario con ID: {user_id}, posibles: {posibles}"
            )

            # Obtener los catálogos del usuario de ambas colecciones
            collections_to_check = ["catalogs", "spreadsheets"]
            all_catalogs = []

            for collection_name in collections_to_check:
                try:
                    db = get_mongo_db()
                    if db is None:
                        continue
                    collection = db[collection_name]
                    # Buscar por todos los campos posibles
                    query: Dict[str, Any] = {"$or": []}
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
                    catalogs_cursor = collection.find(query)
                    for catalog in catalogs_cursor:
                        catalog["collection_source"] = collection_name
                        catalog["_id_str"] = str(catalog["_id"])
                        all_catalogs.append(catalog)
                    logger.info(
                        f"[ADMIN] Encontrados {collection.count_documents(query)} catálogos en {collection_name} para {posibles}"
                    )
                except (AttributeError, KeyError, TypeError, ValueError) as e:
                    logger.error(
                        f"Error al buscar catálogos en {collection_name}: {str(e)}"
                    )

            catalogs = all_catalogs
            logger.info(
                f"[ADMIN] Total de catálogos encontrados para {posibles}: {len(catalogs)}"
            )

            # Añadir información adicional a cada catálogo
            for catalog in catalogs:
                normalize_catalog_rows(catalog)
                if "created_at" in catalog and catalog["created_at"]:
                    try:
                        if hasattr(catalog["created_at"], "strftime"):
                            catalog["created_at_formatted"] = catalog[
                                "created_at"
                            ].strftime("%d/%m/%Y %H:%M")
                        else:
                            catalog["created_at_formatted"] = str(catalog["created_at"])
                    except (AttributeError, ValueError, TypeError) as e:
                        logger.error(f"Error al formatear fecha: {str(e)}")
                        catalog["created_at_formatted"] = str(catalog["created_at"])
                else:
                    catalog["created_at_formatted"] = "Fecha desconocida"

            return render_template(
                "admin/catalogos_usuario.html", catalogs=catalogs, user=usuario
            )
        except (AttributeError, KeyError, TypeError, ValueError) as e:
            logger.error(f"Error en ver_catalogos_usuario: {str(e)}", exc_info=True)
            flash(f"Error al cargar los catálogos del usuario: {str(e)}", "error")
            return redirect(url_for("admin.lista_usuarios"))
