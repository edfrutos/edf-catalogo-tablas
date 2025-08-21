#!/usr/bin/env python3
"""
Script para solucionar problemas de autenticación de Google Drive
"""

import os
import shutil
from pathlib import Path


def fix_google_drive_auth():
    """Solucionar problemas de autenticación de Google Drive"""

    script_dir = Path(__file__).parent
    creds_file = script_dir / "credentials.json"
    token_file = script_dir / "token.json"
    token_pickle = script_dir / "token.pickle"

    print("🔧 SOLUCIONANDO PROBLEMAS DE AUTENTICACIÓN DE GOOGLE DRIVE")
    print("=" * 60)

    # Paso 1: Verificar archivos existentes
    print("\n📋 PASO 1: Verificando archivos...")

    if not creds_file.exists():
        print(f"❌ FALTA: {creds_file}")
        print(
            "   Este archivo debe contener las credenciales OAuth de Google Cloud Console"
        )
        print("   Para obtenerlo:")
        print("   1. Ve a https://console.cloud.google.com/")
        print("   2. Crea un proyecto o selecciona uno existente")
        print("   3. Habilita la API de Google Drive")
        print("   4. Crea credenciales OAuth 2.0 para aplicación de escritorio")
        print("   5. Descarga el JSON y guárdalo como 'credentials.json'")
        return False

    print(f"✅ Encontrado: {creds_file}")

    # Paso 2: Eliminar tokens expirados
    print("\n📋 PASO 2: Limpiando tokens expirados...")

    if token_file.exists():
        print(f"🗑️ Eliminando token expirado: {token_file}")
        token_file.unlink()

    if token_pickle.exists():
        print(f"🗑️ Eliminando token pickle: {token_pickle}")
        token_pickle.unlink()

    print("✅ Tokens eliminados")

    # Paso 3: Ejecutar configuración
    print("\n📋 PASO 3: Ejecutando configuración...")

    try:
        import subprocess
        import sys

        # Ejecutar setup_google_drive.py
        result = subprocess.run(
            [sys.executable, "setup_google_drive.py"],
            cwd=script_dir,
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            print("✅ Configuración exitosa")
            print(result.stdout)
            return True
        else:
            print("❌ Error en configuración:")
            print(result.stderr)
            return False

    except Exception as e:
        print(f"❌ Error ejecutando configuración: {e}")
        return False


def main():
    """Función principal"""
    success = fix_google_drive_auth()

    if success:
        print("\n" + "=" * 60)
        print("✅ PROBLEMA SOLUCIONADO")
        print("Ahora puedes usar Google Drive desde la aplicación Flask")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("❌ NO SE PUDO SOLUCIONAR")
        print("Revisa los pasos manualmente:")
        print("1. Asegúrate de tener credentials.json válido")
        print("2. Ejecuta: cd tools/db_utils && python setup_google_drive.py")
        print("=" * 60)


if __name__ == "__main__":
    main()
