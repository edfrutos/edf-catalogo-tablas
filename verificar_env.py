#!/usr/bin/env python3
"""
Script de verificación del archivo .env
Verifica que todas las variables críticas están correctamente configuradas
"""

import os
import sys
from pathlib import Path


def main():
    """Función principal de verificación del archivo .env"""
    print("🔍 VERIFICADOR DE ARCHIVO .env")
    print("=" * 40)

    # Verificar que existe .env
    env_file = Path(".env")
    if not env_file.exists():
        print("❌ Archivo .env no encontrado")
        sys.exit(1)

    print("✅ Archivo .env encontrado")

    # Cargar variables
    try:
        from dotenv import load_dotenv

        load_dotenv()
        print("✅ Variables de entorno cargadas")
    except ImportError:
        print("⚠️  python-dotenv no instalado. Instalando...")
        os.system("pip install python-dotenv")
        from dotenv import load_dotenv

        load_dotenv()

    # Variables críticas a verificar
    critical_vars = {
        "SECRET_KEY": "Clave secreta de Flask",
        "MONGO_URI": "URI de MongoDB",
        "BREVO_SMTP_USERNAME": "Usuario SMTP Brevo",
        "BREVO_SMTP_PASSWORD": "Password SMTP Brevo",
        "NOTIFICATION_EMAIL_1": "Email de notificación 1",
        "NOTIFICATION_EMAIL_2": "Email de notificación 2",
    }

    print("\n📋 VERIFICACIÓN DE VARIABLES CRÍTICAS:")
    print("-" * 40)

    all_ok = True
    for var, _desc in critical_vars.items():
        value = os.getenv(var)
        if value:
            # Mostrar solo parte de valores sensibles
            if "PASSWORD" in var or "SECRET" in var or "KEY" in var:
                display_value = f"{value[:8]}...***"
            else:
                display_value = value
            print(f"✅ {var}: {display_value}")
        else:
            print(f"❌ {var}: NO DEFINIDA")
            all_ok = False

    # Verificar valores problemáticos
    print("\n🚨 VERIFICACIÓN DE SEGURIDAD:")
    print("-" * 40)

    secret_key = os.getenv("SECRET_KEY", "")
    if "clave-secreta" in secret_key.lower():
        print("⚠️  SECRET_KEY usando valor por defecto")
    else:
        print("✅ SECRET_KEY personalizada")

    brevo_password = os.getenv("BREVO_SMTP_PASSWORD", "")
    if "Rmp3UXwsIkvA0c1d" in brevo_password:
        print("🚨 BREVO_SMTP_PASSWORD usando credencial comprometida")
    else:
        print("✅ BREVO_SMTP_PASSWORD actualizada")

    brevo_api = os.getenv("BREVO_API_KEY", "")
    if "tu-nueva-brevo" in brevo_api:
        print("⚠️  BREVO_API_KEY necesita configuración")
    else:
        print("✅ BREVO_API_KEY configurada")

    # Verificar conexión MongoDB (opcional)
    print("\n🗄️  VERIFICACIÓN DE MONGODB:")
    print("-" * 40)

    try:
        import pymongo

        mongo_uri = os.getenv("MONGO_URI")
        if mongo_uri:
            client = pymongo.MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
            client.admin.command("ismaster")
            print("✅ MongoDB conectado correctamente")
        else:
            print("❌ MONGO_URI no definida")
    except ImportError:
        print("⚠️  pymongo no instalado - no se puede verificar MongoDB")
    except Exception as e:
        print(f"❌ Error conectando a MongoDB: {e}")

    print("\n" + "=" * 40)
    if all_ok:
        print("✅ Archivo .env correctamente configurado")
    else:
        print("⚠️  Archivo .env necesita configuración adicional")

    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
