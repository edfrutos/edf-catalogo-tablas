#!/usr/bin/env python3
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
import os

def test_google_drive():
    # Configuración de rutas
    script_dir = os.path.dirname(os.path.abspath(__file__))
    creds_file = os.path.join(script_dir, 'tools', 'db_utils', 'credentials.json')
    token_file = os.path.join(script_dir, 'tools', 'db_utils', 'token.json')
    
    print(f"1. Verificando archivo de credenciales en: {creds_file}")
    if not os.path.exists(creds_file):
        print(f"✗ Error: No se encontró el archivo de credenciales en {creds_file}")
        return False
    
    print("2. Inicializando autenticación...")
    try:
        gauth = GoogleAuth()
        
        # Configuración básica
        gauth.settings['client_config_backend'] = 'file'
        gauth.settings['client_config_file'] = creds_file
        gauth.settings['save_credentials'] = True
        gauth.settings['save_credentials_backend'] = 'file'
        gauth.settings['save_credentials_file'] = token_file
        gauth.settings['get_refresh_token'] = True
        gauth.settings['oauth_scope'] = ['https://www.googleapis.com/auth/drive']
        
        # Configurar el backend de autenticación
        gauth.DEFAULT_SETTINGS['client_config_file'] = creds_file
        gauth.DEFAULT_SETTINGS['save_credentials_file'] = token_file
        
        print("3. Iniciando flujo de autenticación...")
        gauth.LocalWebserverAuth()
        
        print("4. Autenticación exitosa. Creando instancia de Google Drive...")
        drive = GoogleDrive(gauth)
        
        # Listar archivos para verificar que todo funciona
        print("5. Listando archivos en Google Drive (primeros 10):")
        file_list = drive.ListFile({'maxResults': 10}).GetList()
        for i, file1 in enumerate(file_list):
            print(f"   {i+1}. {file1['title']} ({file1['id']})")
            
        return True
        
    except Exception as e:
        print(f"✗ Error durante la autenticación: {str(e)}")
        return False

if __name__ == "__main__":
    print("=== PRUEBA DE CONEXIÓN A GOOGLE DRIVE ===")
    if test_google_drive():
        print("\n✅ ¡Prueba completada con éxito!")
    else:
        print("\n❌ La prueba ha fallado.")
        print("Por favor, verifica lo siguiente:")
        print("1. Que el archivo de credenciales existe y tiene el formato correcto")
        print("2. Que has habilitado la API de Google Drive en Google Cloud Console")
        print("3. Que has configurado las URIs de redirección correctamente")
        print("4. Que has otorgado los permisos necesarios a la aplicación")
