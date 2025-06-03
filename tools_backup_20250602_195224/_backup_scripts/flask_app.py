#!/usr/bin/env python3
from flask import Flask, render_template, send_from_directory
import os

app = Flask(__name__, 
           static_folder='static',
           template_folder='templates')

@app.route('/')
def hello():
    return "¡La aplicación Flask funciona correctamente!"

@app.route('/ver-plantillas')
def list_templates():
    try:
        template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
        if os.path.exists(template_dir):
            templates = os.listdir(template_dir)
            return f"Plantillas disponibles: {', '.join(templates)}"
        else:
            return "El directorio de plantillas no existe."
    except Exception as e:
        return f"Error al listar plantillas: {str(e)}"

@app.route('/ver-estaticos')
def list_static():
    try:
        static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
        if os.path.exists(static_dir):
            static_files = os.listdir(static_dir)
            return f"Archivos estáticos: {', '.join(static_files)}"
        else:
            return "El directorio static no existe."
    except Exception as e:
        return f"Error al listar archivos estáticos: {str(e)}"

@app.route('/login-simple')
def login_simple():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Login</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 0; padding: 20px; }
            .container { max-width: 500px; margin: 0 auto; }
            .form-group { margin-bottom: 15px; }
            label { display: block; margin-bottom: 5px; }
            input[type="text"], input[type="password"] { width: 100%; padding: 8px; }
            button { padding: 10px 15px; background: #007bff; color: white; border: none; cursor: pointer; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Iniciar Sesión</h1>
            <form method="POST" action="/login">
                <div class="form-group">
                    <label for="username">Usuario:</label>
                    <input type="text" id="username" name="username" required>
                </div>
                <div class="form-group">
                    <label for="password">Contraseña:</label>
                    <input type="password" id="password" name="password" required>
                </div>
                <button type="submit">Acceder</button>
            </form>
        </div>
    </body>
    </html>
    """

@app.route('/plantilla-simple')
def plantilla_simple():
    try:
        return render_template('login.html')
    except Exception as e:
        return f"Error al renderizar plantilla: {str(e)}"

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)