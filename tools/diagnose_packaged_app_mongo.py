#!/usr/bin/env python3
"""
Script de diagnóstico específico para MongoDB en la aplicación empaquetada
"""

import os
import sys
import tempfile  # pyright: ignore[reportUnusedImport]
from pathlib import Path  # pyright: ignore[reportUnusedImport]


def check_packaged_environment():
    """Verificar el entorno de la aplicación empaquetada"""
    print("🔍 Diagnóstico de MongoDB en aplicación empaquetada")
    print("=" * 60)

    # Verificar si estamos empaquetados
    is_frozen = getattr(sys, "frozen", False)
    print(f"📦 Aplicación empaquetada: {is_frozen}")

    if is_frozen:
        print(
            f"📁 Directorio base: {sys._MEIPASS}"  # pyright: ignore[reportAttributeAccessIssue]
        )
        env_path = os.path.join(
            sys._MEIPASS, ".env"  # pyright: ignore[reportAttributeAccessIssue]
        )
        if os.path.exists(env_path):
            print(f"✅ Archivo .env encontrado: {env_path}")

            # Leer y mostrar la URI de MongoDB
            try:
                with open(env_path, "r") as f:  # noqa: UP015
                    content = f.read()
                    lines = content.split("\n")
                    for line in lines:
                        if line.startswith("MONGO_URI="):
                            mongo_uri = line.split("=", 1)[1]
                            print(f"📡 URI de MongoDB en .env: {mongo_uri[:60]}...")
                            break
            except Exception as e:
                print(f"❌ Error al leer .env: {e}")
        else:
            print(f"❌ Archivo .env no encontrado en: {env_path}")
    else:
        print("⚠️  No estamos en una aplicación empaquetada")

    # Verificar variables de entorno actuales
    print("\n⚙️  Variables de entorno actuales:")
    print("=" * 40)

    mongo_uri = os.environ.get("MONGO_URI")
    if mongo_uri:
        print(f"✅ MONGO_URI: {mongo_uri[:60]}...")
    else:
        print("❌ MONGO_URI: No definida")

    # Intentar cargar .env manualmente
    print("\n🔄 Intentando cargar .env manualmente...")
    print("=" * 40)

    try:
        from dotenv import load_dotenv

        load_dotenv()  # pyright: ignore[reportUnusedCallResult]
        print("✅ load_dotenv() ejecutado")

        # Verificar si se cargó la variable
        mongo_uri_after = os.environ.get("MONGO_URI")
        if mongo_uri_after:
            print(f"✅ MONGO_URI después de load_dotenv: {mongo_uri_after[:60]}...")
        else:
            print("❌ MONGO_URI aún no definida después de load_dotenv")

    except ImportError:
        print("❌ python-dotenv no disponible")
    except Exception as e:
        print(f"❌ Error al cargar .env: {e}")


def test_mongodb_connection():
    """Probar conexión a MongoDB con la configuración actual"""
    print("\n🔍 Probando conexión a MongoDB...")
    print("=" * 40)

    mongo_uri = os.environ.get("MONGO_URI")
    if not mongo_uri:
        print("❌ MONGO_URI no disponible para la prueba")
        return False

    try:
        from pymongo import MongoClient

        print(f"📡 Conectando con URI: {mongo_uri[:60]}...")

        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=10000)
        client.admin.command("ping")  # pyright: ignore[reportUnusedCallResult]

        db = client.get_database()
        print("✅ Conexión exitosa a MongoDB Atlas")
        print(f"📊 Base de datos: {db.name}")

        # Listar colecciones
        collections = db.list_collection_names()
        print(f"📋 Colecciones disponibles: {len(collections)}")

        client.close()
        return True

    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return False


def main():
    """Función principal"""
    print("🔍 DIAGNÓSTICO MONGODB EN APLICACIÓN EMPAQUETADA")
    print("=" * 70)

    try:
        # Verificar entorno
        check_packaged_environment()

        # Probar conexión
        if test_mongodb_connection():
            print("\n🎉 ¡Conexión a MongoDB exitosa!")
            print("✅ La aplicación debería funcionar correctamente")
        else:
            print("\n❌ Problemas con la conexión a MongoDB")
            print("🔧 Revisa la configuración")

        print("\n📋 Resumen:")
        print("   • Verifica que el archivo .env esté incluido en la aplicación")
        print("   • Confirma que load_dotenv() se ejecute correctamente")
        print("   • Asegúrate de que la URI de MongoDB Atlas sea correcta")

    except Exception as e:
        print(f"\n❌ Error durante el diagnóstico: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
