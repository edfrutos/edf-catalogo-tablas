#!/usr/bin/env python3
# Script: google_drive_utils_v2.py
# Descripción: Utilidades para interactuar con Google Drive API (versión actualizada)
# Uso: python3 google_drive_utils_v2.py [opciones]
# Requiere: google-auth-oauthlib, google-auth, google-api-python-client
# Variables de entorno: [si aplica]
# Autor: EDF Equipo de Desarrollo - 2025-05-28

import argparse
import datetime
import logging
import os
import pickle
import tempfile
import traceback
from typing import Any, Dict, List, Optional, TypedDict, Union, cast

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials

# Configurar logging
logging.basicConfig(level=logging.DEBUG)


# Tipo para el resultado de upload_to_drive
class UploadResult(TypedDict, total=False):
    success: bool
    file_id: str
    file_name: str
    file_size: float
    file_url: str
    error: str
    filename: str
    suggested_solution: str


# Tipo para el resultado de reset_gdrive_token
class ResetTokenResult(TypedDict, total=False):
    success: bool
    error: str
    message: str
    next_steps: str


# Tipo para la información de archivos en Google Drive
class FileInfo(TypedDict):
    id: str
    name: str
    size: int
    created: str
    modified: str
    download_url: str


def get_drive_service():
    """
    Inicializa y devuelve una instancia autenticada del servicio de Google Drive.

    Returns:
        googleapiclient.discovery.Resource: Instancia autenticada del servicio de Drive

    Raises:
        Exception: Si hay algún error en la autenticación
    """
    try:
        # Rutas a los archivos necesarios
        script_dir = os.path.dirname(os.path.abspath(__file__))
        creds_file = os.path.join(script_dir, "credentials.json")
        token_file = os.path.join(script_dir, "token.pickle")

        # Asegurarse de que el directorio existe
        os.makedirs(script_dir, exist_ok=True)

        # Verificar que el archivo de credenciales existe
        if not os.path.exists(creds_file):
            error_msg = (
                f"Error: El archivo de credenciales no existe en {creds_file}.\n"
                "Por favor, sigue estos pasos para solucionarlo:\n"
                "1. Ve a Google Cloud Console (https://console.cloud.google.com/)\n"
                "2. Crea un nuevo proyecto o selecciona uno existente\n"
                "3. Habilita la API de Google Drive\n"
                "4. Crea credenciales OAuth 2.0 para una aplicación de escritorio\n"
                "5. Descarga el archivo JSON y guárdalo como 'credentials.json' en la carpeta del script"
            )
            print(error_msg)
            raise FileNotFoundError(error_msg)

        # Scopes necesarios
        SCOPES = [
            "https://www.googleapis.com/auth/drive",
            "https://www.googleapis.com/auth/drive.file",
            "https://www.googleapis.com/auth/drive.metadata.readonly",
        ]

        creds = None

        # Cargar token existente si existe
        if os.path.exists(token_file):
            try:
                print(f"Cargando credenciales desde: {token_file}")
                with open(token_file, "rb") as token:
                    creds = pickle.load(token)
                print("✓ Credenciales cargadas correctamente")

                # Verificar si el token ha expirado y necesita refresh
                if creds and creds.expired and creds.refresh_token:
                    print("⚠️ Token expirado, intentando refresh...")
                    try:
                        creds.refresh(Request())
                        print("✓ Token refrescado exitosamente")

                        # Guardar el token actualizado
                        with open(token_file, "wb") as token:
                            pickle.dump(creds, token)
                        print("✓ Token actualizado guardado")

                    except Exception as refresh_error:
                        print(f"✗ Error al refrescar token: {refresh_error}")
                        raise Exception(
                            f"Token expirado y no se pudo refrescar: {refresh_error}"
                        )

            except Exception as e:
                print(f"✗ Error al cargar credenciales: {str(e)}")
                raise Exception(
                    f"Error con credenciales guardadas: {str(e)}. "
                    + "Si el problema persiste, ejecute: "
                    + f"cd {script_dir} && python setup_google_drive_cli.py"
                )

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
                    flow = InstalledAppFlow.from_client_secrets_file(creds_file, SCOPES)

                    # Usar autenticación por línea de comandos
                    creds = flow.run_local_server(
                        port=8080, prompt="consent", access_type="offline"
                    )

                    print("✅ Autenticación completada")

                    # Guardar credenciales
                    with open(token_file, "wb") as token:
                        pickle.dump(creds, token)
                    print(f"💾 Token guardado en: {token_file}")

                except Exception as e:
                    print(f"❌ Error en autenticación: {e}")
                    raise Exception(f"Error en autenticación: {e}")

        # Crear y retornar el servicio de Drive
        service = build("drive", "v3", credentials=creds)
        return service

    except Exception as e:
        print(f"❌ Error inicializando Google Drive: {e}")
        raise e


def list_files_in_folder(folder_name: str = "Backups_CatalogoTablas") -> List[FileInfo]:
    """
    Lista archivos en una carpeta específica de Google Drive.

    Args:
        folder_name: Nombre de la carpeta en Google Drive

    Returns:
        List[FileInfo]: Lista de archivos en la carpeta
    """
    try:
        service = get_drive_service()

        # Buscar la carpeta por nombre
        query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
        results = service.files().list(q=query, fields="files(id, name)").execute()
        folders = results.get("files", [])

        if not folders:
            print(f"❌ No se encontró la carpeta '{folder_name}' en Google Drive")
            return []

        folder_id = folders[0]["id"]
        print(f"📁 Carpeta encontrada: {folder_name} (ID: {folder_id})")

        # Listar archivos en la carpeta
        query = f"'{folder_id}' in parents and trashed=false"
        results = (
            service.files()
            .list(
                q=query,
                fields="files(id, name, size, createdTime, modifiedTime, webViewLink)",
                orderBy="modifiedTime desc",
            )
            .execute()
        )

        files = results.get("files", [])

        file_info_list = []
        for file in files:
            file_info = FileInfo(
                id=file["id"],
                name=file["name"],
                size=int(file.get("size", 0)),
                created=file.get("createdTime", ""),
                modified=file.get("modifiedTime", ""),
                download_url=file.get("webViewLink", ""),
            )
            file_info_list.append(file_info)

        print(f"✅ Encontrados {len(file_info_list)} archivos en '{folder_name}'")
        return file_info_list

    except Exception as e:
        print(f"❌ Error listando archivos: {e}")
        return []


def upload_file_to_drive(
    file_path: str, folder_name: str = "Backups_CatalogoTablas"
) -> UploadResult:
    """
    Sube un archivo a Google Drive.

    Args:
        file_path: Ruta del archivo a subir
        folder_name: Nombre de la carpeta en Google Drive

    Returns:
        UploadResult: Resultado de la subida
    """
    try:
        if not os.path.exists(file_path):
            return UploadResult(
                success=False,
                error=f"El archivo {file_path} no existe",
                suggested_solution="Verifica la ruta del archivo",
            )

        service = get_drive_service()

        # Buscar la carpeta por nombre
        query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
        results = service.files().list(q=query, fields="files(id, name)").execute()
        folders = results.get("files", [])

        if not folders:
            return UploadResult(
                success=False,
                error=f"No se encontró la carpeta '{folder_name}' en Google Drive",
                suggested_solution="Crea la carpeta en Google Drive o verifica el nombre",
            )

        folder_id = folders[0]["id"]

        # Preparar metadatos del archivo
        file_name = os.path.basename(file_path)
        file_metadata = {"name": file_name, "parents": [folder_id]}

        # Crear el archivo en Drive
        media = MediaFileUpload(file_path, resumable=True)
        file = (
            service.files()
            .create(
                body=file_metadata,
                media_body=media,
                fields="id, name, size, webViewLink",
            )
            .execute()
        )

        file_size = os.path.getsize(file_path) / (1024 * 1024)  # MB

        return UploadResult(
            success=True,
            file_id=file["id"],
            file_name=file["name"],
            file_size=file_size,
            file_url=file.get("webViewLink", ""),
            filename=file_name,
        )

    except Exception as e:
        return UploadResult(
            success=False,
            error=str(e),
            suggested_solution="Verifica la conexión a internet y los permisos de Google Drive",
        )


def download_file(file_id: str) -> bytes:
    """
    Descarga un archivo de Google Drive.

    Args:
        file_id: ID del archivo en Google Drive

    Returns:
        bytes: Contenido del archivo
    """
    try:
        service = get_drive_service()

        # Descargar el archivo
        request = service.files().get_media(fileId=file_id)
        file_content = request.execute()

        return file_content

    except Exception as e:
        print(f"❌ Error descargando archivo {file_id}: {e}")
        raise Exception(f"Error al descargar archivo: {e}")


def delete_file(file_id: str) -> bool:
    """
    Elimina un archivo de Google Drive.

    Args:
        file_id: ID del archivo en Google Drive

    Returns:
        bool: True si se eliminó correctamente, False en caso contrario
    """
    try:
        service = get_drive_service()

        # Eliminar el archivo
        service.files().delete(fileId=file_id).execute()

        print(f"✅ Archivo {file_id} eliminado exitosamente")
        return True

    except Exception as e:
        print(f"❌ Error eliminando archivo {file_id}: {e}")
        return False


def main():
    """Función principal para pruebas"""
    parser = argparse.ArgumentParser(description="Utilidades de Google Drive")
    parser.add_argument("--list", action="store_true", help="Listar archivos en Drive")
    parser.add_argument("--upload", type=str, help="Subir archivo a Drive")
    parser.add_argument(
        "--folder",
        type=str,
        default="Backups_CatalogoTablas",
        help="Nombre de la carpeta",
    )

    args = parser.parse_args()

    if args.list:
        print("📋 Listando archivos en Google Drive...")
        files = list_files_in_folder(args.folder)
        for file in files:
            print(f"   - {file['name']} ({file['size']} bytes)")

    elif args.upload:
        print(f"📤 Subiendo archivo: {args.upload}")
        result = upload_file_to_drive(args.upload, args.folder)
        if result["success"]:
            print(f"✅ Archivo subido exitosamente: {result['file_name']}")
            print(f"   ID: {result['file_id']}")
            print(f"   URL: {result['file_url']}")
        else:
            print(f"❌ Error: {result['error']}")

    else:
        print("🔧 Probando conexión con Google Drive...")
        try:
            service = get_drive_service()
            print("✅ Conexión exitosa con Google Drive")
        except Exception as e:
            print(f"❌ Error de conexión: {e}")


if __name__ == "__main__":
    main()
