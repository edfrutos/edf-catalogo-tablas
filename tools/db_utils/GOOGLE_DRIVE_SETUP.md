# Configuración de Google Drive para Backups

Para habilitar la funcionalidad de backups con Google Drive, necesitas configurar las credenciales de OAuth2.

## Pasos para configurar Google Drive:

### 1. Crear proyecto en Google Cloud Console

1. Ve a [Google Cloud Console](https://console.cloud.google.com/)
2. Crea un nuevo proyecto o selecciona uno existente
3. Habilita la **Google Drive API**:
   - Ve a "APIs & Services" > "Library"
   - Busca "Google Drive API"
   - Haz clic en "Enable"

### 2. Crear credenciales OAuth2

1. Ve a "APIs & Services" > "Credentials"
2. Haz clic en "+ CREATE CREDENTIALS" > "OAuth client ID"
3. Si es la primera vez, configura la pantalla de consentimiento OAuth:
   - Selecciona "External" (a menos que tengas Google Workspace)
   - Completa la información básica de la aplicación
   - En "Scopes", agrega:
     - `https://www.googleapis.com/auth/drive`
     - `https://www.googleapis.com/auth/drive.file`
     - `https://www.googleapis.com/auth/drive.metadata.readonly`
4. Selecciona "Desktop application" como tipo de aplicación
5. Dale un nombre (ej: "Catalogo Tablas Backup")
6. Descarga el archivo JSON de credenciales

### 3. Configurar credenciales en el proyecto

1. Renombra el archivo descargado a `credentials.json`
2. Cópialo a la carpeta `tools/db_utils/`
3. Asegúrate de que el archivo tenga la siguiente estructura:

```json
{
  "installed": {
    "client_id": "tu-client-id.googleusercontent.com",
    "project_id": "tu-project-id",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_secret": "tu-client-secret",
    "redirect_uris": ["http://localhost"]
  }
}
```

### 4. Ejecutar configuración inicial

Desde la raíz del proyecto, ejecuta:

```bash
cd tools/db_utils
python3 setup_google_drive.py
```

Esto abrirá un navegador para completar la autenticación OAuth2 y generará el archivo `token.json`.

### 5. Verificar configuración

Una vez completada la configuración, deberías tener estos archivos en `tools/db_utils/`:
- `credentials.json` (credenciales OAuth2)
- `token.json` (token de acceso generado)
- `settings.yaml` (configuración de PyDrive2)

## Solución de problemas

### Error: "Not a gzipped file"
Este error indica que la descarga de Google Drive no está funcionando. Verifica:
1. Que los archivos de credenciales estén configurados correctamente
2. Que el token no haya expirado
3. Que la cuenta tenga permisos para acceder a los archivos

### Error: "Token expirado"
Si el token expira, puedes regenerarlo:
```bash
cd tools/db_utils
rm token.json
python3 setup_google_drive.py
```

### Error: "Archivo no encontrado"
Verifica que:
1. El archivo `credentials.json` existe en `tools/db_utils/`
2. El archivo tiene el formato JSON correcto
3. Los permisos del archivo permiten lectura

## Seguridad

⚠️ **IMPORTANTE**: 
- Nunca subas `credentials.json` o `token.json` a un repositorio público
- Agrega estos archivos a tu `.gitignore`
- Mantén las credenciales seguras y no las compartas

## Estructura de carpetas en Google Drive

La aplicación creará automáticamente una carpeta llamada `Backups_CatalogoTablas` en tu Google Drive donde se almacenarán todos los backups.