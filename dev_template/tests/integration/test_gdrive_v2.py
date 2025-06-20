#!/usr/bin/env python3
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import os
import pickle

def get_google_drive_service():
    creds = None
    SCOPES = ['https://www.googleapis.com/auth/drive']
    token_file = 'tools/db_utils/token.pickle'
    creds_file = 'tools/db_utils/credentials.json'
    
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
    
    return build('drive', 'v3', credentials=creds)

def main():
    try:
        print("Iniciando autenticación con Google Drive...")
        service = get_google_drive_service()
        
        # Listar los primeros 10 archivos
        print("\nListando los primeros 10 archivos en Google Drive:")
        results = service.files().list(
            pageSize=10, 
            fields="nextPageToken, files(id, name, mimeType, createdTime)"
        ).execute()
        
        items = results.get('files', [])
        
        if not items:
            print('No se encontraron archivos.')
        else:
            for item in items:
                print(f"- {item['name']} ({item['id']})")
        
        print("\n✅ Autenticación exitosa!")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        print("\nPosibles soluciones:")
        print("1. Verifica que el archivo credentials.json existe y es válido")
        print("2. Asegúrate de que la API de Google Drive esté habilitada")
        print("3. Verifica que las URIs de redirección en Google Cloud Console incluyan http://localhost:*")

if __name__ == '__main__':
    main()
