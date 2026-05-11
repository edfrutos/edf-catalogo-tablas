# Script: admin_backup_routes.py
# Descripción: Rutas pequeñas de backup administrativo registradas sobre admin_bp.
# Autor: EDF Developer

import csv
import io
import json
import os
from datetime import datetime

from flask import flash, redirect, request, send_file, session, url_for

from app.audit import audit_log
from app.database import get_catalogs_collection
from app.decorators import admin_required
from app.routes.admin.admin_backup_utils import get_backup_dir
from tools.db_utils.google_drive_utils import upload_to_drive


def register_admin_backup_routes(admin_bp) -> None:
    """Registra rutas de backup sobre el blueprint admin existente."""

    @admin_bp.route("/backup/json")
    @admin_required
    def backup_json():
        catalog = get_catalogs_collection()
        if catalog is None:
            flash("Error: No se pudo acceder a la colección de catálogos", "error")
            return redirect(url_for("maintenance.maintenance_daard"))

        data = list(catalog.find())
        for d in data:
            d["_id"] = str(d["_id"])

        output = io.StringIO()
        json.dump(data, output, indent=4, default=str)
        output.seek(0)

        backups_dir = get_backup_dir()
        filename = f"catalog_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        backup_path = os.path.join(backups_dir, filename)

        with open(backup_path, "w", encoding="utf-8") as f:
            f.write(output.getvalue())

        try:
            enlace_drive = upload_to_drive(backup_path)
            os.remove(backup_path)
            flash(
                f"Backup subido a Google Drive y eliminado localmente. <a href='{enlace_drive}' target='_blank'>Ver en Drive</a>",
                "success",
            )
            audit_log(
                "backup_json_uploaded_to_drive",
                user_id=session.get("user_id"),
                details={
                    "filename": filename,
                    "username": session.get("username", "desconocido"),
                    "drive_url": enlace_drive,
                },
            )
        except (OSError, PermissionError, ValueError) as e:
            flash(
                f"Error al subir el backup a Google Drive: {str(e)}. El archivo local no se ha eliminado.",
                "danger",
            )
            audit_log(
                "backup_json_upload_failed",
                user_id=session.get("user_id"),
                details={
                    "filename": filename,
                    "username": session.get("username", "desconocido"),
                    "error": str(e),
                },
                success=False,
            )

        return send_file(
            io.BytesIO(output.read().encode()),
            download_name="backup_catalog.json",
            as_attachment=True,
        )

    @admin_bp.route("/backup/csv")
    @admin_required
    def backup_csv():
        catalog = get_catalogs_collection()
        if catalog is None:
            flash("Error: No se pudo acceder a la colección de catálogos", "error")
            return redirect(url_for("maintenance.maintenance_dashboard"))

        data = list(catalog.find())
        if not data:
            flash("No hay datos para exportar", "warning")
            return redirect(url_for("maintenance.maintenance_dashboard"))

        all_fields = set()
        for row in data:
            all_fields.update(row.keys())

        headers = list(all_fields)
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=headers)
        writer.writeheader()

        for row in data:
            row["_id"] = str(row["_id"])
            row_filled = {k: row.get(k, "") for k in headers}
            writer.writerow(row_filled)

        output.seek(0)

        backups_dir = get_backup_dir()
        filename = f"catalog_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        backup_path = os.path.join(backups_dir, filename)

        with open(backup_path, "w", encoding="utf-8") as f:
            f.write(output.getvalue())

        try:
            enlace_drive = upload_to_drive(backup_path)
            os.remove(backup_path)
            flash(
                f"Backup subido a Google Drive y eliminado localmente. <a href='{enlace_drive}' target='_blank'>Ver en Drive</a>",
                "success",
            )
            audit_log(
                "backup_csv_uploaded_to_drive",
                user_id=session.get("user_id"),
                details={
                    "filename": filename,
                    "username": session.get("username", "desconocido"),
                    "drive_url": enlace_drive,
                },
            )
        except (OSError, PermissionError, ValueError) as e:
            flash(
                f"Error al subir el backup a Google Drive: {str(e)}. El archivo local no se ha eliminado.",
                "danger",
            )
            audit_log(
                "backup_csv_upload_failed",
                user_id=session.get("user_id"),
                details={
                    "filename": filename,
                    "username": session.get("username", "desconocido"),
                    "error": str(e),
                },
                success=False,
            )

        return send_file(
            io.BytesIO(output.read().encode()),
            download_name="backup_catalog.csv",
            as_attachment=True,
        )

    @admin_bp.route("/backups/cleanup", methods=["POST"])
    @admin_required
    def cleanup_old_backups():
        days = int(request.form.get("days", 30))
        max_files = int(request.form.get("max_files", 20))
        backups_dir = get_backup_dir()

        if not os.path.exists(backups_dir):
            flash("No hay backups para limpiar", "info")
            return redirect(url_for("maintenance.maintenance_dashboard"))

        files = [
            os.path.join(backups_dir, f)
            for f in os.listdir(backups_dir)
            if os.path.isfile(os.path.join(backups_dir, f))
        ]

        files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
        now = datetime.now()
        removed = 0

        for f in files:
            mtime = datetime.fromtimestamp(os.path.getmtime(f))
            if (now - mtime).days > days:
                try:
                    os.remove(f)
                    removed += 1
                except (OSError, PermissionError):
                    pass

        files = [
            os.path.join(backups_dir, f)
            for f in os.listdir(backups_dir)
            if os.path.isfile(os.path.join(backups_dir, f))
        ]

        if len(files) > max_files:
            for f in files[max_files:]:
                try:
                    os.remove(f)
                    removed += 1
                except (OSError, PermissionError):
                    pass

        flash(f"Backups antiguos eliminados: {removed}", "info")
        audit_log(
            "backup_cleanup",
            user_id=session.get("user_id"),
            details={
                "username": session.get("username", "desconocido"),
                "days": days,
                "max_files": max_files,
                "removed_count": removed,
            },
        )
        return redirect(url_for("maintenance.maintenance_dashboard"))
