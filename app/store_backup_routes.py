"""Rutas de la copia ZIP de la edición de tienda (exportar e importar)."""

from __future__ import annotations

import datetime as _dt
import logging
import os
import tempfile

from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    send_file,
    url_for,
)

from app.decorators import admin_required
from app.store_backup_zip import ZipInvalido, crear_zip, importar_zip
from app.utils.paths import backups_dir

logger = logging.getLogger(__name__)

store_backup_bp = Blueprint("store_backup", __name__)


def _carpeta_copias() -> str:
    return current_app.config.get("STORE_BACKUP_DIR") or backups_dir(
        os.path.join(os.path.dirname(current_app.root_path), "backups")
    )


@store_backup_bp.route("/admin/backup/zip")
@admin_required
def exportar_zip():
    from app.database import get_mongo_db

    db = get_mongo_db()
    if db is None:
        flash("No se pudo acceder a los datos.", "danger")
        return redirect(url_for("catalogs.list"))
    salida = tempfile.TemporaryFile()
    crear_zip(db, current_app.config["UPLOAD_FOLDER"], salida)
    salida.seek(0)
    sello = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    return send_file(
        salida,
        mimetype="application/zip",
        as_attachment=True,
        download_name=f"TablaTeca_copia_{sello}.zip",
    )


@store_backup_bp.route("/admin/backup/importar", methods=["GET", "POST"])
@admin_required
def importar():
    if request.method == "GET":
        return render_template("admin/importar_zip.html")

    archivo = request.files.get("archivo")
    if archivo is None or not archivo.filename:
        flash("Elige el archivo ZIP de la copia.", "warning")
        return redirect(url_for("store_backup.importar"))
    if request.form.get("confirmo") != "1":
        flash("Confirma que entiendes que se sustituirán tus catálogos actuales.", "warning")
        return redirect(url_for("store_backup.importar"))

    from app.database import get_mongo_db
    from app.store_edition import ensure_local_user

    db = get_mongo_db()
    if db is None:
        flash("No se pudo acceder a los datos.", "danger")
        return redirect(url_for("store_backup.importar"))
    try:
        resultado = importar_zip(
            db,
            current_app.config["UPLOAD_FOLDER"],
            archivo.stream,
            _carpeta_copias(),
            ensure_local_user(db),
        )
    except ZipInvalido as exc:
        flash(str(exc), "danger")
        return redirect(url_for("store_backup.importar"))
    except Exception:  # noqa: BLE001 - el usuario recibe un mensaje claro y el detalle va al log
        logger.exception("Error al importar la copia")
        flash("No se pudo importar la copia. Tus datos anteriores se han conservado.", "danger")
        return redirect(url_for("store_backup.importar"))

    flash(
        f"Copia importada: {resultado['catalogos']} catálogos y {resultado['archivos']} archivos. "
        "Antes de importar se guardó una copia automática del estado anterior.",
        "success",
    )
    return redirect(url_for("catalogs.list"))
