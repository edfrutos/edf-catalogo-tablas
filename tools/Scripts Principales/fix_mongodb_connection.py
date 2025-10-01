#!/usr/bin/env python3
# Script para solucionar temporalmente problemas de conexión a MongoDB
# Creado: 17/05/2025

import datetime
import os
import re
import shutil
import subprocess
import sys

from dotenv import load_dotenv


def print_header(message):
    print("\n" + "=" * 80)
    print(f" {message} ".center(80, "="))
    print("=" * 80)


def backup_file(file_path):
    """Crea una copia de seguridad del archivo"""
    if os.path.exists(file_path):
        # Crear directorio de backup si no existe
        backup_dir = os.path.join(
            os.path.dirname(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            ),
            "backups",
            "automated",
        )
        os.makedirs(backup_dir, exist_ok=True)

        # Crear nombre de archivo de backup con timestamp
        filename = os.path.basename(file_path)
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        backup_filename = f"{filename}.bak.{timestamp}"
        backup_path = os.path.join(backup_dir, backup_filename)

        # Copiar el archivo original al backup
        shutil.copy2(file_path, backup_path)
        print(f"Copia de seguridad creada: {backup_path}")
        return True
    return False


def update_env_file(env_path, use_local_mongodb=True):
    """Actualiza el archivo .env para usar MongoDB local o remoto"""
    if not os.path.exists(env_path):
        print(f"Error: No se encontró el archivo {env_path}")
        return False

    # Hacer copia de seguridad
    backup_file(env_path)

    # Leer el contenido actual
    with open(env_path) as f:
        content = f.read()

    # Modificar la URI de MongoDB
    if use_local_mongodb:
        # Usar MongoDB local
        if re.search(r"^MONGO_URI\s*=", content, re.MULTILINE):
            # Reemplazar la URI existente
            content = re.sub(
                r"^MONGO_URI\s*=.*$",
                "MONGO_URI=mongodb://localhost:27017/app_catalogojoyero_nueva",
                content,
                flags=re.MULTILINE,
            )
        else:
            # Añadir la URI si no existe
            content += (
                "\nMONGO_URI=mongodb://localhost:27017/app_catalogojoyero_nueva\n"
            )
    else:
        # Restaurar MongoDB Atlas (si se encuentra en el backup)
        backup_files = [
            f
            for f in os.listdir(os.path.dirname(env_path))
            if f.startswith(os.path.basename(env_path) + ".bak")
        ]
        if backup_files:
            # Usar el backup más reciente
            latest_backup = sorted(backup_files)[-1]
            backup_path = os.path.join(os.path.dirname(env_path), latest_backup)

            with open(backup_path) as f:
                backup_content = f.read()

            # Extraer la URI de MongoDB del backup
            mongo_uri_match = re.search(
                r"^MONGO_URI\s*=\s*(.*)$", backup_content, re.MULTILINE
            )
            if mongo_uri_match:
                mongo_uri = mongo_uri_match.group(1).strip()

                # Reemplazar la URI en el archivo actual
                content = re.sub(
                    r"^MONGO_URI\s*=.*$",
                    f"MONGO_URI={mongo_uri}",
                    content,
                    flags=re.MULTILINE,
                )

    # Guardar los cambios
    with open(env_path, "w") as f:
        f.write(content)

    print(f"Archivo {env_path} actualizado correctamente")
    return True


def update_app_py(app_path, disable_mongodb=True):
    """Modifica app.py para hacer opcional la conexión a MongoDB"""
    if not os.path.exists(app_path):
        print(f"Error: No se encontró el archivo {app_path}")
        return False

    # Hacer copia de seguridad
    backup_file(app_path)

    # Leer el contenido actual
    with open(app_path) as f:
        content = f.read()

    if disable_mongodb:
        # Modificar la validación de MONGO_URI para hacerla opcional
        if (
            'raise ValueError("MONGO_URI no está configurada en el archivo .env")'
            in content
        ):
            content = content.replace(
                'raise ValueError("MONGO_URI no está configurada en el archivo .env")',
                'print("Advertencia: MONGO_URI no está configurada, algunas funciones estarán deshabilitadas")\n        MONGO_URI = "mongodb://localhost:27017/app_catalogojoyero_nueva"',
            )

        # Hacer que la conexión a MongoDB sea opcional
        content = content.replace(
            "mongo = PyMongo(app)",
            'try:\n    mongo = PyMongo(app)\nexcept Exception as e:\n    print(f"Error al conectar a MongoDB: {e}")\n    mongo = None',
        )

        # Modificar funciones que usan MongoDB para manejar el caso cuando mongo es None
        content = content.replace(
            "app.spreadsheets_collection = mongo.db.spreadsheets",
            "app.spreadsheets_collection = mongo.db.spreadsheets if mongo else None",
        )

        content = content.replace(
            "app.catalogs_collection = mongo.db.catalogs",
            "app.catalogs_collection = mongo.db.catalogs if mongo else None",
        )

        content = content.replace(
            "app.users_collection = mongo.db.users",
            "app.users_collection = mongo.db.users if mongo else None",
        )
    else:
        # Restaurar el comportamiento original desde el backup
        backup_files = [
            f
            for f in os.listdir(os.path.dirname(app_path))
            if f.startswith(os.path.basename(app_path) + ".bak")
        ]
        if backup_files:
            # Usar el backup más reciente
            latest_backup = sorted(backup_files)[-1]
            backup_path = os.path.join(os.path.dirname(app_path), latest_backup)

            with open(backup_path) as f:
                content = f.read()

    # Guardar los cambios
    with open(app_path, "w") as f:
        f.write(content)

    print(f"Archivo {app_path} actualizado correctamente")
    return True


def create_mock_data_script(script_path):
    """Crea un script para generar datos de prueba cuando MongoDB no está disponible"""
    with open(script_path, "w") as f:
        f.write(
            """#!/usr/bin/env python3
# Script para generar datos de prueba cuando MongoDB no está disponible
# Creado: 17/05/2025

import os
import sys
import json
from flask import Flask, g

class MockCollection:
    def __init__(self, name):
        self.name = name
        self.data = []

    def find(self, query=None, **kwargs):
        return self.data

    def find_one(self, query=None, **kwargs):
        if self.data:
            return self.data[0]
        return None

    def insert_one(self, document):
        self.data.append(document)
        return True

    def update_one(self, query, update, **kwargs):
        return True

    def delete_one(self, query):
        return True

    def count_documents(self, query=None):
        return len(self.data)

class MockDB:
    def __init__(self):
        self.spreadsheets = MockCollection("spreadsheets")
        self.catalogs = MockCollection("catalogs")
        self.users = MockCollection("users")

        # Añadir algunos datos de prueba
        self.users.data = [
            {"_id": "admin_id", "username": "admin", "email": "admin@example.com", "role": "admin"},
            {"_id": "user_id", "username": "usuario", "email": "usuario@example.com", "role": "user"}
        ]

        self.spreadsheets.data = [
            {"_id": "table1", "filename": "tabla_ejemplo.xlsx", "name": "Tabla de Ejemplo", "headers": ["ID", "Nombre", "Descripción"]}
        ]

        self.catalogs.data = [
            {"_id": "catalog1", "name": "Catálogo de Prueba", "description": "Un catálogo para pruebas", "rows": []}
        ]

class MockPyMongo:
    def __init__(self, app=None):
        self.db = MockDB()

def patch_app(app):
    \"\"\"Parcha la aplicación Flask para usar datos simulados en lugar de MongoDB\"\"\"
    app.mock_mongo = MockPyMongo()

    # Reemplazar las colecciones con versiones simuladas
    if not hasattr(app, 'spreadsheets_collection') or app.spreadsheets_collection is None:
        app.spreadsheets_collection = app.mock_mongo.db.spreadsheets

    if not hasattr(app, 'catalogs_collection') or app.catalogs_collection is None:
        app.catalogs_collection = app.mock_mongo.db.catalogs

    if not hasattr(app, 'users_collection') or app.users_collection is None:
        app.users_collection = app.mock_mongo.db.users

    print("Aplicación parchada para usar datos simulados en lugar de MongoDB")
    return app

# Función para ser importada desde otros scripts
def get_mock_mongo():
    return MockPyMongo()

if __name__ == "__main__":
    print("Este script debe ser importado desde app.py, no ejecutado directamente")
    sys.exit(1)
"""
        )

    # Hacer el script ejecutable
    os.chmod(script_path, 0o755)
    print(f"Script {script_path} creado correctamente")
    return True


def update_wsgi_file(wsgi_path, use_mock_data=True):
    """Actualiza el archivo wsgi.py para usar datos simulados"""
    if not os.path.exists(wsgi_path):
        print(f"Error: No se encontró el archivo {wsgi_path}")
        return False

    # Hacer copia de seguridad
    backup_file(wsgi_path)

    # Leer el contenido actual
    with open(wsgi_path) as f:
        content = f.read()

    if use_mock_data:
        # Añadir código para usar datos simulados
        if "from app import app" in content and "import mock_data" not in content:
            # Añadir la importación de mock_data antes de la importación de app
            content = content.replace(
                "from app import app",
                'import sys\nimport os\n\n# Añadir el directorio actual al path para importar mock_data\nsys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))\n\ntry:\n    from app import app\n    from tools.mock_data import patch_app\n    \n    # Parchar la aplicación para usar datos simulados si MongoDB no está disponible\n    app = patch_app(app)\nexcept Exception as e:\n    print(f"Error al inicializar la aplicación: {e}")\n    raise',
            )
    else:
        # Restaurar el comportamiento original desde el backup
        backup_files = [
            f
            for f in os.listdir(os.path.dirname(wsgi_path))
            if f.startswith(os.path.basename(wsgi_path) + ".bak")
        ]
        if backup_files:
            # Usar el backup más reciente
            latest_backup = sorted(backup_files)[-1]
            backup_path = os.path.join(os.path.dirname(wsgi_path), latest_backup)

            with open(backup_path) as f:
                content = f.read()

    # Guardar los cambios
    with open(wsgi_path, "w") as f:
        f.write(content)

    print(f"Archivo {wsgi_path} actualizado correctamente")
    return True


def restart_gunicorn():
    """Reinicia el servidor Gunicorn"""
    print("Reiniciando el servidor Gunicorn...")
    try:
        # Intentar usar systemctl
        result = subprocess.run(
            ["systemctl", "restart", "edefrutos2025"], capture_output=True, text=True
        )
        if result.returncode == 0:
            print("Servidor Gunicorn reiniciado correctamente mediante systemctl")
            return True
        else:
            print(f"Error al reiniciar Gunicorn mediante systemctl: {result.stderr}")

            # Intentar usar el script de reinicio
            restart_script = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), "restart_server.sh"
            )
            if os.path.exists(restart_script):
                result = subprocess.run(
                    [restart_script], capture_output=True, text=True
                )
                if result.returncode == 0:
                    print("Servidor Gunicorn reiniciado correctamente mediante script")
                    return True
                else:
                    print(
                        f"Error al reiniciar Gunicorn mediante script: {result.stderr}"
                    )

            return False
    except Exception as e:
        print(f"Error al reiniciar Gunicorn: {str(e)}")
        return False


def fix_log_permissions():
    """Corrige los permisos de los archivos de log"""
    print("Corrigiendo permisos de archivos de log...")
    try:
        log_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs"
        )

        # Verificar que el directorio existe
        if not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
            print(f"Directorio de logs creado: {log_dir}")

        # Cambiar el propietario del directorio de logs
        subprocess.run(["chown", "-R", "www-data:www-data", log_dir], check=True)

        # Establecer permisos adecuados
        subprocess.run(["chmod", "-R", "775", log_dir], check=True)

        # Crear archivos de log si no existen
        log_files = ["gunicorn_error.log", "gunicorn_access.log", "flask_debug.log"]
        for log_file in log_files:
            log_path = os.path.join(log_dir, log_file)
            if not os.path.exists(log_path):
                with open(log_path, "w") as f:
                    f.write("")
                print(f"Archivo de log creado: {log_path}")

            # Asegurarse de que www-data sea el propietario
            subprocess.run(["chown", "www-data:www-data", log_path], check=True)

            # Establecer permisos de escritura
            subprocess.run(["chmod", "664", log_path], check=True)

        print("Permisos de archivos de log corregidos correctamente")
        return True
    except Exception as e:
        print(f"Error al corregir permisos de logs: {str(e)}")
        return False


def main():
    # Definir rutas
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env_path = os.path.join(root_dir, ".env")
    app_path = os.path.join(root_dir, "app.py")
    wsgi_path = os.path.join(root_dir, "wsgi.py")
    mock_data_path = os.path.join(root_dir, "tools", "mock_data.py")

    print_header("SOLUCIÓN TEMPORAL PARA PROBLEMAS DE CONEXIÓN A MONGODB")
    print(f"Fecha y hora: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Directorio raíz: {root_dir}")

    # Corregir permisos de logs
    print_header("CORRIGIENDO PERMISOS DE LOGS")
    fix_log_permissions()

    # Crear script de datos simulados
    print_header("CREANDO SCRIPT DE DATOS SIMULADOS")
    create_mock_data_script(mock_data_path)

    # Actualizar archivo .env
    print_header("ACTUALIZANDO ARCHIVO .ENV")
    update_env_file(env_path)

    # Actualizar app.py
    print_header("ACTUALIZANDO APP.PY")
    update_app_py(app_path)

    # Actualizar wsgi.py
    print_header("ACTUALIZANDO WSGI.PY")
    update_wsgi_file(wsgi_path)

    # Reiniciar Gunicorn
    print_header("REINICIANDO SERVIDOR")
    restart_gunicorn()

    print_header("SOLUCIÓN COMPLETADA")
    print(
        "Se ha implementado una solución temporal para los problemas de conexión a MongoDB."
    )
    print(
        "La aplicación ahora debería funcionar con datos simulados en lugar de conectarse a MongoDB Atlas."
    )
    print("\nPara revertir estos cambios, ejecute este script con la opción --revert:")
    print(f"python3 {os.path.abspath(__file__)} --revert")


if __name__ == "__main__":
    # Verificar si se debe revertir los cambios
    if len(sys.argv) > 1 and sys.argv[1] == "--revert":
        print_header("REVIRTIENDO CAMBIOS")

        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        env_path = os.path.join(root_dir, ".env")
        app_path = os.path.join(root_dir, "app.py")
        wsgi_path = os.path.join(root_dir, "wsgi.py")

        # Revertir cambios
        update_env_file(env_path, use_local_mongodb=False)
        update_app_py(app_path, disable_mongodb=False)
        update_wsgi_file(wsgi_path, use_mock_data=False)

        # Reiniciar Gunicorn
        restart_gunicorn()

        print_header("CAMBIOS REVERTIDOS")
        print(
            "Se han revertido los cambios y la aplicación intentará conectarse a MongoDB Atlas nuevamente."
        )
    else:
        main()
