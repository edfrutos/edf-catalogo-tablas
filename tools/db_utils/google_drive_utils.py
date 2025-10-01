#!/usr/bin/env python3
# Script: google_drive_utils.py
# Descripción: Utilidades para interactuar con Google Drive API
# Uso: python3 google_drive_utils.py [opciones]
# Requiere: pydrive2, google-auth-oauthlib, google-auth, google-api-python-client
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
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive

# Configurar logging
logging.basicConfig(level=logging.DEBUG)

# Configurar tipos para suprimir advertencias de Pyright
# pyright: reportUnknownVariableType=false
# pyright: reportUnknownMemberType=false
# pyright: reportUnknownArgumentType=false
# pyright: reportUnusedCallResult=false

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


def get_drive() -> GoogleDrive:
    """
    Inicializa y devuelve una instancia autenticada de Google Drive.

    Returns:
        GoogleDrive: Instancia autenticada de GoogleDrive

    Raises:
        Exception: Si hay algún error en la autenticación
    """
    try:
        # Rutas a los archivos necesarios
        script_dir = os.path.dirname(os.path.abspath(__file__))
        creds_file = os.path.join(script_dir, "credentials.json")
        token_file = os.path.join(script_dir, "token.json")

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

        # Configuración de autenticación
        gauth = GoogleAuth()
        gauth_any = cast(Any, gauth)  # Para evitar problemas de tipos

        # Configurar el archivo de credenciales
        settings = cast(Dict[str, Any], gauth.settings)
        settings["client_config_file"] = creds_file

        # Configuración del flujo OAuth
        default_settings = cast(Dict[str, Any], gauth.DEFAULT_SETTINGS)
        default_settings["client_config_file"] = creds_file
        default_settings["save_credentials_file"] = token_file
        default_settings["get_refresh_token"] = True
        default_settings["oauth_scope"] = ["https://www.googleapis.com/auth/drive"]

        # Configurar el backend de autenticación
        settings = cast(Dict[str, Any], gauth.settings)
        settings["client_config_backend"] = "file"
        settings["save_credentials_backend"] = "file"
        settings["save_credentials"] = True

        # Cargar credenciales existentes si existen
        if os.path.exists(token_file):
            try:
                print(f"Cargando credenciales desde: {token_file}")
                gauth_any.LoadCredentialsFile(token_file)
                print("✓ Credenciales cargadas correctamente")

                # Verificar si el token ha expirado y necesita refresh
                # Usar hasattr para verificar si existe access_token_expired en
                # GoogleAuth, NO en GoogleDrive
                needs_refresh = False
                try:
                    if (
                        hasattr(gauth_any, "access_token_expired")
                        and gauth_any.access_token_expired
                    ):
                        needs_refresh = True
                    elif hasattr(gauth_any, "credentials") and gauth_any.credentials:
                        # Verificar de manera alternativa si las credenciales están
                        # válidas
                        credentials = gauth_any.credentials
                        if (
                            hasattr(credentials, "token_expiry")
                            and credentials.token_expiry
                        ):
                            if credentials.token_expiry <= datetime.datetime.utcnow():
                                needs_refresh = True
                except Exception as check_error:
                    print(f"⚠️ No se pudo verificar el estado del token: {check_error}")
                    # Si no podemos verificar, asumimos que está bien y continuamos
                    needs_refresh = False

                if needs_refresh:
                    print("⚠️ Token expirado, intentando refresh...")
                    try:
                        gauth_any.Refresh()
                        gauth_any.SaveCredentialsFile(token_file)
                        print("✓ Token refrescado exitosamente")
                    except Exception as refresh_error:
                        print(f"✗ Error al refrescar token: {refresh_error}")
                        # NO eliminamos el token, solo reportamos el error
                        raise Exception(
                            f"Token expirado y no se pudo refrescar: {refresh_error}"
                        )

            except Exception as e:
                print(f"✗ Error al cargar credenciales: {str(e)}")
                # NO eliminamos el archivo automáticamente
                # En su lugar, proporcionamos instrucciones claras
                raise Exception(
                    f"Error con credenciales guardadas: {str(e)}. "
                    + "Si el problema persiste, ejecute: "
                    + f"cd {script_dir} && python setup_google_drive.py"
                )

        # Iniciar autenticación si es necesario
        # Verificar si necesitamos autenticación con verificaciones más robustas
        needs_auth = False
        if not hasattr(gauth_any, "credentials") or gauth_any.credentials is None:
            needs_auth = True
        else:
            # Verificar expiración de manera segura SOLO en GoogleAuth
            try:
                if (
                    hasattr(gauth_any, "access_token_expired")
                    and gauth_any.access_token_expired
                ):
                    needs_auth = True
            except Exception:
                # Si hay error verificando, asumimos que está bien
                needs_auth = False

        if needs_auth:
            if os.path.exists(token_file):
                # Intentar cargar credenciales existentes
                try:
                    print("Intentando cargar credenciales guardadas...")
                    gauth_any.LoadCredentialsFile(token_file)
                    # ⚠️ IMPORTANTE: solo verificar access_token_expired en GoogleAuth, NO en GoogleDrive
                    if (
                        gauth_any.credentials
                        and hasattr(gauth_any, "access_token_expired")
                        and not gauth_any.access_token_expired
                    ):
                        print("✓ Credenciales cargadas y válidas")
                    else:
                        print("⚠️ Las credenciales expiraron, intentando refrescar...")
                        gauth_any.Refresh()
                        gauth_any.SaveCredentialsFile(token_file)
                        print("✓ Token refrescado correctamente")
                except Exception as e:
                    print(f"✗ Error al cargar/refrescar credenciales: {str(e)}")
                    # Si no podemos cargar, necesitamos autenticación manual
                    raise Exception(f"Necesita nueva autenticación. Error: {str(e)}")
            else:
                # No hay token guardado, necesita autenticación inicial
                raise Exception(
                    "No hay credenciales guardadas. Necesita configuración inicial de OAuth."
                )

        # Crear y retornar la instancia de GoogleDrive
        # IMPORTANTE: GoogleDrive NO tiene access_token_expired, solo GoogleAuth
        # lo tiene
        drive = GoogleDrive(gauth)

        # Para debugging, agregar una referencia al auth para poder acceder más
        # tarde si es necesario
        drive.auth = (
            gauth  # Esto nos permitirá verificar el auth más tarde si es necesario
        )

        return drive

    except Exception as e:
        error_msg = f"Error en get_drive: {str(e)}"
        print("\n" + "=" * 80)
        print("ERROR DE AUTENTICACIÓN CON GOOGLE DRIVE")
        print("=" * 80)
        print("Posibles soluciones:")
        print("1. Verifica que el archivo 'credentials.json' existe y es válido")
        print(
            "2. Asegúrate de que la API de Google Drive esté habilitada en Google Cloud Console"
        )
        print("3. Intenta eliminar el archivo 'token.json' y vuelve a intentarlo")
        print("4. Verifica que la cuenta tenga permisos para acceder a Google Drive")
        print(
            "5. Revisa que la URL de redirección en Google Cloud Console incluya 'http://localhost:8080/'"
        )
        print(
            "6. Asegúrate de que los puertos 8080-8082 no estén siendo usados por otras aplicaciones"
        )
        print("7. Prueba con un navegador diferente o en modo incógnito")
        print("=" * 80 + "\n")
        raise Exception(error_msg)


def get_or_create_folder(drive: GoogleDrive, folder_name: str) -> str:
    """
    Busca una carpeta por nombre en Google Drive y la devuelve si existe.
    Si no existe, la crea.

    Args:
        drive: Instancia de GoogleDrive autenticada
        folder_name (str): Nombre de la carpeta a buscar/crear

    Returns:
        str: ID de la carpeta encontrada o creada

    Raises:
        Exception: Si hay un error al buscar o crear la carpeta
    """
    try:
        print(f"Buscando carpeta: {folder_name}")

        # Buscar la carpeta por nombre
        query = f"mimeType='application/vnd.google-apps.folder' and title='{folder_name}' and trashed=false"
        file_list = drive.ListFile({"q": query}).GetList()

        # Si encontramos alguna carpeta con ese nombre, devolver la primera
        if file_list:
            folder_id = file_list[0]["id"]
            print(f"Carpeta encontrada con ID: {folder_id}")
            return folder_id

        # Si no existe, crearla
        print(f"La carpeta '{folder_name}' no existe. Creando...")
        folder_metadata = {
            "title": folder_name,
            "mimeType": "application/vnd.google-apps.folder",
            "description": f"Carpeta para almacenar backups de {folder_name}",
        }

        folder = drive.CreateFile(folder_metadata)
        folder.Upload()
        print(f"Carpeta creada con ID: {folder['id']}")
        return folder["id"]

    except Exception as e:
        error_msg = f"Error en get_or_create_folder: {str(e)}"
        print(error_msg)
        raise Exception(error_msg)


def upload_to_drive(
    file_path: str, folder_name: str = "Backups_CatalogoTablas"
) -> UploadResult:
    """
    Sube un archivo a Google Drive en la carpeta especificada.

    Args:
        file_path (str): Ruta local del archivo a subir
        folder_name (str): Nombre de la carpeta en Google Drive (se creará si no existe)

    Returns:
        Dict[str, Union[bool, str, float]]: Diccionario con el resultado de la operación
            - success (bool): True si la operación fue exitosa
            - file_id (str): ID del archivo en Google Drive (solo si success=True)
            - file_name (str): Nombre del archivo
            - file_size (float): Tamaño del archivo en MB (solo si success=True)
            - file_url (str): URL de vista previa del archivo (solo si success=True)
            - error (str): Mensaje de error (solo si success=False)
            - filename (str): Nombre del archivo (solo si success=False)
            - suggested_solution (str): Solución sugerida (solo si success=False)
    """

    print("\n" + "=" * 80)
    print(f"INICIANDO SUBIDA A GOOGLE DRIVE: {os.path.basename(file_path)}")
    print("=" * 80)

    try:
        # Verificar que el archivo existe
        if not os.path.exists(file_path):
            error_msg = f"El archivo no existe: {file_path}"
            print(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "filename": os.path.basename(file_path),
            }

        # Obtener información del archivo
        file_size = os.path.getsize(file_path) / (1024 * 1024)  # Tamaño en MB
        file_name = os.path.basename(file_path)
        print(f"Archivo: {file_name}")
        print(f"Tamaño: {file_size:.2f} MB")
        print(f"Carpeta destino: {folder_name}")

        # Configuración
        SCOPES = ["https://www.googleapis.com/auth/drive"]
        creds_file = os.path.join(os.path.dirname(__file__), "credentials.json")
        token_file = os.path.join(os.path.dirname(__file__), "token.pickle")

        # Autenticación
        print("\n1. Inicializando autenticación con Google Drive...")
        creds = None

        # Cargar credenciales si existen
        if os.path.exists(token_file):
            with open(token_file, "rb") as token:
                creds = pickle.load(token)

        # Si no hay credenciales válidas, autenticar
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(creds_file, SCOPES)
                creds = flow.run_local_server(port=0)

            # Guardar credenciales para la próxima vez
            with open(token_file, "wb") as token:
                pickle.dump(creds, token)

        # Crear servicio de Google Drive
        service = build("drive", "v3", credentials=creds)

        # Buscar o crear la carpeta
        print("\n2. Buscando carpeta en Google Drive...")
        query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
        results = service.files().list(q=query, fields="files(id, name)").execute()
        items = results.get("files", [])

        if not items:
            print(f"   La carpeta no existe. Creando '{folder_name}'...")
            file_metadata = {
                "name": folder_name,
                "mimeType": "application/vnd.google-apps.folder",
            }
            folder = service.files().create(body=file_metadata, fields="id").execute()
            folder_id = folder.get("id")
            print(f"   Carpeta creada con ID: {folder_id}")
        else:
            folder_id = items[0]["id"]
            print(f"   Carpeta encontrada con ID: {folder_id}")

        # Subir el archivo
        print("\n3. Subiendo archivo a Google Drive...")

        # Verificar si el archivo ya existe
        query = f"name='{file_name}' and '{folder_id}' in parents and trashed=false"
        results = service.files().list(q=query, fields="files(id, name)").execute()
        items = results.get("files", [])

        file_upload_metadata: Dict[str, Any] = {
            "name": file_name,
            "parents": [folder_id],
        }

        media = MediaFileUpload(file_path, resumable=True)

        if items:
            print("   El archivo ya existe. Actualizando...")
            file_id = items[0]["id"]
            file = service.files().update(fileId=file_id, media_body=media).execute()
            print(f"   Archivo actualizado exitosamente con ID: {file_id}")
        else:
            file = (
                service.files()
                .create(body=file_upload_metadata, media_body=media, fields="id")
                .execute()
            )
            file_id = file.get("id")
            print(f"   Archivo subido exitosamente con ID: {file_id}")

        # Obtener enlace de vista previa
        file_url = f"https://drive.google.com/file/d/{file_id}/view?usp=sharing"

        print("\n" + "=" * 80)
        print("✅ SUBIDA COMPLETADA CON ÉXITO")
        print("=" * 80)
        print(f"Archivo: {file_name}")
        print(f"Tamaño: {file_size:.2f} MB")
        print(f"URL: {file_url}")

        return {
            "success": True,
            "file_id": file_id,
            "file_name": file_name,
            "file_size": file_size,
            "file_url": file_url,
        }

    except Exception as e:
        error_msg = f"Error al subir a Google Drive: {str(e)}"
        print(error_msg)
        print("\n" + "=" * 80)
        print("ERROR DURANTE LA SUBIDA")
        print("=" * 80)
        print("Posibles soluciones:")
        print("1. Verifica tu conexión a internet")
        print("2. Asegúrate de que el archivo no esté abierto en otro programa")
        print("3. Verifica que tengas espacio suficiente en Google Drive")
        print(
            "4. Si el error persiste, intenta eliminar el archivo token.pickle y vuelve a autenticarte"
        )

        return {
            "success": False,
            "error": error_msg,
            "filename": (
                os.path.basename(file_path)
                if "file_path" in locals()
                else "desconocido"
            ),
            "suggested_solution": "Verifica la conexión a internet y los permisos de Google Drive.",
        }


def delete_file(file_id: str) -> bool:
    """
    Elimina un archivo de Google Drive por su ID.

    Args:
        file_id (str): ID del archivo en Google Drive

    Returns:
        bool: True si se eliminó correctamente, False en caso contrario

    Raises:
        Exception: Si hay algún error en la eliminación
    """
    try:
        print(f"Iniciando eliminación del archivo con ID: {file_id}")

        # Obtener instancia de Google Drive
        drive = get_drive()

        # Obtener información del archivo
        try:
            file_obj = drive.CreateFile({"id": file_id})
            file_obj.FetchMetadata()
            file_name = file_obj["title"]
            print(f"Eliminando archivo: {file_name}")
        except Exception as e:
            raise Exception(
                f"No se pudo obtener información del archivo {file_id}: {str(e)}"
            )

        # Eliminar el archivo
        try:
            file_obj.Delete()
            print(f"Archivo eliminado exitosamente: {file_name}")
            return True
        except Exception as e:
            raise Exception(f"Error al eliminar el archivo: {str(e)}")

    except Exception as e:
        error_msg = f"Error en delete_file: {str(e)}"
        print(error_msg)
        raise Exception(error_msg)


def download_file(file_id: str, output_path: Optional[str] = None) -> Union[bytes, str]:
    """
    Descarga un archivo de Google Drive por su ID.

    Args:
        file_id (str): ID del archivo en Google Drive
        output_path (str, optional): Ruta donde guardar el archivo. Si no se especifica,
                                   se devuelve el contenido como bytes.

    Returns:
        bytes or str: Si output_path es None, devuelve el contenido como bytes.
                     Si output_path se especifica, devuelve la ruta del archivo guardado.

    Raises:
        Exception: Si hay algún error en la descarga
    """
    try:
        print(f"Iniciando descarga del archivo con ID: {file_id}")

        # Obtener instancia de Google Drive
        drive = get_drive()

        # Obtener información del archivo
        try:
            file_obj = drive.CreateFile({"id": file_id})
            file_obj.FetchMetadata()
            file_name = file_obj["title"]
            file_size = int(file_obj.get("fileSize", 0))
            print(f"Archivo: {file_name}")
            print(f"Tamaño: {file_size / (1024 * 1024):.2f} MB")
        except Exception as e:
            raise Exception(
                f"No se pudo obtener información del archivo {file_id}: {str(e)}"
            )

        # Descargar el contenido del archivo
        print("Descargando contenido...")
        try:
            # Usar un archivo temporal para la descarga

            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                temp_path = temp_file.name

            # Descargar a archivo temporal
            file_obj.GetContentFile(temp_path)

            # Leer el contenido del archivo temporal
            with open(temp_path, "rb") as f:
                content_bytes = f.read()

            # Eliminar archivo temporal
            os.unlink(temp_path)

            if len(content_bytes) == 0:
                raise Exception("El archivo descargado está vacío")

            print(f"Descarga completada: {len(content_bytes)} bytes")

            # Si se especifica output_path, guardar el archivo
            if output_path:
                # Crear directorio si no existe
                os.makedirs(os.path.dirname(output_path), exist_ok=True)

                with open(output_path, "wb") as f:
                    f.write(content_bytes)

                print(f"Archivo guardado en: {output_path}")
                return output_path
            else:
                # Devolver el contenido como bytes
                return content_bytes

        except Exception as e:
            raise Exception(f"Error al descargar el contenido del archivo: {str(e)}")

    except Exception as e:
        error_msg = f"Error en download_file: {str(e)}"
        print(error_msg)
        raise Exception(error_msg)


def list_files_in_folder(
    folder_name: str = "Backups_CatalogoTablas",
) -> List[Dict[str, Any]]:
    """
    Lista todos los archivos en una carpeta específica de Google Drive.

    Args:
        folder_name (str): Nombre de la carpeta a listar

    Returns:
        List[Dict[str, Any]]: Lista de diccionarios con información de los archivos
    """
    try:
        print(f"Listando archivos en la carpeta: {folder_name}")

        # Obtener instancia de Google Drive
        drive = get_drive()

        # Buscar la carpeta
        folder_id = get_or_create_folder(drive, folder_name)

        # Listar archivos en la carpeta
        query = f"'{folder_id}' in parents and trashed=false"
        file_list = drive.ListFile({"q": query}).GetList()

        files_info = []
        for file_obj in file_list:
            # Convertir fechas UTC a zona horaria local
            created_date = file_obj.get("createdDate", "")
            modified_date = file_obj.get("modifiedDate", "")

            # Función para convertir fecha UTC a local
            def convert_utc_to_local(utc_date_str):
                if not utc_date_str:
                    return ""
                try:
                    # Parsear fecha UTC (formato: 2025-08-04T18:33:45.123Z)
                    if utc_date_str.endswith("Z"):
                        # Remover 'Z' y agregar '+00:00' para indicar UTC
                        utc_date_str = utc_date_str[:-1] + "+00:00"

                    # Parsear como datetime con zona horaria
                    from datetime import datetime, timezone

                    # Parsear la fecha UTC
                    dt_utc = datetime.fromisoformat(utc_date_str)

                    # Convertir a zona horaria local (CEST = UTC+2)
                    # Obtener offset local
                    import time

                    local_offset = time.timezone if time.daylight == 0 else time.altzone
                    local_offset_hours = (
                        -local_offset / 3600
                    )  # Convertir segundos a horas

                    # Aplicar offset manualmente
                    from datetime import timedelta

                    dt_local = dt_utc + timedelta(hours=local_offset_hours)

                    # Formatear como string
                    return dt_local.strftime("%Y-%m-%d %H:%M:%S")
                except Exception as e:
                    print(f"Error convirtiendo fecha {utc_date_str}: {e}")
                    return utc_date_str

            file_info = {
                "id": file_obj["id"],
                "name": file_obj["title"],
                "size": int(file_obj.get("fileSize", 0)),
                "created": convert_utc_to_local(created_date),
                "modified": convert_utc_to_local(modified_date),
                "download_url": f"https://drive.google.com/file/d/{file_obj['id']}/view",
                "file_id": file_obj["id"],  # Agregar file_id para descarga directa
            }
            files_info.append(file_info)

        print(f"Encontrados {len(files_info)} archivos")
        return files_info

    except Exception as e:
        error_msg = f"Error al listar archivos: {str(e)}"
        print(error_msg)
        raise Exception(error_msg)


def reset_gdrive_token() -> ResetTokenResult:
    """
    Elimina el token.json y muestra instrucciones para regenerar el refresh_token de Google Drive.

    Returns:
        dict: Diccionario con el estado de la operación
    """
    try:
        # Obtener rutas de los archivos
        script_dir = os.path.dirname(os.path.abspath(__file__))
        token_path = os.path.join(script_dir, "token.json")
        creds_path = os.path.join(script_dir, "credentials.json")

        # Verificar que exista el archivo de credenciales
        if not os.path.exists(creds_path):
            error_msg = (
                f"Error: No se encontró el archivo de credenciales en {creds_path}"
            )
            print(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "message": "Asegúrate de tener un archivo credentials.json válido en la carpeta tools/db_utils/",
            }

        # Eliminar el token si existe
        if os.path.exists(token_path):
            try:
                os.remove(token_path)
                print("✓ Archivo token.json eliminado exitosamente.")
                message = "Token eliminado correctamente. La próxima vez que se intente autenticar, se solicitarán nuevos permisos."
                success = True
            except Exception as e:
                error_msg = f"Error al eliminar el archivo token.json: {str(e)}"
                print(f"✗ {error_msg}")
                return {
                    "success": False,
                    "error": error_msg,
                    "message": "No se pudo eliminar el archivo token.json. Verifica los permisos del archivo.",
                }
        else:
            print(
                "ℹ️ El archivo token.json no existe. Se creará uno nuevo en la próxima autenticación."
            )
            message = "No se encontró un token existente. Se creará uno nuevo en la próxima autenticación."
            success = True

        # Mostrar instrucciones detalladas
        instructions = """

        Para generar un nuevo token de acceso:

        1. Ejecuta el siguiente comando desde la raíz del proyecto:
           python3 -m tools.db_utils.google_drive_utils --reset-token

        2. Se abrirá una ventana del navegador pidiendo que inicies sesión con tu cuenta de Google.

        3. Asegúrate de iniciar sesión con una cuenta que tenga permisos para acceder a Google Drive.

        4. Acepta los permisos solicitados por la aplicación.

        5. Después de la autenticación exitosa, se creará un nuevo archivo token.json
           en la carpeta tools/db_utils/

        6. El token se usará automáticamente para futuras operaciones con Google Drive.
        """

        print(instructions)

        return {"success": success, "message": message, "next_steps": instructions}

    except Exception as e:
        error_msg = f"Error inesperado en reset_gdrive_token: {str(e)}"
        print(f"✗ {error_msg}")
        return {
            "success": False,
            "error": error_msg,
            "message": "Ocurrió un error inesperado al intentar reiniciar el token.",
        }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Utilidades Google Drive para backups."
    )
    parser.add_argument("filepath", nargs="?", help="Ruta al archivo que quieres subir")
    parser.add_argument(
        "--folder",
        default="Backups_CatalogoTablas",
        help="Nombre de la carpeta de destino en Google Drive (por defecto: Backups_CatalogoTablas)",
    )
    parser.add_argument(
        "--reset-token",
        action="store_true",
        help="Borra el token.json y muestra instrucciones para regenerar el refresh_token",
    )
    args = parser.parse_args()

    if args.reset_token:
        _ = reset_gdrive_token()
    elif args.filepath:
        try:
            enlace = upload_to_drive(args.filepath, args.folder)
            print(f"Archivo subido correctamente. Enlace: {enlace}")
        except Exception as e:
            print(f"Error al subir el archivo: {e}")
            traceback.print_exc()
    else:
        parser.print_help()
