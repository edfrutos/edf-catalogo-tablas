"""Rutas de Ajustes de la edición de tienda."""

from __future__ import annotations

import datetime as _dt
import logging
import os

from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from app import store_settings as ajustes
from app.decorators import admin_required
from app.store_backup_zip import crear_zip

logger = logging.getLogger(__name__)

store_settings_bp = Blueprint("store_settings", __name__)


def _db():
    from app.database import get_mongo_db

    return get_mongo_db()


@store_settings_bp.route("/ajustes")
@admin_required
def ver():
    db = _db()
    datos = ajustes.cargar(db)
    carpeta_activa = ajustes.carpeta_de_copias(datos)
    return render_template(
        "admin/ajustes.html",
        ajustes=datos,
        carpeta_activa=carpeta_activa,
    )


@store_settings_bp.route("/ajustes/perfil", methods=["POST"])
@admin_required
def guardar_perfil():
    perfil, errores = ajustes.validar_perfil(request.form)
    if errores:
        for e in errores:
            flash(e, "danger")
        return redirect(url_for("store_settings.ver"))
    db = _db()
    ajustes.guardar_perfil(db, perfil)
    # El nombre se muestra en la barra superior
    from app.store_edition import LOCAL_EMAIL

    db["users"].update_one(
        {"email": LOCAL_EMAIL}, {"$set": {"nombre": perfil["nombre"], "name": perfil["nombre"]}}
    )
    session["nombre"] = perfil["nombre"]
    flash("Perfil guardado.", "success")
    return redirect(url_for("store_settings.ver"))


@store_settings_bp.route("/ajustes/carpeta", methods=["POST"])
@admin_required
def guardar_carpeta():
    carpeta = (request.form.get("carpeta") or "").strip()
    marcador = (request.form.get("marcador") or "").strip()
    if not ajustes.es_escribible(carpeta):
        flash("No se puede escribir en esa carpeta. Elige otra.", "danger")
        return redirect(url_for("store_settings.ver"))
    ajustes.guardar_carpeta(_db(), carpeta, marcador)
    flash("Carpeta de copias guardada.", "success")
    return redirect(url_for("store_settings.ver"))


@store_settings_bp.route("/ajustes/carpeta/olvidar", methods=["POST"])
@admin_required
def olvidar_carpeta():
    ajustes.olvidar_carpeta(_db())
    flash("Carpeta de copias eliminada de los ajustes.", "success")
    return redirect(url_for("store_settings.ver"))


@store_settings_bp.route("/ajustes/guardar-copia", methods=["POST"])
@admin_required
def guardar_copia():
    db = _db()
    carpeta = ajustes.carpeta_de_copias(ajustes.cargar(db))
    if not carpeta:
        flash("Elige primero una carpeta de copias accesible.", "warning")
        return redirect(url_for("store_settings.ver"))
    sello = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    destino = os.path.join(carpeta, f"TablaTeca_copia_{sello}.zip")
    parcial = destino + ".parte"
    try:
        with open(parcial, "wb") as f:
            crear_zip(db, current_app.config["UPLOAD_FOLDER"], f)
        os.replace(parcial, destino)
    except OSError:
        logger.exception("No se pudo guardar la copia en la carpeta elegida")
        try:
            os.remove(parcial)
        except OSError:
            pass
        flash("No se pudo guardar la copia en esa carpeta.", "danger")
        return redirect(url_for("store_settings.ver"))
    flash(f"Copia guardada: {os.path.basename(destino)}", "success")
    return redirect(url_for("store_settings.ver"))
