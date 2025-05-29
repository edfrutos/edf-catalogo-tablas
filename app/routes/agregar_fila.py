# Script: agregar_fila.py
# Descripción: [Explica brevemente qué hace el script]
# Uso: python3 agregar_fila.py [opciones]
# Requiere: [librerías externas, si aplica]
# Variables de entorno: [si aplica]
# Autor: [Tu nombre o equipo] - 2025-05-28

from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, session
from bson.objectid import ObjectId
import logging

logger = logging.getLogger(__name__)

def agregar_fila_route(main_bp):
    @main_bp.route("/agregar_fila/<tabla_id>", methods=["GET", "POST"])
    def agregar_fila(tabla_id):
        # Verificar sesión
        if "username" not in session:
            flash("Debe iniciar sesión para agregar filas", "warning")
            return redirect(url_for("auth.login"))
        
        try:
            # Obtener la tabla
            tabla = current_app.spreadsheets_collection.find_one({"_id": ObjectId(tabla_id)})
            if not tabla:
                flash("Tabla no encontrada", "error")
                return redirect(url_for("main.dashboard_user"))
            
            # Verificar permisos: solo el propietario o admin puede agregar filas
            if session.get("role") != "admin" and session.get("username") != tabla.get("owner"):
                flash("No tiene permisos para agregar filas a esta tabla", "error")
                return redirect(url_for("main.dashboard_user"))
            
            if request.method == "POST":
                # Obtener datos del formulario
                nueva_fila = {}
                for header in tabla.get("headers", []):
                    nueva_fila[header] = request.form.get(header, "")
                
                # Agregar la fila a la tabla
                current_app.spreadsheets_collection.update_one(
                    {"_id": ObjectId(tabla_id)},
                    {"$push": {"data": nueva_fila}, "$inc": {"num_rows": 1}}
                )
                
                flash("Fila agregada correctamente", "success")
                return redirect(url_for("main.ver_tabla", table_id=tabla_id))
            
            # Para peticiones GET, mostrar el formulario
            return render_template("agregar_fila_tabla.html", tabla=tabla)
        except Exception as e:
            logger.error(f"Error al agregar fila: {str(e)}", exc_info=True)
            flash(f"Error al agregar fila: {str(e)}", "error")
            return redirect(url_for("main.dashboard_user"))
    
    return agregar_fila
