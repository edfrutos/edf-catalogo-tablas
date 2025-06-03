#!/usr/bin/env python3
"""
Módulo auxiliar para garantizar el acceso a la ruta /tables/
Implementación independiente que no depende de blueprints
"""
import logging
import traceback
from flask import render_template, redirect, session, request

# Configuración de logging
logger = logging.getLogger(__name__)

def register_tables_direct_routes(app):
    """
    Registra rutas directas para acceso a tablas.
    Esta función debe ser importada y llamada desde app.py.
    """
    logger.info("Registrando rutas directas para acceso a tablas...")
    
    @app.route('/direct_tables/')
    def direct_tables_list():
        """Ruta directa para listar todas las tablas"""
        try:
            # Obtener la sesión actual
            user_id = session.get('user_id', 'no-user')
            email = session.get('email', 'no-email')
            username = session.get('username', 'no-username')
            role = session.get('role', 'no-role')
            
            logger.info(f"Acceso directo a lista de tablas por: {email}")
            
            # Mostrar página de emergencia simple
            emergency_html = """
            <!DOCTYPE html>
            <html lang="es">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Tablas - Acceso Directo</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 40px; }
                    h1 { color: #2c3e50; }
                    .alert { background-color: #d4edda; border: 1px solid #c3e6cb; padding: 15px; border-radius: 4px; margin-bottom: 20px; }
                    .btn { display: inline-block; padding: 6px 12px; margin: 2px; text-decoration: none; background-color: #007bff; color: white; border-radius: 4px; }
                    .btn-secondary { background-color: #6c757d; }
                    .nav { margin-bottom: 20px; }
                    .nav a { margin-right: 15px; }
                </style>
            </head>
            <body>
                <h1>Tablas de Usuarios - Acceso Directo</h1>
                
                <div class="nav">
                    <a href="/admin/" class="btn">Panel Admin</a>
                    <a href="/admin.html" class="btn">Acceso Estático</a>
                </div>
                
                <div class="alert">
                    Estás utilizando el modo de acceso directo garantizado.
                </div>
                
                <p>Sesión actual:</p>
                <ul>
                    <li>Usuario ID: {user_id}</li>
                    <li>Email: {email}</li>
                    <li>Username: {username}</li>
                    <li>Rol: {role}</li>
                </ul>
                
                <h2>Lista de Tablas</h2>
                <p>Esta es una versión simplificada del gestor de tablas.</p>
                
                <h2>Acciones rápidas</h2>
                <p>
                    <a href="/admin/" class="btn">Volver al Panel</a>
                </p>
            </body>
            </html>
            """.format(
                user_id=user_id,
                email=email,
                username=username,
                role=role
            )
            
            return emergency_html
            
        except Exception as e:
            logger.error(f"Error en direct_tables_list: {str(e)}")
            traceback.print_exc()
            return "Error al cargar tablas. Por favor, vuelve al <a href='/admin/'>Panel Admin</a>."
    
    @app.route('/direct_tables/<table_id>')
    def direct_table_view(table_id):
        """Ruta directa para ver una tabla específica"""
        try:
            # Obtener la sesión actual
            user_id = session.get('user_id', 'no-user')
            email = session.get('email', 'no-email')
            username = session.get('username', 'no-username')
            role = session.get('role', 'no-role')
            
            logger.info(f"Acceso directo a tabla {table_id} por: {email}")
            
            # Devolver HTML básico con información de la tabla
            emergency_html = """
            <!DOCTYPE html>
            <html lang="es">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Tabla {table_id} - Acceso Directo</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 40px; }}
                    h1 {{ color: #2c3e50; }}
                    .alert {{ background-color: #d4edda; border: 1px solid #c3e6cb; padding: 15px; border-radius: 4px; margin-bottom: 20px; }}
                    .btn {{ display: inline-block; padding: 6px 12px; margin: 2px; text-decoration: none; background-color: #007bff; color: white; border-radius: 4px; }}
                    .btn-secondary {{ background-color: #6c757d; }}
                    .nav {{ margin-bottom: 20px; }}
                    .nav a {{ margin-right: 15px; }}
                </style>
            </head>
            <body>
                <h1>Tabla {table_id} - Acceso Directo</h1>
                
                <div class="nav">
                    <a href="/admin/" class="btn">Panel Admin</a>
                    <a href="/direct_tables/" class="btn">Todas las Tablas</a>
                    <a href="/admin.html" class="btn">Acceso Estático</a>
                </div>
                
                <div class="alert">
                    Estás viendo la tabla {table_id} en modo de acceso directo.
                </div>
                
                <p>Estás viendo la tabla con ID: <strong>{table_id}</strong></p>
                
                <h2>Sesión actual</h2>
                <ul>
                    <li>Usuario ID: {user_id}</li>
                    <li>Email: {email}</li>
                    <li>Username: {username}</li>
                    <li>Rol: {role}</li>
                </ul>
                
                <h2>Acciones disponibles</h2>
                <p>
                    <a href="/direct_tables/" class="btn">Ver todas las tablas</a>
                    <a href="/admin/" class="btn btn-secondary">Volver al Panel Admin</a>
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
            logger.error(f"Error en direct_table_view: {str(e)}")
            return f"Error al mostrar la tabla {table_id}. Por favor, vuelve al <a href='/admin/'>Panel Admin</a>."
    
    # Redirecciones de /tables/ a /direct_tables/
    @app.route('/tables/')
    def tables_redirect():
        logger.info("⚠️ Redirigiendo de /tables/ a /direct_tables/")
        return redirect('/direct_tables/')
    
    @app.route('/tables/<table_id>')
    def table_redirect(table_id):
        logger.info(f"⚠️ Redirigiendo de /tables/{table_id} a /direct_tables/{table_id}")
        return redirect(f'/direct_tables/{table_id}')
    
    logger.info("✅ Rutas directas para tablas registradas correctamente")
    return app
