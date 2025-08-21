# Configuración de Google Drive

## Problema Actual
El botón de Google Drive en el dashboard de mantenimiento no funciona porque el token de autenticación ha expirado.

## Solución

### Paso 1: Obtener Credenciales de Google Cloud Console

1. Ve a [Google Cloud Console](https://console.cloud.google.com/)
2. Crea un nuevo proyecto o selecciona uno existente
3. Habilita la API de Google Drive:
   - Ve a "APIs & Services" > "Library"
   - Busca "Google Drive API"
   - Haz clic en "Enable"
4. Crea credenciales OAuth 2.0:
   - Ve a "APIs & Services" > "Credentials"
   - Haz clic en "Create Credentials" > "OAuth 2.0 Client IDs"
   - Selecciona "Desktop application"
   - Dale un nombre (ej: "EDF CatalogoTablas")
   - Haz clic en "Create"
5. Descarga el archivo JSON de credenciales

### Paso 2: Configurar el Proyecto

1. Copia el archivo JSON descargado a `tools/db_utils/credentials.json`
2. Ejecuta el script de configuración:

```bash
cd tools/db_utils
python fix_google_drive_auth.py
```

### Paso 3: Autenticación

1. El script abrirá un navegador
2. Inicia sesión con tu cuenta de Google
3. Autoriza la aplicación
4. El token se guardará automáticamente

### Paso 4: Verificar

1. Ve a http://localhost:5001/admin/maintenance/dashboard
2. Haz clic en el botón "Google Drive"
3. Debería funcionar correctamente

## Archivos Importantes

- `credentials.json` - Credenciales OAuth (debes crearlo)
- `token.json` - Token de acceso (se genera automáticamente)
- `settings.yaml` - Configuración de PyDrive
- `google_drive_utils.py` - Utilidades principales
- `setup_google_drive.py` - Script de configuración inicial
- `fix_google_drive_auth.py` - Script para solucionar problemas

## Troubleshooting

### Error: "Token has been expired or revoked"
```bash
cd tools/db_utils
python fix_google_drive_auth.py
```

### Error: "No se encuentra credentials.json"
1. Asegúrate de haber descargado las credenciales de Google Cloud Console
2. Renombra el archivo a `credentials.json`
3. Colócalo en la carpeta `tools/db_utils/`

### Error: "API not enabled"
1. Ve a Google Cloud Console
2. Habilita la API de Google Drive
3. Espera unos minutos y vuelve a intentar

## Notas Importantes

- El token expira cada cierto tiempo y necesita renovación
- Las credenciales son específicas para tu proyecto de Google Cloud
- No compartas el archivo `credentials.json` en el repositorio
- El archivo `token.json` se regenera automáticamente
