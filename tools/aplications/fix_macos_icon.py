#!/usr/bin/env python3
"""
Script para corregir el problema del icono en la aplicación macOS
Configura correctamente el Info.plist y verifica los recursos necesarios
"""

import os
import sys
import plistlib
import shutil
from pathlib import Path

def fix_app_icon(app_path="dist/EDF_CatalogoJoyero.app"):
    """
    Corrige la configuración del icono para la aplicación macOS
    """
    print(f"🔧 Corrigiendo configuración de icono para {app_path}")
    
    if not os.path.exists(app_path):
        print(f"❌ Error: La aplicación {app_path} no existe")
        return False
    
    # Rutas importantes
    contents_path = os.path.join(app_path, "Contents")
    info_plist_path = os.path.join(contents_path, "Info.plist")
    resources_path = os.path.join(contents_path, "Resources")
    
    # Verificar estructura básica
    if not os.path.exists(contents_path):
        print(f"❌ Error: No existe Contents/ en {app_path}")
        return False
    
    # Crear directorio Resources si no existe
    if not os.path.exists(resources_path):
        print(f"📁 Creando directorio Resources...")
        os.makedirs(resources_path)
    
    # Buscar archivo de icono existente
    icon_files = []
    for ext in ['.icns', '.ico', '.png']:
        for root, dirs, files in os.walk(app_path):
            for file in files:
                if file.lower().endswith(ext) and 'icon' in file.lower():
                    icon_files.append(os.path.join(root, file))
    
    print(f"🔍 Archivos de icono encontrados: {icon_files}")
    
    # Configurar Info.plist
    try:
        if os.path.exists(info_plist_path):
            with open(info_plist_path, 'rb') as f:
                plist_data = plistlib.load(f)
            print("📄 Info.plist existente cargado")
        else:
            plist_data = {}
            print("📄 Creando nuevo Info.plist")
        
        # Configuraciones básicas
        plist_data.update({
            'CFBundleName': 'EDF CatalogoJoyero',
            'CFBundleDisplayName': 'EDF CatalogoJoyero',
            'CFBundleIdentifier': 'com.edf.catalogojoyero',
            'CFBundleVersion': '1.0.0',
            'CFBundleShortVersionString': '1.0.0',
            'CFBundleExecutable': 'EDF_CatalogoJoyero',
            'CFBundlePackageType': 'APPL',
            'LSMinimumSystemVersion': '10.13.0',
            'NSHighResolutionCapable': True,
            'NSRequiresAquaSystemAppearance': False
        })
        
        # Configurar icono si existe
        if icon_files:
            # Usar el primer icono encontrado
            icon_file = icon_files[0]
            icon_name = os.path.basename(icon_file)
            
            # Copiar icono a Resources si no está ahí
            target_icon_path = os.path.join(resources_path, icon_name)
            if not os.path.exists(target_icon_path):
                shutil.copy2(icon_file, target_icon_path)
                print(f"📋 Icono copiado a Resources: {icon_name}")
            
            # Configurar en plist
            plist_data['CFBundleIconFile'] = icon_name.replace('.icns', '')  # Sin extensión
            print(f"🎨 Configurado CFBundleIconFile: {plist_data['CFBundleIconFile']}")
        else:
            print("⚠️  No se encontró archivo de icono")
        
        # Guardar Info.plist
        with open(info_plist_path, 'wb') as f:
            plistlib.dump(plist_data, f)
        
        print("✅ Info.plist actualizado correctamente")
        
        # Mostrar configuración final
        print("\n📋 Configuración final del Info.plist:")
        for key in ['CFBundleName', 'CFBundleDisplayName', 'CFBundleIconFile']:
            if key in plist_data:
                print(f"   {key}: {plist_data[key]}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error al configurar Info.plist: {e}")
        return False

def create_default_icon():
    """
    Crea un icono por defecto si no existe ninguno
    """
    print("🎨 Creando icono por defecto...")
    
    # Este es un placeholder - en un caso real necesitarías crear un .icns
    # Por ahora solo documentamos el proceso
    print("""
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
    """)

def main():
    """Función principal"""
    print("🚀 Iniciando corrección de icono para aplicación macOS")
    
    # Verificar que estamos en macOS
    if sys.platform != 'darwin':
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
