#!/usr/bin/env python3
"""
Script para reparar problemas de sesión y acceso directo
Este script puede ejecutarse directamente desde la terminal
"""

import os
import sys
from datetime import datetime

from dotenv import load_dotenv
from pymongo import MongoClient
from werkzeug.security import generate_password_hash

# Cargar variables de entorno
load_dotenv()

# Conectar a MongoDB
MONGO_URI = os.getenv('MONGO_URI')
db_name = os.getenv('MONGODB_DB', 'app_catalogojoyero_nueva')
client = MongoClient(MONGO_URI)
db = client[db_name]
users = db["users"]
sessions = db["flask_session"]  # Colección donde Flask puede guardar sesiones

def crear_usuario_acceso():
    """Crea un usuario garantizado para acceso normal con permisos de usuario"""
    # Datos del usuario de acceso garantizado
    acceso_user = {
        "nombre": "Usuario Acceso Garantizado",
        "username": "acceso_user",
        "email": "acceso@example.com",
        "password": generate_password_hash("acceso123"),
        "created_at": datetime.utcnow(),
        "role": "user",
        "updated_at": datetime.utcnow().isoformat(),
        "failed_attempts": 0,
        "last_ip": "",
        "last_login": None,
        "locked_until": None,
        "num_tables": 0,
        "password_updated_at": datetime.utcnow().isoformat(),
        "tables_updated_at": None,
        # Campos extra para garantizar compatibilidad
        "usuario": "acceso_user",
        "rol": "user",
        "logged_in": True
    }

    # Verificar si ya existe
    existing = users.find_one({"email": "acceso@example.com"})
    if existing:
        print("✅ El usuario de acceso garantizado ya existe")
        print(f"ID: {existing['_id']}")
        return str(existing['_id'])
    else:
        # Crear el usuario
        result = users.insert_one(acceso_user)
        print(f"✅ Usuario de acceso garantizado creado con ID: {result.inserted_id}")
        return str(result.inserted_id)

def modificar_permisos():
    """Permite acceder a las rutas sin autenticación (solo para depuración)"""
    print("🔄 Modificando archivo app/decorators.py para permitir acceso sin autenticación...")
    decorators_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app', 'decorators.py')

    if not os.path.exists(decorators_path):
        print("❌ No se encontró el archivo de decoradores")
        return False

    # Leer el archivo actual
    with open(decorators_path) as f:
        content = f.read()

    # Buscar la función login_required
    if "def login_required(f):" in content:
        # Crear copia de seguridad
        with open(f"{decorators_path}.bak", 'w') as f:
            f.write(content)

        # Modificar el contenido para permitir acceso sin autenticación
        modified = content.replace(
            "def login_required(f):\n    def wrapper(*args, **kwargs):\n        if 'user_id' not in session:",
            "def login_required(f):\n    def wrapper(*args, **kwargs):\n        # DEBUG - BYPASS AUTENTICACIÓN\n        print('DEBUG: Bypasseando autenticación')\n        return f(*args, **kwargs)\n        # Código original:\n        if False and 'user_id' not in session:"
        )

        # Guardar los cambios
        with open(decorators_path, 'w') as f:
            f.write(modified)

        print("✅ Decorador login_required modificado para permitir acceso sin autenticación")
        return True
    else:
        print("❌ No se encontró la función login_required en el archivo")
        return False

def crear_pagina_acceso_rapido():
    """Crea una página HTML simple para acceso directo"""
    acceso_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'acceso.html')

    html_content = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Acceso Garantizado</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .btn { 
            padding: 10px 15px; 
            margin: 10px 0; 
            display: block; 
            text-decoration: none;
            background-color: #007bff;
            color: white;
            border-radius: 5px;
            text-align: center;
        }
        .admin { background-color: #dc3545; }
    </style>
</head>
<body>
    <h1>Acceso Garantizado</h1>
    <p>Esta página permite acceder directamente a la aplicación sin depender del sistema normal de login.</p>
    
    <h2>Acceso como usuario normal</h2>
    <p>Credenciales: acceso@example.com / acceso123</p>
    
    <h2>Acceso como administrador</h2>
    <p>Credenciales: admin@example.com / admin123</p>
    
    <script>
        // Funciones para establecer cookies de sesión manualmente
        function setUserSession() {
            document.cookie = "user_id=ACCESO_USER_ID; path=/";
            document.cookie = "username=acceso_user; path=/";
            document.cookie = "email=acceso@example.com; path=/";
            document.cookie = "role=user; path=/";
            document.cookie = "logged_in=true; path=/";
            window.location.href = "/";
        }
        
        function setAdminSession() {
            document.cookie = "user_id=680bc20aa170ac7fe8e58bec; path=/";
            document.cookie = "username=administrator; path=/";
            document.cookie = "email=admin@example.com; path=/";
            document.cookie = "role=admin; path=/";
            document.cookie = "logged_in=true; path=/";
            window.location.href = "/admin/";
        }
    </script>
    
    <a href="javascript:setUserSession()" class="btn">ACCEDER COMO USUARIO</a>
    <a href="javascript:setAdminSession()" class="btn admin">ACCEDER COMO ADMINISTRADOR</a>
    
    <hr>
    <p><small>Esta página es solo para propósitos de desarrollo y depuración.</small></p>
</body>
</html>"""

    # Insertar el ID del usuario de acceso
    user_id = crear_usuario_acceso()
    html_content = html_content.replace("ACCESO_USER_ID", user_id)

    # Guardar la página
    with open(acceso_path, 'w') as f:
        f.write(html_content)

    print(f"✅ Página de acceso rápido creada en: {acceso_path}")
    print(f"Puedes acceder a ella directamente desde: file://{acceso_path}")
    return acceso_path

def main():
    print("=" * 50)
    print("🚀 SCRIPT DE REPARACIÓN DE ACCESO A DASHBOARD")
    print("=" * 50)

    # Crear usuario garantizado
    user_id = crear_usuario_acceso()

    # Modificar permisos (opcional basado en argumentos)
    if len(sys.argv) > 1 and sys.argv[1] == '--bypass-auth':
        modificar_permisos()

    # Crear página de acceso rápido
    acceso_path = crear_pagina_acceso_rapido()

    # Instrucciones
    print("\n" + "=" * 50)
    print("✅ ACCIONES COMPLETADAS")
    print("=" * 50)
    print("\nPara acceder como usuario normal:")
    print("1. Credenciales: acceso@example.com / acceso123")
    print("2. URL de la página de acceso rápido:")
    print(f"   file://{acceso_path}")
    print("\nPresiona cualquier tecla para salir...")
    input()

if __name__ == "__main__":
    main()
