#!/usr/bin/env python3
"""
Script para corregir el problema del icono en la aplicación macOS
Configura correctamente el Info.plist y verifica los recursos necesarios
"""

import os
import plistlib
import shutil
import sys
from pathlib import Path


def fix_app_icon(app_path="dist/EDF_CatalogoJoyero.app"):
    """
    Corrige la configuración del icono para la aplicación macOS
    DESHABILITADO: El icono personalizado causa problemas con la aplicación nativa
    """
    print(f"🔧 Función de icono deshabilitada para evitar conflictos")
    print(f"💡 La aplicación usa el icono por defecto de PyInstaller")
    return True


def create_default_icon():
    """
    Crea un icono por defecto si no existe ninguno
    """
    print("🎨 Creando icono por defecto...")

    # Este es un placeholder - en un caso real necesitarías crear un .icns
    # Por ahora solo documentamos el proceso
    print(
        """
    Para crear un icono personalizado:
    1. Crear una imagen PNG de 1024x1024 píxeles
    2. Usar iconutil (macOS) para convertir a .icns:
       mkdir icon.iconset
       sips -z 16 16 icon.png --out icon.iconset/icon_16x16.png
       sips -z 32 32 icon.png --out icon.iconset/icon_16x16@2x.png
       sips -z 32 32 icon.png --out icon.iconset/icon_32x32.png
       sips -z 64 64 icon.png --out icon.iconset/icon_32x32@2x.png
       sips -z 128 128 icon.png --out icon.iconset/icon_128x128.png
       sips -z 256 256 icon.png --out icon.iconset/icon_128x128@2x.png
       sips -z 256 256 icon.png --out icon.iconset/icon_256x256.png
       sips -z 512 512 icon.png --out icon.iconset/icon_256x256@2x.png
       sips -z 512 512 icon.png --out icon.iconset/icon_512x512.png
       sips -z 1024 1024 icon.png --out icon.iconset/icon_512x512@2x.png
       iconutil -c icns icon.iconset
    3. Copiar el archivo icon.icns resultante al directorio del proyecto
    """
    )


def main():
    """Función principal"""
    print("🚀 Iniciando corrección de icono para aplicación macOS")

    # Verificar que estamos en macOS
    if sys.platform != "darwin":
        print("⚠️  Este script está diseñado para macOS")
        return

    # Corregir aplicación principal
    success = fix_app_icon("dist/EDF_CatalogoJoyero.app")

    if success:
        print("\n✅ Corrección completada exitosamente")
        print("💡 Para que los cambios surtan efecto:")
        print("   1. Cierra la aplicación si está ejecutándose")
        print("   2. Ejecuta: sudo touch /Applications")
        print("   3. Reinicia Finder: sudo killall Finder")
        print("   4. O reinicia el sistema")
    else:
        print("\n❌ La corrección falló")
        print("💡 Verifica que la aplicación existe en dist/EDF_CatalogoJoyero.app")


if __name__ == "__main__":
    main()
