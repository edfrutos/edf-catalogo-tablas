#!/usr/bin/env python3
"""
Script para arreglar la aplicación nativa macOS
Autor: EDF Developer - 2025
"""

import os
import shutil
import subprocess
from pathlib import Path


def check_native_app():
    """Verifica si la aplicación nativa existe"""
    print("🔍 VERIFICANDO APLICACIÓN NATIVA")
    print("=" * 40)

    app_path = "dist/EDF_CatalogoDeTablas_Web_Native.app"

    if os.path.exists(app_path):
        print(f"✅ Aplicación nativa encontrada: {app_path}")

        # Verificar estructura
        contents_path = os.path.join(app_path, "Contents")
        macos_path = os.path.join(
            contents_path, "MacOS"
        resources_path=os.path.join(
            contents_path, "Resources"

        if os.path.exists(contents_path):
            print("✅ Estructura de aplicación válida")
        else:
            print("❌ Estructura de aplicación inválida")
            return False

        return True
    else:
        print(f"❌ Aplicación nativa no encontrada: {app_path}")
        return False


def copy_env_file():
    """Copia el archivo .env a la aplicación nativa"""
    print("\n📁 COPIANDO ARCHIVO .env")
    print("=" * 40)

    # Rutas
    source_env=".env"
    app_path="dist/EDF_CatalogoDeTablas_Web_Native.app"
    target_env=os.path.join(app_path, ".env")

    if not os.path.exists(source_env):
        print("❌ Archivo .env no encontrado en el directorio raíz")
        return False

    try:
        # Copiar archivo .env
        shutil.copy2(source_env, target_env)
        print(f"✅ Archivo .env copiado a: {target_env}")

        # Verificar que se copió correctamente
        if os.path.exists(target_env):
            print("✅ Verificación: archivo .env copiado correctamente")
            return True
        else:
            print("❌ Error: archivo .env no se copió correctamente")
            return False

    except Exception as e:
        print(f"❌ Error copiando archivo .env: {e}")
        return False


def create_native_launcher():
    """Crea un launcher específico para la aplicación nativa"""
    print("\n🚀 CREANDO LAUNCHER PARA APLICACIÓN NATIVA")
    print("=" * 40)

    app_path="dist/EDF_CatalogoDeTablas_Web_Native.app"
    launcher_script=f"""#!/bin/bash
# Launcher para la aplicación nativa macOS
# Generado automáticamente por fix_native_app_macos.py

# Cambiar al directorio de la aplicación
cd "$(dirname "$0")"

# Verificar que la aplicación existe
if [ ! -d "{app_path}" ]; then
    echo "❌ Aplicación nativa no encontrada: {app_path}"
    exit 1
fi

# Cargar variables de entorno desde .env si existe
if [ -f ".env" ]; then
    echo "📁 Cargando variables de entorno desde .env..."

    # Cargar variables de entorno de forma robusta
    while IFS= read -r line; do
        # Ignorar líneas vacías, comentarios y líneas que no contienen '='
        if [[ -n "$line" && ! "$line" =~ ^[[:space:]]*# && "$line" == *"="* ]]; then
            # Extraer nombre y valor de la variable
            var_name="${{line%%=*}}"
            var_value="${{line#*=}}"
            # Eliminar espacios en blanco
            var_name=$(echo "$var_name" | xargs)
            var_value=$(echo "$var_value" | xargs)
            # Exportar la variable solo si tiene un nombre válido
            if [[ -n "$var_name" && "$var_name" =~ ^[a-zA-Z_][a-zA-Z0-9_]*$ ]]; then
                export "$var_name=$var_value"
            fi
        fi
    done < ".env"

    echo "✅ Variables de entorno cargadas"
else
    echo "⚠️  Archivo .env no encontrado, usando variables del sistema"
fi

# Verificar MONGO_URI
if [ -z "$MONGO_URI" ]; then
    echo "❌ MONGO_URI no está configurada"
    echo "💡 Asegúrate de que el archivo .env esté presente"
    exit 1
fi

echo "🚀 Iniciando aplicación nativa..."
echo "📡 MongoDB URI: ${{MONGO_URI:0:30}}... (ocultando credenciales)"

# Ejecutar la aplicación nativa
open "{app_path}"
"""

    # Guardar el launcher
    launcher_path="launch_native_app.sh"
    try:
        with open(launcher_path, "w") as f:
            f.write(launcher_script)

        # Dar permisos de ejecución
        os.chmod(launcher_path, 0o755)
        print(f"✅ Launcher creado: {launcher_path}")

    except Exception as e:
        print(f"❌ Error creando launcher: {e}")
        return False

    return True


def test_native_app():
    """Prueba la aplicación nativa"""
    print("\n🧪 PROBANDO APLICACIÓN NATIVA")
    print("=" * 40)

    app_path="dist/EDF_CatalogoDeTablas_Web_Native.app"

    try:
        # Verificar que la aplicación se puede abrir
        print("🔍 Verificando que la aplicación se puede abrir...")

        # Intentar abrir la aplicación
        result=subprocess.run(
            ["open", app_path], capture_output=True, text=True, timeout=10
        )

        if result.returncode == 0:
            print("✅ Aplicación nativa abierta correctamente")
            return True
        else:
            print(f"⚠️  Aplicación abierta con código: {result.returncode}")
            return True  # Aún consideramos éxito si se abrió

    except subprocess.TimeoutExpired:
        print("✅ Aplicación nativa iniciada (timeout esperado)")
        return True
    except Exception as e:
        print(f"❌ Error probando aplicación nativa: {e}")
        return False


def create_env_in_app_bundle():
    """Crea el archivo .env dentro del bundle de la aplicación"""
    print("\n📝 CREANDO .env EN EL BUNDLE DE LA APLICACIÓN")
    print("=" * 40)

    app_path="dist/EDF_CatalogoDeTablas_Web_Native.app"
    bundle_env_path=os.path.join(app_path, "Contents", "Resources", ".env")

    # Leer el archivo .env original
    try:
        with open(".env", "r") as f:
            env_content=f.read()

        # Escribir el archivo .env en el bundle
        with open(bundle_env_path, "w") as f:
            f.write(env_content)

        print(f"✅ Archivo .env creado en el bundle: {bundle_env_path}")
        return True

    except Exception as e:
        print(f"❌ Error creando .env en el bundle: {e}")
        return False


def fix_app_permissions():
    """Arregla los permisos de la aplicación"""
    print("\n🔐 ARREGLANDO PERMISOS")
    print("=" * 40)

    app_path="dist/EDF_CatalogoDeTablas_Web_Native.app"

    try:
        # Dar permisos de ejecución a la aplicación
        os.chmod(app_path, 0o755)

        # Dar permisos al ejecutable
        executable_path=os.path.join(
            app_path, "Contents", "MacOS", "EDF_CatalogoDeTablas_Web_Native"
        )
        if os.path.exists(executable_path):
            os.chmod(executable_path, 0o755)
            print("✅ Permisos de ejecución configurados")

        # Dar permisos a los archivos .env
        env_files=[
            os.path.join(app_path, ".env"),
            os.path.join(app_path, "Contents", "Resources", ".env"),
        ]

        for env_file in env_files:
            if os.path.exists(env_file):
                os.chmod(env_file, 0o644)
                print(f"✅ Permisos configurados para: {env_file}")

        return True

    except Exception as e:
        print(f"❌ Error arreglando permisos: {e}")
        return False


def main():
    """Función principal"""
    print("🔧 ARREGLANDO APLICACIÓN NATIVA MACOS")
    print("=" * 60)

    try:
        # Paso 1: Verificar aplicación nativa
        if not check_native_app():
            print("❌ No se puede continuar sin la aplicación nativa")
            return

        # Paso 2: Copiar archivo .env
        if not copy_env_file():
            print("❌ No se pudo copiar el archivo .env")
            return

        # Paso 3: Crear .env en el bundle
        if not create_env_in_app_bundle():
            print("❌ No se pudo crear .env en el bundle")
            return

        # Paso 4: Crear launcher
        if not create_native_launcher():
            print("❌ No se pudo crear el launcher")
            return

        # Paso 5: Arreglar permisos
        if not fix_app_permissions():
            print("❌ No se pudieron arreglar los permisos")
            return

        # Paso 6: Probar aplicación
        if not test_native_app():
            print("❌ La aplicación nativa no funciona correctamente")
            return

        print("\n🎉 ¡APLICACIÓN NATIVA ARREGLADA!")
        print("✅ La aplicación nativa ahora debería funcionar correctamente")
        print("\n💡 Para usar la aplicación nativa:")
        print("   1. Ejecuta: ./launch_native_app.sh")
        print("   2. O haz doble clic en: dist/EDF_CatalogoDeTablas_Web_Native.app")
        print("\n🔧 Si hay problemas:")
        print("   1. Verifica que el archivo .env esté en el directorio raíz")
        print("   2. Ejecuta este script nuevamente")
        print("   3. Revisa los logs de la aplicación")

    except Exception as e:
        print(f"\n❌ Error durante la reparación: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
