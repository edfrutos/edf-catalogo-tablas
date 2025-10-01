#!/usr/bin/env python3
"""
Script para arreglar problemas de carga de variables de entorno en la aplicación macOS
Autor: EDF Developer - 2025
"""

import os
import shutil  # pyright: ignore[reportUnusedImport]
import sys
from pathlib import Path  # pyright: ignore[reportUnusedImport]


def check_env_loading():
    """Verifica si las variables de entorno se están cargando correctamente"""
    print("🔍 VERIFICANDO CARGA DE VARIABLES DE ENTORNO")
    print("=" * 50)

    # Verificar si estamos en una aplicación empaquetada
    if getattr(sys, "frozen", False):
        print("✅ Aplicación empaquetada detectada")
        app_path = os.path.dirname(sys.executable)
    else:
        print("ℹ️  Ejecutando en modo desarrollo")
        app_path = os.getcwd()

    # Verificar archivo .env
    env_path = os.path.join(app_path, ".env")
    if os.path.exists(env_path):
        print(f"✅ Archivo .env encontrado: {env_path}")

        # Leer contenido del archivo .env
        try:
            with open(env_path, "r") as f:  # noqa: UP015
                content = f.read()

            # Buscar MONGO_URI
            if "MONGO_URI=" in content:
                print("✅ MONGO_URI encontrada en .env")
                # Extraer la URI (sin mostrar credenciales)
                lines = content.split("\n")
                for line in lines:
                    if line.startswith("MONGO_URI="):
                        uri_parts = line.split("@")
                        if len(uri_parts) > 1:
                            safe_uri = f"mongodb+srv://***:***@{uri_parts[1]}"
                            print(f"📡 URI: {safe_uri}")
                        break
            else:
                print("❌ MONGO_URI no encontrada en .env")
                return False

        except Exception as e:
            print(f"❌ Error leyendo .env: {e}")
            return False
    else:
        print("❌ Archivo .env no encontrado")
        return False

    # Verificar si la variable está en el entorno
    mongo_uri_env = os.environ.get("MONGO_URI")
    if mongo_uri_env:
        print("✅ MONGO_URI en variables de entorno")
        return True
    else:
        print("❌ MONGO_URI no está en variables de entorno")
        return False


def fix_env_loading():
    """Arregla la carga de variables de entorno"""
    print("\n🔧 ARREGLANDO CARGA DE VARIABLES DE ENTORNO")
    print("=" * 50)

    # Determinar la ruta de la aplicación
    if getattr(sys, "frozen", False):
        app_path = os.path.dirname(sys.executable)
    else:
        app_path = os.getcwd()

    env_path = os.path.join(app_path, ".env")

    # Crear un script de inicialización que cargue las variables
    init_script = f"""#!/bin/bash
# Script de inicialización para cargar variables de entorno
# Generado automáticamente por fix_mongodb_env_macos.py

# Cargar variables de entorno desde .env
if [ -f "{env_path}" ]; then
    export $(grep -v '^#' {env_path} | xargs)
    echo "✅ Variables de entorno cargadas desde {env_path}"
else
    echo "❌ Archivo .env no encontrado en {env_path}"
    exit 1
fi

# Verificar que MONGO_URI esté disponible
if [ -z "$MONGO_URI" ]; then
    echo "❌ MONGO_URI no está configurada"
    exit 1
else
    echo "✅ MONGO_URI configurada correctamente"
fi

# Ejecutar la aplicación
echo "🚀 Iniciando aplicación..."
exec "$@"
"""

    # Guardar el script de inicialización
    init_script_path = os.path.join(app_path, "init_app.sh")
    try:
        with open(init_script_path, "w") as f:
            f.write(init_script)

        # Dar permisos de ejecución
        os.chmod(init_script_path, 0o755)
        print(f"✅ Script de inicialización creado: {init_script_path}")

    except Exception as e:
        print(f"❌ Error creando script de inicialización: {e}")
        return False

    # Crear un script Python que cargue las variables
    python_init_script = f"""#!/usr/bin/env python3
# Script Python para cargar variables de entorno
import os
import sys
from pathlib import Path

def load_env_variables():
    \"\"\"Carga variables de entorno desde .env\"\"\"
    env_path = Path("{env_path}")

    if not env_path.exists():
        print(f"❌ Archivo .env no encontrado: {{env_path}}")
        return False

    try:
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value

        print("✅ Variables de entorno cargadas desde .env")
        return True

    except Exception as e:
        print(f"❌ Error cargando variables de entorno: {{e}}")
        return False

if __name__ == "__main__":
    if load_env_variables():
        # Verificar que MONGO_URI esté disponible
        if os.environ.get('MONGO_URI'):
            print("✅ MONGO_URI configurada correctamente")
            sys.exit(0)
        else:
            print("❌ MONGO_URI no está configurada")
            sys.exit(1)
    else:
        sys.exit(1)
"""

    # Guardar el script Python
    python_init_path = os.path.join(app_path, "load_env.py")
    try:
        with open(python_init_path, "w") as f:
            f.write(python_init_script)  # pyright: ignore[reportUnusedCallResult]

        os.chmod(python_init_path, 0o755)
        print(f"✅ Script Python de carga creado: {python_init_path}")

    except Exception as e:
        print(f"❌ Error creando script Python: {e}")
        return False

    return True


def create_launcher_script():
    """Crea un script launcher que cargue las variables antes de ejecutar la app"""
    print("\n🚀 CREANDO SCRIPT LAUNCHER")
    print("=" * 50)

    # Determinar la ruta de la aplicación
    if getattr(sys, "frozen", False):
        app_path = os.path.dirname(sys.executable)
        app_executable = sys.executable
    else:
        app_path = os.getcwd()
        app_executable = "python3 app.py"  # O el comando apropiado

    launcher_script = f"""#!/bin/bash
# Launcher para la aplicación con variables de entorno
# Generado automáticamente por fix_mongodb_env_macos.py

# Cambiar al directorio de la aplicación
cd "{app_path}"

# Cargar variables de entorno
if [ -f ".env" ]; then
    export $(grep -v '^#' .env | xargs)
    echo "✅ Variables de entorno cargadas"
else
    echo "❌ Archivo .env no encontrado"
    exit 1
fi

# Verificar MONGO_URI
if [ -z "$MONGO_URI" ]; then
    echo "❌ MONGO_URI no está configurada"
    exit 1
fi

echo "🚀 Iniciando aplicación..."
echo "📡 MongoDB URI: ${{MONGO_URI:0:30}}... (ocultando credenciales)"

# Ejecutar la aplicación
{app_executable}
"""

    # Guardar el launcher
    launcher_path = os.path.join(app_path, "launch_app.sh")
    try:
        with open(launcher_path, "w") as f:
            f.write(launcher_script)

        os.chmod(launcher_path, 0o755)
        print(f"✅ Launcher creado: {launcher_path}")

    except Exception as e:
        print(f"❌ Error creando launcher: {e}")
        return False

    return True


def test_env_loading():
    """Prueba la carga de variables de entorno"""
    print("\n🧪 PROBANDO CARGA DE VARIABLES")
    print("=" * 50)

    try:
        from dotenv import load_dotenv

        # Cargar variables desde .env
        load_dotenv()

        # Verificar MONGO_URI
        mongo_uri = os.environ.get("MONGO_URI")
        if mongo_uri:
            print("✅ MONGO_URI cargada correctamente")

            # Probar conexión a MongoDB
            try:
                import certifi
                import pymongo

                config = {
                    "serverSelectionTimeoutMS": 5000,
                    "connectTimeoutMS": 5000,
                }

                if mongo_uri.startswith("mongodb+srv://"):
                    config["tlsCAFile"] = certifi.where()

                client = pymongo.MongoClient(mongo_uri, **config)
                client.admin.command("ping")
                client.close()

                print("✅ Conexión a MongoDB exitosa")
                return True

            except Exception as e:
                print(f"❌ Error de conexión a MongoDB: {e}")
                return False
        else:
            print("❌ MONGO_URI no está disponible")
            return False

    except Exception as e:
        print(f"❌ Error probando carga de variables: {e}")
        return False


def main():
    """Función principal"""
    print("🔧 ARREGLANDO CARGA DE VARIABLES DE ENTORNO")
    print("=" * 60)

    try:
        # Verificar estado actual
        env_ok = check_env_loading()

        if not env_ok:
            print("\n🔧 Aplicando soluciones...")

            # Arreglar carga de variables
            if not fix_env_loading():
                print("❌ No se pudo arreglar la carga de variables")
                return

            # Crear launcher
            if not create_launcher_script():
                print("❌ No se pudo crear el launcher")
                return

            # Probar la solución
            if not test_env_loading():
                print("❌ La solución no funciona correctamente")
                return

            print("\n🎉 ¡SOLUCIÓN APLICADA!")
            print("✅ Las variables de entorno ahora se cargan correctamente")
            print("\n💡 Para usar la aplicación:")
            print("   1. Ejecuta: ./launch_app.sh")
            print("   2. O ejecuta: python3 load_env.py && python3 app.py")

        else:
            print("\n✅ Las variables de entorno ya están funcionando correctamente")

    except Exception as e:
        print(f"\n❌ Error durante la solución: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
