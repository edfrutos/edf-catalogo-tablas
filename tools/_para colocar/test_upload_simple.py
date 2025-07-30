#!/usr/bin/env python3
"""
Script simplificado para probar la subida de archivos a Google Drive.
"""
import os
import sys

from tools.db_utils.google_drive_utils import get_drive, get_or_create_folder


def upload_file(filepath, folder_name="Backups_CatalogoTablas"):
    try:
        print(f"Iniciando subida del archivo: {filepath}")

        # Validar que el archivo exista
        if not os.path.exists(filepath):
            print(f"Error: El archivo {filepath} no existe")
            return False

        # Obtener información del archivo
        file_size = os.path.getsize(filepath)
        file_basename = os.path.basename(filepath)

        print(f"Tamaño del archivo: {file_size} bytes")

        # Inicializar Google Drive
        print("Conectando con Google Drive...")
        drive = get_drive()

        # Obtener o crear carpeta
        print(f"Buscando/creando carpeta: {folder_name}")
        folder_id = get_or_create_folder(drive, folder_name)

        # Subir archivo
        print("Subiendo archivo...")
        file_metadata = {
            "title": file_basename,
            "parents": [{"id": folder_id}],
            "description": f"Backup de prueba: {file_basename}",
        }

        file1 = drive.CreateFile(file_metadata)
        file1.SetContentFile(filepath)
        file1.Upload()

        print(f"✅ Archivo subido exitosamente!")
        print(f"ID del archivo: {file1['id']}")
        print(f"Enlace: https://drive.google.com/file/d/{file1['id']}/view")

        return True

    except Exception as e:
        print(f"❌ Error durante la subida: {str(e)}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python test_upload_simple.py <ruta_al_archivo> [nombre_carpeta]")
        sys.exit(1)

    filepath = sys.argv[1]
    folder_name = sys.argv[2] if len(sys.argv) > 2 else "Backups_CatalogoTablas"

    upload_file(filepath, folder_name)
