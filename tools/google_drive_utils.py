#!/usr/bin/env python3
# Script: google_drive_utils.py
# Descripción: [Explica brevemente qué hace el script]
# Uso: python3 google_drive_utils.py [opciones]
# Requiere: [librerías externas, si aplica]
# Variables de entorno: [si aplica]
# Autor: [Tu nombre o equipo] - 2025-05-28

from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
import os
import argparse

def get_drive():
    gauth = GoogleAuth()
    gauth.DEFAULT_SETTINGS['client_config_file'] = os.path.join(os.path.dirname(__file__), 'credentials.json')
    token_path = os.path.join(os.path.dirname(__file__), 'token.json')
    gauth.LoadCredentialsFile(token_path)
    if gauth.credentials is None:
        gauth.LocalWebserverAuth()
    elif gauth.access_token_expired:
        gauth.Refresh()
    else:
        gauth.Authorize()
    gauth.SaveCredentialsFile(token_path)
    return GoogleDrive(gauth)

def get_or_create_folder(drive, folder_name):
    file_list = drive.ListFile({'q': f"title='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"}).GetList()
    if file_list:
        return file_list[0]['id']
    folder_metadata = {'title': folder_name, 'mimeType': 'application/vnd.google-apps.folder'}
    folder = drive.CreateFile(folder_metadata)
    folder.Upload()
    return folder['id']

def upload_to_drive(filepath, folder_name='Backups_CatalogoTablas'):
    drive = get_drive()
    folder_id = get_or_create_folder(drive, folder_name)
    file1 = drive.CreateFile({'title': os.path.basename(filepath), 'parents': [{'id': folder_id}]})
    file1.SetContentFile(filepath)
    file1.Upload()
    return file1['alternateLink']

def reset_gdrive_token():
    """Elimina el token.json y muestra instrucciones para regenerar el refresh_token de Google Drive."""
    token_path = os.path.join(os.path.dirname(__file__), 'token.json')
    if os.path.exists(token_path):
        os.remove(token_path)
        print(f"✅ Archivo {token_path} eliminado.")
    else:
        print(f"ℹ️  No existe {token_path}, no hay nada que borrar.")
    print("\nIMPORTANTE: Ahora ejecuta una subida de prueba para lanzar el flujo OAuth2 y autorizar de nuevo la app.")
    print("Si no recibes refresh_token, elimina el acceso de la app en https://myaccount.google.com/permissions y repite el proceso.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Utilidades Google Drive para backups.")
    parser.add_argument("filepath", nargs="?", help="Ruta al archivo que quieres subir")
    parser.add_argument("--folder", default="Backups_CatalogoTablas", help="Nombre de la carpeta de destino en Google Drive (por defecto: Backups_CatalogoTablas)")
    parser.add_argument("--reset-token", action="store_true", help="Borra el token.json y muestra instrucciones para regenerar el refresh_token")
    args = parser.parse_args()

    if args.reset_token:
        reset_gdrive_token()
    elif args.filepath:
        try:
            enlace = upload_to_drive(args.filepath, args.folder)
            print(f"Archivo subido correctamente. Enlace: {enlace}")
        except Exception as e:
            import traceback
            print(f"Error al subir el archivo: {e}")
            traceback.print_exc()
    else:
        parser.print_help() 