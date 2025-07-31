#!/usr/bin/env python3
"""
Script para probar la subida de archivos a Google Drive.
"""
import os
import sys
from tools.db_utils.google_drive_utils import upload_to_drive

def main():
    if len(sys.argv) < 2:
        print("Uso: python test_gdrive_upload.py <ruta_al_archivo>")
        sys.exit(1)
    
    filepath = sys.argv[1]
    
    if not os.path.exists(filepath):
        print(f"Error: El archivo {filepath} no existe.")
        sys.exit(1)
    
    print(f"Intentando subir el archivo: {filepath}")
    
    try:
        result = upload_to_drive(filepath)
        if result.get('success'):
            print("\n✅ Archivo subido exitosamente a Google Drive!")
            print("\nDetalles del archivo:")
            print(f"- Nombre: {result.get('filename')}")
            print(f"- ID: {result.get('file_id')}")
            print(f"- Tamaño: {result.get('file_size')} bytes")
            print(f"- URL: {result.get('web_view_url')}")
            print(f"- Carpeta: {result.get('folder_name')} (ID: {result.get('folder_id')})")
        else:
            print(f"\n❌ Error al subir el archivo: {result.get('error')}")
            
    except Exception as e:
        print(f"\n❌ Error inesperado: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
