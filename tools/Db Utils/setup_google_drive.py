#!/usr/bin/env python3
# Script: setup_google_drive.py
# Descripción: [Script para configurar inicialmente la autenticación de Google Drive. Debe ejecutarse una vez para generar el token inicial.]
# Uso: python3 setup_google_drive.py [opciones]
# Requiere: [librerías externas, si aplica]
# Variables de entorno: [si aplica]
# Autor: EDF Equipo de Desarrollo - 2025-05-28
"""
Script para configurar inicialmente la autenticación de Google Drive
Debe ejecutarse una vez para generar el token inicial
"""

from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
import os

def setup_google_drive_auth():
    """Configura la autenticación inicial de Google Drive"""
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    creds_file = os.path.join(script_dir, 'credentials.json')
    settings_file = os.path.join(script_dir, 'settings.yaml')
    token_file = os.path.join(script_dir, 'token.json')
    
    print("🔧 Configurando autenticación de Google Drive...")
    print(f"📁 Directorio: {script_dir}")
    print(f"📄 Credenciales: {creds_file}")
    print(f"⚙️ Settings: {settings_file}")
    print(f"🔑 Token: {token_file}")
    
    # Verificar archivos
    if not os.path.exists(creds_file):
        print(f"❌ Error: No se encuentra {creds_file}")
        return False
        
    if not os.path.exists(settings_file):
        print(f"❌ Error: No se encuentra {settings_file}")
        return False
    
    try:
        # Configurar autenticación
        gauth = GoogleAuth(settings_file)
        
        print("\n🌐 Iniciando autenticación OAuth...")
        print("Se abrirá un navegador para completar la autenticación")
        print("Por favor, sigue las instrucciones en el navegador")
        
        # Hacer autenticación interactiva
        gauth.LocalWebserverAuth(port_numbers=[8080, 8081, 8082])
        
        # Verificar que la autenticación fue exitosa
        if gauth.credentials:
            print("✅ Autenticación exitosa!")
            
            # Guardar el token
            gauth.SaveCredentialsFile(token_file)
            print(f"💾 Token guardado en: {token_file}")
            
            # Probar la conexión
            drive = GoogleDrive(gauth)
            print("🔍 Probando conexión con Google Drive...")
            
            # Listar algunos archivos para verificar
            file_list = drive.ListFile({'q': "'root' in parents and trashed=false", 'maxResults': 5}).GetList()
            print(f"✅ Conexión exitosa! Encontrados {len(file_list)} archivos en Drive")
            
            return True
        else:
            print("❌ Error: No se pudieron obtener credenciales")
            return False
            
    except Exception as e:
        print(f"❌ Error durante la autenticación: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("CONFIGURACIÓN INICIAL DE GOOGLE DRIVE")
    print("=" * 60)
    
    success = setup_google_drive_auth()
    
    if success:
        print("\n" + "=" * 60)
        print("✅ CONFIGURACIÓN COMPLETADA EXITOSAMENTE")
        print("Ahora puedes usar Google Drive desde la aplicación Flask")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("❌ CONFIGURACIÓN FALLÓ")
        print("Revisa los errores arriba y vuelve a intentar")
        print("=" * 60)
