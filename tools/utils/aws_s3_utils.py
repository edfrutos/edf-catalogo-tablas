#!/usr/bin/env python3
"""
Script: aws_s3_utils.py
Descripción: Acceso rápido al menú de utilidades AWS S3.
             Este script redirige al menú interactivo ubicado en tools/local/aws_utils/

Uso:
  python3 aws_s3_utils.py

Autor: EDF Developer - 2025-08-08
Versión: 1.0
"""

import os
import sys
import subprocess
from pathlib import Path


def main():
    """Función principal que redirige al menú de AWS S3."""

    # Obtener el directorio del script actual
    current_dir = Path(__file__).parent

    # Ruta al menú de AWS S3
    menu_path = current_dir / "tools" / "local" / "aws_utils" / "aws_s3_menu.py"

    print("🚀 AWS S3 UTILS - ACCESO RÁPIDO")
    print("=" * 50)

    if not menu_path.exists():
        print("❌ Error: No se encontró el menú de AWS S3")
        print(f"   Buscado en: {menu_path}")
        print("\n💡 Asegúrate de que el proyecto esté correctamente configurado")
        sys.exit(1)

    print(f"📁 Redirigiendo a: {menu_path}")
    print("⏳ Iniciando menú interactivo...")
    print()

    try:
        # Ejecutar el menú
        subprocess.run([sys.executable, str(menu_path)], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Error ejecutando el menú: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n👋 ¡Hasta luego!")
        sys.exit(0)


if __name__ == "__main__":
    main()
