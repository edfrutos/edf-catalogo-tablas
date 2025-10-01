#!/usr/bin/env python3
"""
Script de solución rápida para problemas de MongoDB en la aplicación macOS
Autor: EDF Developer - 2025
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path  # pyright: ignore[reportUnusedImport]


def create_env_file():
    """Crea o actualiza el archivo .env con la configuración de MongoDB"""
    print("🔧 CREANDO ARCHIVO .env")
    print("=" * 40)

    # Determinar la ruta de la aplicación
    if getattr(sys, "frozen", False):
        app_path = os.path.dirname(sys.executable)
    else:
        app_path = os.getcwd()

    env_path = os.path.join(app_path, ".env")

    # Configuración de MongoDB Atlas (reemplaza con tus credenciales)
    mongo_uri = "mongodb+srv://admin:admin123@cluster0.pmokh.mongodb.net/app_catalogojoyero_nueva?retryWrites=true&w=majority"

    env_content = f"""# Configuración de MongoDB
MONGO_URI={mongo_uri}

# Configuración de Flask
SECRET_KEY=edf_secret_key_2025
FLASK_ENV=production

# Configuración de correo
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your_email@gmail.com
MAIL_PASSWORD=your_app_password

# Configuración de AWS S3 (opcional)
AWS_ACCESS_KEY_ID=your_aws_key
AWS_SECRET_ACCESS_KEY=your_aws_secret
AWS_BUCKET_NAME=your_bucket_name
USE_S3=False
"""

    try:
        with open(env_path, "w") as f:
            f.write(env_content)  # pyright: ignore[reportUnusedCallResult]
        print(f"✅ Archivo .env creado en: {env_path}")
        return True
    except Exception as e:
        print(f"❌ Error creando .env: {e}")
        return False


def install_requirements():
    """Instala las dependencias necesarias"""
    print("\n📦 INSTALANDO DEPENDENCIAS")
    print("=" * 40)

    requirements = [
        "pymongo==4.6.1",
        "certifi==2024.2.2",
        "python-dotenv==1.0.0",
        "flask==3.0.0",
        "flask-login==0.6.3",
    ]

    for req in requirements:
        try:
            print(f"📦 Instalando {req}...")
            subprocess.run(
                [sys.executable, "-m", "pip", "install", req],
                check=True,
                capture_output=True,
            )
            print(f"✅ {req} instalado correctamente")
        except subprocess.CalledProcessError as e:
            print(f"❌ Error instalando {req}: {e}")
            return False

    return True


def fix_ssl_certificates():
    """Arregla problemas con certificados SSL"""
    print("\n🔒 ARREGLANDO CERTIFICADOS SSL")
    print("=" * 40)

    try:
        import certifi

        cert_path = certifi.where()

        if os.path.exists(cert_path):
            print(f"✅ Certificados SSL encontrados: {cert_path}")

            # Verificar que el archivo no esté corrupto
            size = os.path.getsize(cert_path)
            if size > 0:
                print("✅ Archivo de certificados válido")
                return True
            else:
                print("⚠️  Archivo de certificados vacío, reinstalando...")
        else:
            print("⚠️  Archivo de certificados no encontrado, reinstalando...")

        # Reinstalar certifi
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "--force-reinstall", "certifi"],
            check=True,
            capture_output=True,
        )
        print("✅ Certifi reinstalado correctamente")
        return True

    except Exception as e:
        print(f"❌ Error arreglando certificados: {e}")
        return False


def test_mongodb_connection():
    """Prueba la conexión a MongoDB"""
    print("\n🔍 PROBANDO CONEXIÓN A MONGODB")
    print("=" * 40)

    try:
        import certifi
        import pymongo
        from dotenv import load_dotenv

        # Cargar variables de entorno
        load_dotenv()

        mongo_uri = os.environ.get("MONGO_URI")
        if not mongo_uri:
            print("❌ MONGO_URI no configurada")
            return False

        print("📡 Conectando a MongoDB...")

        # Configuración optimizada
        config = {
            "serverSelectionTimeoutMS": 10000,
            "connectTimeoutMS": 5000,
            "socketTimeoutMS": 30000,
            "maxPoolSize": 5,
            "minPoolSize": 1,
            "maxIdleTimeMS": 30000,
            "waitQueueTimeoutMS": 5000,
        }

        if mongo_uri.startswith("mongodb+srv://"):
            config["tlsCAFile"] = certifi.where()

        client = pymongo.MongoClient(mongo_uri, **config)
        client.admin.command("ping")

        db = client.get_database()
        print(f"✅ Conexión exitosa a: {db.name}")

        # Verificar colección de usuarios
        if "users" in db.list_collection_names():
            users_count = db.users.count_documents({})
            print(f"👥 Usuarios encontrados: {users_count}")
        else:
            print("⚠️  Colección 'users' no encontrada")

        client.close()
        return True

    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return False


def create_fallback_user():
    """Crea un usuario de fallback para emergencias"""
    print("\n👤 CREANDO USUARIO DE FALLBACK")
    print("=" * 40)

    try:
        import certifi
        import pymongo
        from bson import ObjectId
        from dotenv import load_dotenv

        load_dotenv()

        mongo_uri = os.environ.get("MONGO_URI")
        if not mongo_uri:
            print("❌ MONGO_URI no configurada")
            return False

        config = (
            {"tlsCAFile": certifi.where()}
            if mongo_uri.startswith("mongodb+srv://")
            else {}
        )
        client = pymongo.MongoClient(mongo_uri, **config)
        db = client.get_database()

        # Usuario de emergencia
        emergency_user = {
            "_id": ObjectId(),
            "email": "admin@emergency.com",
            "username": "emergency_admin",
            "password": "emergency_password_2025",
            "role": "admin",
            "active": True,
            "created_at": "2025-01-01T00:00:00Z",
        }

        # Verificar si ya existe
        existing = db.users.find_one({"email": emergency_user["email"]})
        if existing:
            print("✅ Usuario de emergencia ya existe")
        else:
            db.users.insert_one(emergency_user)
            print("✅ Usuario de emergencia creado")
            print(f"   Email: {emergency_user['email']}")
            print(f"   Password: {emergency_user['password']}")

        client.close()
        return True

    except Exception as e:
        print(f"❌ Error creando usuario de emergencia: {e}")
        return False


def fix_permissions():
    """Arregla permisos de archivos"""
    print("\n🔐 ARREGLANDO PERMISOS")
    print("=" * 40)

    try:
        # Determinar la ruta de la aplicación
        if getattr(sys, "frozen", False):
            app_path = os.path.dirname(sys.executable)
        else:
            app_path = os.getcwd()

        # Archivos importantes
        important_files = [".env", "logs", "flask_session"]

        for file_name in important_files:
            file_path = os.path.join(app_path, file_name)
            if os.path.exists(file_path):
                # Dar permisos de lectura/escritura
                os.chmod(file_path, 0o755)
                print(f"✅ Permisos arreglados para: {file_name}")

        return True

    except Exception as e:
        print(f"❌ Error arreglando permisos: {e}")
        return False


def main():
    """Función principal"""
    print("🔧 SOLUCIÓN RÁPIDA MONGODB PARA MACOS")
    print("=" * 60)

    try:
        # Paso 1: Crear archivo .env
        if not create_env_file():
            print("❌ No se pudo crear el archivo .env")
            return

        # Paso 2: Instalar dependencias
        if not install_requirements():
            print("❌ No se pudieron instalar las dependencias")
            return

        # Paso 3: Arreglar certificados SSL
        if not fix_ssl_certificates():
            print("❌ No se pudieron arreglar los certificados SSL")
            return

        # Paso 4: Arreglar permisos
        if not fix_permissions():
            print("❌ No se pudieron arreglar los permisos")
            return

        # Paso 5: Probar conexión
        if not test_mongodb_connection():
            print("❌ No se pudo conectar a MongoDB")
            print("💡 Verifica tu conexión a internet y la URI de MongoDB")
            return

        # Paso 6: Crear usuario de emergencia
        create_fallback_user()

        print("\n🎉 ¡SOLUCIÓN COMPLETADA!")
        print("✅ La aplicación debería funcionar correctamente ahora")
        print("\n💡 Próximos pasos:")
        print("   1. Reinicia la aplicación")
        print("   2. Intenta hacer login")
        print("   3. Si hay problemas, ejecuta el script de diagnóstico")

    except Exception as e:
        print(f"\n❌ Error durante la solución: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
