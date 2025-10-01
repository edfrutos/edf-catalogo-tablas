#!/usr/bin/env python3
# Script para solucionar problemas de conexión a MongoDB Atlas
# Creado: 17/05/2025

import datetime
import os
import re
import shutil
import socket
import subprocess
import sys
import time

import certifi
import dns.resolver
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


def check_dns_resolution(hostname):
    """Verifica la resolución DNS de un hostname"""
    print(f"Verificando resolución DNS para: {hostname}")
    try:
        # Intentar resolver el hostname
        ip_address = socket.gethostbyname(hostname)
        print(f"  Resolución exitosa: {hostname} -> {ip_address}")
        return True, ip_address
    except socket.gaierror as e:
        print(f"  Error de resolución DNS: {e}")
        return False, None


def check_srv_records(hostname):
    """Verifica los registros SRV para MongoDB Atlas"""
    print(f"Verificando registros SRV para: _mongodb._tcp.{hostname}")
    try:
        # Intentar resolver los registros SRV
        answers = dns.resolver.resolve(f"_mongodb._tcp.{hostname}", "SRV")
        print(f"  Registros SRV encontrados: {len(answers)}")

        servers = []
        # Convertir RRset a lista para iteración
        for rdata in list(answers):
            server = str(rdata.target).rstrip(".")
            print(
                f"  {server} (prioridad: {rdata.priority}, peso: {rdata.weight}, puerto: {rdata.port})"
            )
            servers.append(f"{server}:{rdata.port}")

        return True, servers
    except Exception as e:
        print(f"  Error al resolver registros SRV: {e}")
        return False, []


def check_network_connectivity(host, port):
    """Verifica la conectividad de red a un host y puerto específicos"""
    print(f"Verificando conectividad de red a {host}:{port}")

    try:
        # Crear un socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)

        # Intentar conectar
        result = sock.connect_ex((host, port))

        if result == 0:
            print(f"  Conexión exitosa a {host}:{port}")
            sock.close()
            return True
        else:
            print(f"  No se pudo conectar a {host}:{port} (código de error: {result})")
            sock.close()
            return False
    except socket.gaierror as e:
        print(f"  Error de resolución de dirección: {e}")
        return False
    except OSError as e:
        print(f"  Error de socket: {e}")
        return False


def create_direct_mongodb_uri(srv_uri, servers):
    """Crea una URI directa a partir de una URI SRV y una lista de servidores"""
    # Extraer usuario, contraseña y base de datos de la URI SRV
    match = re.match(r"mongodb\+srv://([^:]+):([^@]+)@([^/]+)/([^?]+)(\?.*)?", srv_uri)
    if not match:
        return None

    user, password, _, db, params = match.groups()
    if params is None:
        params = ""

    # Crear URI directa con todos los servidores
    server_list = ",".join(servers)
    direct_uri = f"mongodb://{user}:{password}@{server_list}/{db}{params}"

    return direct_uri


def update_env_file(
    env_path, new_uri=None, use_direct_uri=False, use_local_mongodb=False
):
    """Actualiza el archivo .env con la nueva URI de MongoDB"""
    if not os.path.exists(env_path):
        print(f"Error: No se encontró el archivo {env_path}")
        return False

    # Hacer copia de seguridad
    backup_file(env_path)

    # Leer el contenido actual
    with open(env_path) as f:
        content = f.read()

    # Extraer la URI actual
    mongo_uri_match = re.search(r"^MONGO_URI\s*=\s*(.*)$", content, re.MULTILINE)
    current_uri = mongo_uri_match.group(1).strip() if mongo_uri_match else None

    # Determinar la nueva URI
    if use_local_mongodb:
        new_uri = "mongodb://localhost:27017/app_catalogojoyero_nueva"
    elif use_direct_uri and current_uri and current_uri.startswith("mongodb+srv://"):
        # Extraer el hostname de la URI SRV
        hostname_match = re.search(r"mongodb\+srv://[^@]+@([^/]+)", current_uri)
        if hostname_match:
            hostname = hostname_match.group(1)
            # Verificar registros SRV
            srv_success, servers = check_srv_records(hostname)
            if srv_success and servers:
                # Crear URI directa
                direct_uri = create_direct_mongodb_uri(current_uri, servers)
                if direct_uri:
                    new_uri = direct_uri

    # Si se proporciona una nueva URI, actualizar el archivo
    if new_uri:
        # Reemplazar la URI existente o añadir una nueva
        if mongo_uri_match:
            content = re.sub(
                r"^MONGO_URI\s*=.*$",
                f"MONGO_URI={new_uri}",
                content,
                flags=re.MULTILINE,
            )
        else:
            content += f"\nMONGO_URI={new_uri}\n"

        # Guardar los cambios
        with open(env_path, "w") as f:
            f.write(content)

        print(f"Archivo {env_path} actualizado con la nueva URI: {new_uri[:20]}...")
        return True

    return False


def update_app_py(app_path, add_retry_logic=True):
    """Modifica app.py para añadir lógica de reintento para MongoDB"""
    if not os.path.exists(app_path):
        print(f"Error: No se encontró el archivo {app_path}")
        return False

    # Hacer copia de seguridad
    backup_file(app_path)

    # Leer el contenido actual
    with open(app_path) as f:
        content = f.read()

    if add_retry_logic:
        # Añadir importaciones necesarias si no existen
        if "import time" not in content:
            import_section = re.search(r"import.*?\n\n", content, re.DOTALL)
            if import_section:
                content = content.replace(
                    import_section.group(0),
                    import_section.group(0) + "import time\nimport certifi\n",
                )

        # Modificar la inicialización de PyMongo para añadir lógica de reintento
        if "mongo = PyMongo(app)" in content:
            content = content.replace(
                "mongo = PyMongo(app)",
                """# Intentar conectar a MongoDB con reintentos
max_retries = 3
retry_delay = 2
for retry in range(max_retries):
    try:
        mongo = PyMongo(app, tlsCAFile=certifi.where())
        print(f"Conexión a MongoDB establecida correctamente en el intento {retry + 1}")
        break
    except Exception as e:
        print(f"Error al conectar a MongoDB (intento {retry + 1}/{max_retries}): {e}")
        if retry < max_retries - 1:
            print(f"Reintentando en {retry_delay} segundos...")
            time.sleep(retry_delay)
            retry_delay *= 2  # Aumentar el tiempo de espera exponencialmente
        else:
            print("Todos los intentos de conexión a MongoDB fallaron. Utilizando datos simulados.")
            # Importar datos simulados si están disponibles
            try:
                from tools.mock_data import get_mock_mongo
                mongo = get_mock_mongo()
                print("Usando datos simulados en lugar de MongoDB")
            except ImportError:
                print("No se encontró el módulo de datos simulados. Algunas funciones estarán deshabilitadas.")
                mongo = None""",
            )

        # Modificar las asignaciones de colecciones para manejar el caso cuando
        # mongo es None
        content = content.replace(
            "app.spreadsheets_collection = mongo.db.spreadsheets",
            "app.spreadsheets_collection = mongo.db.spreadsheets if hasattr(mongo, 'db') else None",
        )

        content = content.replace(
            "app.catalogs_collection = mongo.db.catalogs",
            "app.catalogs_collection = mongo.db.catalogs if hasattr(mongo, 'db') else None",
        )

        content = content.replace(
            "app.users_collection = mongo.db.users",
            "app.users_collection = mongo.db.users if hasattr(mongo, 'db') else None",
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


def main():
    # Cargar variables de entorno
    load_dotenv()

    # Definir rutas
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env_path = os.path.join(root_dir, ".env")
    app_path = os.path.join(root_dir, "app.py")

    print_header("SOLUCIÓN PARA PROBLEMAS DE CONEXIÓN A MONGODB ATLAS")
    print(f"Fecha y hora: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Directorio raíz: {root_dir}")

    # Obtener la URI de MongoDB original
    original_uri = None
    backup_env = os.path.join(root_dir, ".env.bak.20250517200439")
    if os.path.exists(backup_env):
        with open(backup_env) as f:
            content = f.read()
            mongo_uri_match = re.search(
                r"^MONGO_URI\s*=\s*(.*)$", content, re.MULTILINE
            )
            if mongo_uri_match:
                original_uri = mongo_uri_match.group(1).strip()

    if not original_uri:
        print(
            "No se pudo encontrar la URI de MongoDB original. Utilizando la URI predeterminada."
        )
        original_uri = "mongodb+srv://edfrutos:rYjwUC6pUNrLtbaI@cluster0.pmokh.mongodb.net/app_catalogojoyero_nueva?retryWrites=true&w=majority"

    print(f"URI de MongoDB original: {original_uri[:20]}...")

    # Extraer el hostname de la URI
    hostname_match = re.search(r"mongodb\+srv://[^@]+@([^/]+)", original_uri)
    if not hostname_match:
        print("Error: No se pudo extraer el hostname de la URI de MongoDB")
        sys.exit(1)

    hostname = hostname_match.group(1)
    print(f"Hostname extraído: {hostname}")

    # Verificar resolución DNS
    print_header("VERIFICACIÓN DE DNS")
    dns_success, ip_address = check_dns_resolution(hostname)

    # Verificar registros SRV
    srv_success, servers = check_srv_records(hostname)

    # Verificar conectividad de red
    print_header("VERIFICACIÓN DE CONECTIVIDAD DE RED")
    # Probar conectividad a servicios comunes
    dns_google = check_network_connectivity("8.8.8.8", 53)  # DNS de Google
    dns_cloudflare = check_network_connectivity("1.1.1.1", 53)  # DNS de Cloudflare
    mongodb_website = check_network_connectivity(
        "mongodb.com", 443
    )  # Sitio web de MongoDB

    # Probar conectividad a los servidores de MongoDB
    mongodb_servers_reachable = []
    if srv_success and servers:
        for server in servers:
            host, port = server.split(":")
            if check_network_connectivity(host, int(port)):
                mongodb_servers_reachable.append(server)

    # Determinar la mejor solución
    print_header("DETERMINANDO LA MEJOR SOLUCIÓN")

    if dns_success and srv_success and mongodb_servers_reachable:
        print(
            "Los servidores de MongoDB Atlas son accesibles. Intentando crear una URI directa."
        )
        direct_uri = create_direct_mongodb_uri(original_uri, mongodb_servers_reachable)
        if direct_uri:
            print(f"URI directa creada: {direct_uri[:20]}...")
            update_env_file(env_path, new_uri=direct_uri)
        else:
            print(
                "No se pudo crear una URI directa. Utilizando la URI original con lógica de reintento."
            )
            update_env_file(env_path, new_uri=original_uri)
    elif dns_success and srv_success:
        print(
            "Los registros SRV se resuelven pero no se puede conectar a los servidores. Utilizando la URI original con lógica de reintento."
        )
        update_env_file(env_path, new_uri=original_uri)
    else:
        print(
            "No se pueden resolver los registros SRV. Utilizando MongoDB local temporalmente."
        )
        update_env_file(env_path, use_local_mongodb=True)

    # Añadir lógica de reintento a app.py
    print_header("ACTUALIZANDO APP.PY CON LÓGICA DE REINTENTO")
    update_app_py(app_path)

    # Reiniciar Gunicorn
    print_header("REINICIANDO SERVIDOR")
    restart_gunicorn()

    print_header("SOLUCIÓN COMPLETADA")
    print(
        "Se ha implementado una solución para los problemas de conexión a MongoDB Atlas."
    )
    print(
        "La aplicación ahora intentará conectarse a MongoDB Atlas con lógica de reintento."
    )
    print(
        "Si la conexión falla, utilizará datos simulados para mantener la aplicación funcionando."
    )
    print("\nPara revertir a la configuración original, ejecute:")
    print(f"python3 {os.path.abspath(__file__)} --revert")


if __name__ == "__main__":
    # Verificar si se debe revertir los cambios
    if len(sys.argv) > 1 and sys.argv[1] == "--revert":
        print_header("REVIRTIENDO CAMBIOS")

        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        env_path = os.path.join(root_dir, ".env")
        app_path = os.path.join(root_dir, "app.py")

        # Restaurar archivos desde backups
        backup_files = [f for f in os.listdir(root_dir) if f.startswith(".env.bak")]
        if backup_files:
            latest_backup = sorted(backup_files)[-1]
            backup_path = os.path.join(root_dir, latest_backup)
            shutil.copy2(backup_path, env_path)
            print(f"Archivo .env restaurado desde {latest_backup}")

        backup_files = [f for f in os.listdir(root_dir) if f.startswith("app.py.bak")]
        if backup_files:
            latest_backup = sorted(backup_files)[-1]
            backup_path = os.path.join(root_dir, latest_backup)
            shutil.copy2(backup_path, app_path)
            print(f"Archivo app.py restaurado desde {latest_backup}")

        # Reiniciar Gunicorn
        restart_gunicorn()

        print_header("CAMBIOS REVERTIDOS")
        print("Se han revertido los cambios a la configuración original.")
    else:
        main()
