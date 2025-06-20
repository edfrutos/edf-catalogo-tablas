#!/usr/bin/env python3
"""
Script para probar la autenticación con Google Drive.
"""
import os
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive

def test_auth():
    try:
        print("Iniciando prueba de autenticación con Google Drive...")
        
        # Configuración básica
        gauth = GoogleAuth()
        
        # Ruta a los archivos necesarios
        creds_file = os.path.join(os.path.dirname(__file__), 'tools/db_utils/credentials.json')
        token_file = os.path.join(os.path.dirname(__file__), 'tools/db_utils/token.json')
        
        print(f"Archivo de credenciales: {creds_file}")
        print(f"Archivo de token: {token_file}")
        
        # Verificar que el archivo de credenciales existe
        if not os.path.exists(creds_file):
            print("❌ Error: No se encontró el archivo credentials.json")
            return False
        
        # Configurar la autenticación
        gauth.DEFAULT_SETTINGS['client_config_file'] = creds_file
        
        # Intentar cargar credenciales existentes
        if os.path.exists(token_file):
            print("Cargando credenciales existentes...")
            gauth.LoadCredentialsFile(token_file)
        
        # Iniciar autenticación
        if gauth.credentials is None:
            print("Iniciando autenticación en el navegador...")
            gauth.LocalWebserverAuth(port_numbers=[8080, 8090])
        elif gauth.access_token_expired:
            print("Refrescando token...")
            gauth.Refresh()
        else:
            print("Usando credenciales existentes...")
            gauth.Authorize()
        
        # Guardar credenciales
        gauth.SaveCredentialsFile(token_file)
        
        # Probar la conexión
        drive = GoogleDrive(gauth)
        file_list = drive.ListFile({'q': "'root' in parents and trashed=false"}).GetList()
        
        print("✅ Autenticación exitosa!")
        print(f"Encontrados {len(file_list)} archivos en la raíz de Google Drive")
        return True
        
    except Exception as e:
        print(f"❌ Error durante la autenticación: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_auth()
