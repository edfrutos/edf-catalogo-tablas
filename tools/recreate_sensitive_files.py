#!/usr/bin/env python3
"""
Script para recrear archivos sensibles locales
"""

import json
import os
from pathlib import Path


def recreate_notifications_config():
    """Recrear archivo de configuración de notificaciones"""

    config = {
        "enabled": True,
        "smtp": {
            "server": "smtp-relay.brevo.com",
            "port": 587,
            "username": "TU_USUARIO_SMTP_AQUI",
            "password": "TU_PASSWORD_SMTP_AQUI",
            "use_tls": True,
        },
        "brevo_api": {
            "api_key": "TU_API_KEY_DE_BREVO_AQUI",
            "sender_name": "Administrador",
            "sender_email": "no-reply@edefrutos2025.xyz",
        },
        "use_api": True,
        "recipients": [
            "tu-email-principal@ejemplo.com",
            "tu-email-secundario@ejemplo.com",
        ],
        "thresholds": {"cpu": 80, "memory": 90, "disk": 85, "error_rate": 5},
        "cooldown_minutes": 60,
        "last_alerts": {
            "memory": "2025-06-06 10:45:02",
            "cpu": "2025-08-25 12:38:12",
            "database": "2025-08-25 16:56:09",
        },
    }

    # Crear directorio si no existe
    app_data_dir = Path("app_data")
    app_data_dir.mkdir(exist_ok=True)

    # Guardar archivo
    config_file = app_data_dir / "edefrutos2025_notifications_config.json"
    with open(config_file, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

    print(f"✅ Archivo recreado: {config_file}")
    return config_file


def recreate_env_file():
    """Recrear archivo .env"""

    env_content = """# Variables de entorno para EDF Catálogo de Tablas

# MongoDB
MONGO_URI=mongodb://localhost:27017/edefrutos2025

# Flask
SECRET_KEY=edefrutos2025-secret-key-local

# Brevo API
BREVO_API_KEY=TU_API_KEY_DE_BREVO_AQUI
BREVO_SMTP_USERNAME=TU_USUARIO_SMTP_AQUI
BREVO_SMTP_PASSWORD=TU_PASSWORD_SMTP_AQUI

# Emails de notificación
NOTIFICATION_EMAIL_1=tu-email-principal@ejemplo.com
NOTIFICATION_EMAIL_2=tu-email-secundario@ejemplo.com

# AWS S3 (si usas)
AWS_ACCESS_KEY_ID=tu_access_key_aqui
AWS_SECRET_ACCESS_KEY=tu_secret_key_aqui
AWS_REGION=us-east-1
S3_BUCKET_NAME=tu_bucket_name_aqui
"""

    # Guardar archivo .env
    with open(".env", "w", encoding="utf-8") as f:
        f.write(env_content)  # pyright: ignore[reportUnusedCallResult]

    print("✅ Archivo .env recreado")
    return ".env"


def recreate_github_secrets_script():
    """Recrear script de configuración de GitHub Secrets"""

    script_content = """#!/bin/bash

echo "🔐 Configurando GitHub Secrets Manualmente..."
echo "=============================================="

# Verificar si GitHub CLI está instalado
if ! command -v gh &> /dev/null; then
    echo "❌ GitHub CLI no está instalado"
    echo "📦 Instalando GitHub CLI..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        brew install gh
    else
        echo "Por favor, instala GitHub CLI manualmente: https://cli.github.com/"
        exit 1
    fi
fi

# Verificar si está autenticado
if ! gh auth status &> /dev/null; then
    echo "🔑 Autenticándose con GitHub..."
    gh auth login
fi

echo "📋 Configurando secrets con valores reales..."
echo ""

# Configurar cada secret con valores reales
echo "1. Configurando BREVO_API_KEY..."
gh secret set BREVO_API_KEY --body "TU_API_KEY_DE_BREVO_AQUI"

echo "2. Configurando BREVO_SMTP_USERNAME..."
gh secret set BREVO_SMTP_USERNAME --body "TU_USUARIO_SMTP_AQUI"

echo "3. Configurando BREVO_SMTP_PASSWORD..."
gh secret set BREVO_SMTP_PASSWORD --body "TU_PASSWORD_SMTP_AQUI"

echo "4. Configurando NOTIFICATION_EMAIL_1..."
gh secret set NOTIFICATION_EMAIL_1 --body "tu-email-principal@ejemplo.com"

echo "5. Configurando NOTIFICATION_EMAIL_2..."
gh secret set NOTIFICATION_EMAIL_2 --body "tu-email-secundario@ejemplo.com"

echo "6. Configurando MONGO_URI..."
gh secret set MONGO_URI --body "mongodb://localhost:27017/edefrutos2025"

echo "7. Configurando SECRET_KEY..."
gh secret set SECRET_KEY --body "edefrutos2025-secret-key-$(date +%s)"

echo ""
echo "✅ Todos los secrets han sido configurados exitosamente"
echo ""
echo "🔍 Para verificar, ve a:"
echo "   https://github.com/edfrutos/edf_catalogotablas/settings/secrets/actions"
echo ""
echo "🚀 El próximo push activará el workflow con los secrets configurados"
echo ""
echo "⚠️  IMPORTANTE: Este archivo contiene claves sensibles."
echo "   No lo commits al repositorio."
"""

    # Guardar script
    with open("setup_github_secrets_manual.sh", "w", encoding="utf-8") as f:
        f.write(script_content)  # pyright: ignore[reportUnusedCallResult]

    # Hacer ejecutable
    os.chmod("setup_github_secrets_manual.sh", 0o755)

    print("✅ Script setup_github_secrets_manual.sh recreado")
    return "setup_github_secrets_manual.sh"


def main():
    """Función principal"""
    print("🔄 Recreando archivos sensibles...")
    print("=" * 50)

    try:
        # Recrear archivos
        recreate_notifications_config()  # pyright: ignore[reportUnusedCallResult]
        recreate_env_file()  # pyright: ignore[reportUnusedCallResult]
        recreate_github_secrets_script()  # pyright: ignore[reportUnusedCallResult]

        print("\n✅ Todos los archivos sensibles han sido recreados")
        print("\n📋 Archivos creados:")
        print("   - app_data/edefrutos2025_notifications_config.json")
        print("   - .env")
        print("   - setup_github_secrets_manual.sh")

        print("\n⚠️  IMPORTANTE:")
        print("   - Estos archivos están en .gitignore")
        print("   - NO los commits al repositorio")
        print("   - Solo son para desarrollo local")
        print("   - Reemplaza los placeholders con tus claves reales")

    except Exception as e:
        print(f"❌ Error al recrear archivos: {e}")


if __name__ == "__main__":
    main()
