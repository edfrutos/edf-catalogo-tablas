# Script: tables_helper.py
# Descripción: [Módulo auxiliar para garantizar el acceso a la ruta /tables/Este módulo proporciona rutas alternativas y funciones de manejo para solucionar problemas con la visualización de tablas.]
# Uso: python3 tables_helper.py [opciones]
# Requiere: [librerías externas, si aplica]
# Variables de entorno: [si aplica]
# Autor: EDF Developer - 2025-05-28

"""
Módulo auxiliar para garantizar el acceso a la ruta /tables/
Este módulo proporciona rutas alternativas y funciones de manejo para
solucionar problemas con la visualización de tablas.
"""
import logging
import os
import traceback
from flask import Blueprint, render_template, redirect, url_for, flash, session, request, jsonify
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime
import certifi  # Añadido para certificados SSL
from app.database import get_mongo_db

# Configuración de logging
logger = logging.getLogger(__name__)

# Crear blueprint
tables_helper_bp = Blueprint('tables_helper', __name__, url_prefix='/tables_helper')

# Usar la función centralizada de conexión a MongoDB

# Ruta auxiliar para listar tablas de forma alternativa
@tables_helper_bp.route('/')
def list_tables():
    try:
        # Obtener la sesión actual
        user_id = session.get('user_id', 'no-user')
        email = session.get('email', 'no-email')
        username = session.get('username', session.get('email', 'no-username'))
        role = session.get('role', 'no-role')
        
        logger.info(f"Acceso a lista de tablas por: {email} (ID: {user_id}, Rol: {role})")
        
        # Obtener la base de datos
        db = get_mongo_db()
        if db is None:
            return render_template('admin/tables_emergency.html', 
                                message="Error de conexión a MongoDB", 
                                tables=[], 
                                user={'email': email, 'username': username, 'role': role})
        
        # Buscar colecciones de tablas
        collections = db.list_collection_names()
        tables_collection = None
        
        # Detectar colección correcta
        if 'tables' in collections:
            tables_collection = db.tables
        elif 'tables_data' in collections:
            tables_collection = db.tables_data
        
        if tables_collection is None:
            return render_template('admin/tables_emergency.html',
                                message="No se encontró la colección de tablas",
                                tables=[],
                                user={'email': email, 'username': username, 'role': role})
        
        # Obtener todas las tablas
        tables = list(tables_collection.find().sort('created_at', -1))
        
        return render_template('admin/tables_emergency.html',
                            tables=tables,
                            user={'email': email, 'username': username, 'role': role})
    
    except Exception as e:
        logger.error(f"Error en list_tables: {str(e)}")
        traceback.print_exc()
        
        # Devolver una página de emergencia simple
        emergency_html = """
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Tablas - Acceso de Emergencia</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                h1 {{ color: #2c3e50; }}
                .alert {{ background-color: #f8d7da; border: 1px solid #f5c6cb; padding: 15px; border-radius: 4px; margin-bottom: 20px; }}
                .success {{ background-color: #d4edda; border: 1px solid #c3e6cb; }}
                table {{ width: 100%; border-collapse: collapse; }}
                table, th, td {{ border: 1px solid #ddd; }}
                th, td {{ padding: 12px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                tr:nth-child(even) {{ background-color: #f9f9f9; }}
                .btn {{ display: inline-block; padding: 6px 12px; margin: 2px; text-decoration: none; background-color: #6c757d; color: white; border-radius: 4px; }}
                .btn-primary {{ background-color: #007bff; }}
                .nav {{ margin-bottom: 20px; }}
                .nav a {{ margin-right: 15px; }}
            </style>
        </head>
        <body>
            <h1>Tablas de Usuarios - Acceso de Emergencia</h1>
            
            <div class="nav">
                <a href="/admin/" class="btn">Panel Admin</a>
                <a href="/admin.html" class="btn">Acceso Directo</a>
            </div>
            
            <div class="alert">
                Se ha producido un error al obtener las tablas de la base de datos.
                <br>Este es un modo de emergencia simplificado.
            </div>
            
            <p>Sesión actual:</p>
            <ul>
                <li>Usuario ID: {user_id}</li>
                <li>Email: {email}</li>
                <li>Username: {username}</li>
                <li>Rol: {role}</li>
            </ul>
            
            <h2>Acciones rápidas</h2>
            <p>
                <a href="/admin/" class="btn btn-primary">Volver al Panel</a>
            </p>
        </body>
        </html>
        """.format(
            user_id=session.get('user_id', 'no-user'),
            email=session.get('email', 'no-email'),
            username=session.get('username', session.get('email', 'no-username')),
            role=session.get('role', 'no-role')
        )
        
        return emergency_html

# Vista de tabla por ID
@tables_helper_bp.route('/<table_id>')
def view_table(table_id):
    try:
        # Obtener la sesión actual
        user_id = session.get('user_id', 'no-user')
        email = session.get('email', 'no-email')
        username = session.get('username', session.get('email', 'no-username'))
        role = session.get('role', 'no-role')
        
        logger.info(f"Acceso a tabla {table_id} por: {email}")
        
        # Devolver HTML básico con información
        emergency_html = """
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Tabla {table_id} - Acceso de Emergencia</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                h1 {{ color: #2c3e50; }}
                .alert {{ background-color: #f8d7da; border: 1px solid #f5c6cb; padding: 15px; border-radius: 4px; margin-bottom: 20px; }}
                .success {{ background-color: #d4edda; border: 1px solid #c3e6cb; }}
                pre {{ background-color: #f8f9fa; padding: 15px; border-radius: 4px; overflow: auto; }}
                .btn {{ display: inline-block; padding: 6px 12px; margin: 2px; text-decoration: none; background-color: #6c757d; color: white; border-radius: 4px; }}
                .btn-primary {{ background-color: #007bff; }}
                .nav {{ margin-bottom: 20px; }}
                .nav a {{ margin-right: 15px; }}
            </style>
        </head>
        <body>
            <h1>Tabla {table_id} - Modo Emergencia</h1>
            
            <div class="nav">
                <a href="/admin/" class="btn">Panel Admin</a>
                <a href="/tables_helper/" class="btn">Todas las Tablas</a>
                <a href="/admin.html" class="btn">Acceso Directo</a>
            </div>
            
            <div class="alert success">
                Estás viendo la tabla {table_id} en modo de emergencia.
            </div>
            
            <h2>Detalles de la tabla</h2>
            <p>Se ha solicitado la vista de la tabla con ID: <strong>{table_id}</strong></p>
            
            <h2>Sesión actual</h2>
            <ul>
                <li>Usuario ID: {user_id}</li>
                <li>Email: {email}</li>
                <li>Username: {username}</li>
                <li>Rol: {role}</li>
            </ul>
            
            <h2>Acciones disponibles</h2>
            <p>
                <a href="/tables_helper/" class="btn btn-primary">Volver a todas las tablas</a>
                <a href="/admin/" class="btn">Volver al Panel Admin</a>
            </p>
        </body>
        </html>
        """.format(
            table_id=table_id,
            user_id=user_id,
            email=email,
            username=username,
            role=role
        )
        
        return emergency_html
        
    except Exception as e:
        logger.error(f"Error en view_table: {str(e)}")
        return f"Error al mostrar la tabla: {str(e)}"
