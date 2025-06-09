#!/usr/bin/env python3
# Script: google_drive_utils.py
# Descripción: [Explica brevemente qué hace el script]
# Uso: python3 google_drive_utils.py [opciones]
# Requiere: [librerías externas, si aplica]
# Variables de entorno: [si aplica]
# Autor: EDF Equipo de Desarrollo - 2025-05-28

from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
import os
import argparse
import logging
logging.basicConfig(level=logging.DEBUG)

def get_drive():
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
        creds_file = os.path.join(script_dir, 'credentials.json')
        token_file = os.path.join(script_dir, 'token.json')
        
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
        
        # Configurar el archivo de credenciales
        gauth.settings['client_config_file'] = creds_file
        
        # Configuración del flujo OAuth
        gauth.DEFAULT_SETTINGS['client_config_file'] = creds_file
        gauth.DEFAULT_SETTINGS['save_credentials_file'] = token_file
        gauth.DEFAULT_SETTINGS['get_refresh_token'] = True
        gauth.DEFAULT_SETTINGS['oauth_scope'] = ['https://www.googleapis.com/auth/drive']
        
        # Configurar el backend de autenticación
        gauth.settings['client_config_backend'] = 'file'
        gauth.settings['save_credentials_backend'] = 'file'
        gauth.settings['save_credentials'] = True
        
        # Cargar credenciales existentes si existen
        if os.path.exists(token_file):
            try:
                print("Cargando credenciales existentes...")
                gauth.LoadCredentialsFile(token_file)
                print("✓ Credenciales cargadas correctamente")
            except Exception as e:
                print(f"✗ Error al cargar credenciales: {str(e)}")
                print("Eliminando token inválido...")
                os.remove(token_file)
        
        # Iniciar autenticación si es necesario
        if not hasattr(gauth, 'credentials') or gauth.credentials is None or gauth.access_token_expired:
            print("Iniciando autenticación...")
            gauth.LocalWebserverAuth(port_numbers=[8080, 8081, 8082])
            
            # Guardar credenciales
            if gauth.credentials:
                gauth.SaveCredentialsFile(token_file)
                print("✓ Credenciales guardadas correctamente")
        
        return GoogleDrive(gauth)
        
    except Exception as e:
        error_msg = f"Error en get_drive: {str(e)}"
        print("\n" + "="*80)
        print("ERROR DE AUTENTICACIÓN CON GOOGLE DRIVE")
        print("="*80)
        print("Posibles soluciones:")
        print("1. Verifica que el archivo 'credentials.json' existe y es válido")
        print("2. Asegúrate de que la API de Google Drive esté habilitada en Google Cloud Console")
        print("3. Intenta eliminar el archivo 'token.json' y vuelve a intentarlo")
        print("4. Verifica que la cuenta tenga permisos para acceder a Google Drive")
        print("5. Revisa que la URL de redirección en Google Cloud Console incluya 'http://localhost:8080/'")
        print("6. Asegúrate de que los puertos 8080-8082 no estén siendo usados por otras aplicaciones")
        print("7. Prueba con un navegador diferente o en modo incógnito")
        print("="*80 + "\n")
        raise Exception(error_msg)

def get_or_create_folder(drive, folder_name):
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
        file_list = drive.ListFile({'q': query}).GetList()
        
        # Si encontramos alguna carpeta con ese nombre, devolver la primera
        if file_list:
            folder_id = file_list[0]['id']
            print(f"Carpeta encontrada con ID: {folder_id}")
            return folder_id
            
        # Si no existe, crearla
        print(f"La carpeta '{folder_name}' no existe. Creando...")
        folder_metadata = {
            'title': folder_name,
            'mimeType': 'application/vnd.google-apps.folder',
            'description': f'Carpeta para almacenar backups de {folder_name}'
        }
        
        folder = drive.CreateFile(folder_metadata)
        folder.Upload()
        print(f"Carpeta creada con ID: {folder['id']}")
        return folder['id']
        
    except Exception as e:
        error_msg = f"Error en get_or_create_folder: {str(e)}"
        print(error_msg)
        # Intentar obtener más detalles del error
        if hasattr(e, 'content'):
            try:
                error_details = e.content.decode('utf-8')
                print(f"Detalles del error: {error_details}")
                error_msg = f"{error_msg}\nDetalles: {error_details}"
            except:
                pass
        raise Exception(error_msg)

def upload_to_drive(file_path, folder_name='Backups_CatalogoTablas'):
    """
    Sube un archivo a Google Drive en la carpeta especificada.
    
    Args:
        file_path (str): Ruta local del archivo a subir
        folder_name (str): Nombre de la carpeta en Google Drive (se creará si no existe)
        
    Returns:
        dict: Diccionario con el resultado de la operación
    """
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    import pickle
    import os
    
    print("\n" + "="*80)
    print(f"INICIANDO SUBIDA A GOOGLE DRIVE: {os.path.basename(file_path)}")
    print("="*80)
    
    try:
        # Verificar que el archivo existe
        if not os.path.exists(file_path):
            error_msg = f"El archivo no existe: {file_path}"
            print(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'filename': os.path.basename(file_path)
            }
            
        # Obtener información del archivo
        file_size = os.path.getsize(file_path) / (1024 * 1024)  # Tamaño en MB
        file_name = os.path.basename(file_path)
        print(f"Archivo: {file_name}")
        print(f"Tamaño: {file_size:.2f} MB")
        print(f"Carpeta destino: {folder_name}")
        
        # Configuración
        SCOPES = ['https://www.googleapis.com/auth/drive']
        creds_file = os.path.join(os.path.dirname(__file__), 'credentials.json')
        token_file = os.path.join(os.path.dirname(__file__), 'token.pickle')
        
        # Autenticación
        print("\n1. Inicializando autenticación con Google Drive...")
        creds = None
        
        # Cargar credenciales si existen
        if os.path.exists(token_file):
            with open(token_file, 'rb') as token:
                creds = pickle.load(token)
        
        # Si no hay credenciales válidas, autenticar
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(creds_file, SCOPES)
                creds = flow.run_local_server(port=0)
            
            # Guardar credenciales para la próxima vez
            with open(token_file, 'wb') as token:
                pickle.dump(creds, token)
        
        # Crear servicio de Google Drive
        service = build('drive', 'v3', credentials=creds)
        
        # Buscar o crear la carpeta
        print("\n2. Buscando carpeta en Google Drive...")
        query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
        results = service.files().list(q=query, fields="files(id, name)").execute()
        items = results.get('files', [])
        
        if not items:
            print(f"   La carpeta no existe. Creando '{folder_name}'...")
            file_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder'
            }
            folder = service.files().create(body=file_metadata, fields='id').execute()
            folder_id = folder.get('id')
            print(f"   Carpeta creada con ID: {folder_id}")
        else:
            folder_id = items[0]['id']
            print(f"   Carpeta encontrada con ID: {folder_id}")
        
        # Subir el archivo
        print(f"\n3. Subiendo archivo a Google Drive...")
        
        # Verificar si el archivo ya existe
        query = f"name='{file_name}' and '{folder_id}' in parents and trashed=false"
        results = service.files().list(q=query, fields="files(id, name)").execute()
        items = results.get('files', [])
        
        file_metadata = {
            'name': file_name,
            'parents': [folder_id]
        }
        
        media = MediaFileUpload(file_path, resumable=True)
        
        if items:
            print(f"   El archivo ya existe. Actualizando...")
            file_id = items[0]['id']
            file = service.files().update(
                fileId=file_id,
                media_body=media
            ).execute()
            print(f"   Archivo actualizado exitosamente con ID: {file_id}")
        else:
            file = service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()
            file_id = file.get('id')
            print(f"   Archivo subido exitosamente con ID: {file_id}")
        
        # Obtener enlace de vista previa
        file_url = f"https://drive.google.com/file/d/{file_id}/view?usp=sharing"
        
        print("\n" + "="*80)
        print("✅ SUBIDA COMPLETADA CON ÉXITO")
        print("="*80)
        print(f"Archivo: {file_name}")
        print(f"Tamaño: {file_size:.2f} MB")
        print(f"URL: {file_url}")
        
        return {
            'success': True,
            'file_id': file_id,
            'file_name': file_name,
            'file_size': file_size,
            'file_url': file_url
        }
        
    except Exception as e:
        error_msg = f"Error al subir a Google Drive: {str(e)}"
        print(error_msg)
        print("\n" + "="*80)
        print("ERROR DURANTE LA SUBIDA")
        print("="*80)
        print("Posibles soluciones:")
        print("1. Verifica tu conexión a internet")
        print("2. Asegúrate de que el archivo no esté abierto en otro programa")
        print("3. Verifica que tengas espacio suficiente en Google Drive")
        print("4. Si el error persiste, intenta eliminar el archivo token.pickle y vuelve a autenticarte")
        
        return {
            'success': False,
            'error': error_msg,
            'filename': os.path.basename(file_path) if 'file_path' in locals() else 'desconocido',
            'suggested_solution': 'Verifica la conexión a internet y los permisos de Google Drive.'
        }
            
        # No hay necesidad de este bloque ya que ya devolvimos la respuesta exitosa arriba
        pass
    
    except Exception as e:
        error_msg = f"Error en upload_to_drive: {str(e)}"
        print(f"\n✗ {error_msg}")
        print("\n" + "="*80)
        print("ERROR DURANTE LA SUBIDA")
        print("="*80)
        print("Posibles soluciones:")
        print("1. Verifica tu conexión a internet")
        print("2. Asegúrate de que el archivo no esté abierto en otro programa")
        print("3. Verifica que tengas espacio suficiente en Google Drive")
        print("4. Si el error persiste, intenta eliminar el archivo token.json y vuelve a autenticarte")
        print("="*80 + "\n")
        
        return {
            'success': False,
            'error': str(e),
            'filename': os.path.basename(filepath) if 'filepath' in locals() else 'unknown',
            'suggested_solution': 'Verifica la conexión a internet y los permisos de Google Drive. Si el problema persiste, intenta regenerar el token de autenticación.'
        }

def get_or_create_folder(drive, folder_name):
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
        file_list = drive.ListFile({'q': query}).GetList()
        
        # Si encontramos alguna carpeta con ese nombre, devolver la primera
        if file_list:
            folder_id = file_list[0]['id']
            print(f"Carpeta encontrada con ID: {folder_id}")
            return folder_id
            
        # Si no existe, crearla
        print(f"La carpeta '{folder_name}' no existe. Creando...")
        folder_metadata = {
            'title': folder_name,
            'mimeType': 'application/vnd.google-apps.folder',
            'description': f'Carpeta para almacenar backups de {folder_name}'
        }
        
        folder = drive.CreateFile(folder_metadata)
        folder.Upload()
        print(f"Carpeta creada con ID: {folder['id']}")
        return folder['id']
        
    except Exception as e:
        error_msg = f"Error en get_or_create_folder: {str(e)}"
        print(error_msg)
        # Intentar obtener más detalles del error
        if hasattr(e, 'content'):
            try:
                error_details = e.content.decode('utf-8')
                print(f"Detalles del error: {error_details}")
                error_msg = f"{error_msg}\nDetalles: {error_details}"
            except:
                pass
        raise Exception(error_msg)

def reset_gdrive_token():
    """
    Elimina el token.json y muestra instrucciones para regenerar el refresh_token de Google Drive.
    
    Returns:
        dict: Diccionario con el estado de la operación
    """
    try:
        # Obtener rutas de los archivos
        script_dir = os.path.dirname(os.path.abspath(__file__))
        token_path = os.path.join(script_dir, 'token.json')
        creds_path = os.path.join(script_dir, 'credentials.json')
        
        # Verificar que exista el archivo de credenciales
        if not os.path.exists(creds_path):
            error_msg = f"Error: No se encontró el archivo de credenciales en {creds_path}"
            print(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'message': 'Asegúrate de tener un archivo credentials.json válido en la carpeta tools/db_utils/'
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
                    'success': False,
                    'error': error_msg,
                    'message': 'No se pudo eliminar el archivo token.json. Verifica los permisos del archivo.'
                }
        else:
            print("ℹ️ El archivo token.json no existe. Se creará uno nuevo en la próxima autenticación.")
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
        
        return {
            'success': success,
            'message': message,
            'next_steps': instructions
        }
        
    except Exception as e:
        error_msg = f"Error inesperado en reset_gdrive_token: {str(e)}"
        print(f"✗ {error_msg}")
        return {
            'success': False,
            'error': error_msg,
            'message': 'Ocurrió un error inesperado al intentar reiniciar el token.'
        }

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