#!/usr/bin/env python3
"""
Script para configurar Google Drive usando autenticación por línea de comandos
"""

import os
import sys
from pathlib import Path

try:
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    import pickle
except ImportError as e:
    print(f"❌ Error: Falta módulo {e}")
    print(
        "Instala con: pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client"
    )
    sys.exit(1)


def setup_google_drive_cli():
    """Configura Google Drive usando autenticación CLI"""

    script_dir = Path(__file__).parent
    creds_file = script_dir / "credentials.json"
    token_file = script_dir / "token.pickle"

    print("🔧 CONFIGURACIÓN DE GOOGLE DRIVE (CLI)")
    print("=" * 50)

    # Verificar credenciales
    if not creds_file.exists():
        print(f"❌ Error: No se encuentra {creds_file}")
        return False

    print(f"✅ Credenciales encontradas: {creds_file}")

    # Scopes necesarios
    SCOPES = [
        "https://www.googleapis.com/auth/drive",
        "https://www.googleapis.com/auth/drive.file",
        "https://www.googleapis.com/auth/drive.metadata.readonly",
    ]

    creds = None

    # Cargar token existente si existe
    if token_file.exists():
        try:
            with open(token_file, "rb") as token:
                creds = pickle.load(token)
            print("✅ Token existente cargado")
        except Exception as e:
            print(f"⚠️ Error cargando token: {e}")

    # Si no hay credenciales válidas, hacer autenticación
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                print("🔄 Refrescando token...")
                creds.refresh(Request())
                print("✅ Token refrescado")
            except Exception as e:
                print(f"❌ Error refrescando token: {e}")
                creds = None

        if not creds:
            try:
                print("🌐 Iniciando autenticación OAuth...")
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(creds_file), SCOPES
                )

                # Usar autenticación por línea de comandos
                creds = flow.run_local_server(
                    port=8080, prompt="consent", access_type="offline"
                )

                print("✅ Autenticación completada")

            except Exception as e:
                print(f"❌ Error en autenticación: {e}")
                return False

        # Guardar credenciales
        try:
            with open(token_file, "wb") as token:
                pickle.dump(creds, token)
            print(f"💾 Token guardado en: {token_file}")
        except Exception as e:
            print(f"❌ Error guardando token: {e}")
            return False

    # Probar conexión
    try:
        from googleapiclient.discovery import build

        service = build("drive", "v3", credentials=creds)

        # Listar archivos para verificar
        results = (
            service.files()
            .list(pageSize=5, fields="nextPageToken, files(id, name)")
            .execute()
        )

        files = results.get("files", [])
        print(f"✅ Conexión exitosa! Encontrados {len(files)} archivos en Drive")

        if files:
            print("📁 Archivos de ejemplo:")
            for file in files[:3]:
                print(f"   - {file['name']} (ID: {file['id']})")

        return True

    except Exception as e:
        print(f"❌ Error probando conexión: {e}")
        return False


def main():
    """Función principal"""
    success = setup_google_drive_cli()

    if success:
        print("\n" + "=" * 50)
        print("✅ CONFIGURACIÓN COMPLETADA")
        print("Ahora puedes usar Google Drive desde la aplicación Flask")
        print("=" * 50)
    else:
        print("\n" + "=" * 50)
        print("❌ CONFIGURACIÓN FALLÓ")
        print("Revisa los errores y vuelve a intentar")
        print("=" * 50)


if __name__ == "__main__":
    main()
