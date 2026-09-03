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

---

## Estado técnico (2026-09-03)

> Deuda técnica conocida: **dos módulos, dos librerías, tres formatos de token.**

### Módulos

| Módulo | Librería | Token | Lo importan |
|---|---|---|---|
| `google_drive_utils.py` | `pydrive2` en `get_drive()`, `googleapiclient` en `upload_to_drive()` | `token.json` (oauth2client) **y** `token.pickle` | `admin_backups.py`, `admin_backup_routes.py`, `maintenance_routes_refactored.py`, `storage_utils.py` |
| `google_drive_utils_v2.py` | solo `googleapiclient` + `google-auth` | `token.pickle` | `backup_utils.py`, `maintenance_routes.py` |

### Artefactos (todos en esta carpeta, todos gitignored)

| Archivo | Formato | Generado por | Consumido por |
|---|---|---|---|
| `credentials.json` | client secret OAuth escritorio `{"installed":{...}}` | copia manual del `client_secret_*.json` de la raíz | ambos |
| `token.pickle` | `google.oauth2.credentials.Credentials` pickled | `regenerar_tokens_google_drive.py`, `generar_token_pickle.py` | v2 y rama googleapiclient de v1 |
| `token.json` | `oauth2client` `OAuth2Credentials` JSON | `regenerar_tokens_google_drive.py`, `setup_google_drive.py` | `get_drive()` (PyDrive2) de v1 |

### Regenerar los dos a la vez (recomendado)

```bash
python3 tools/db_utils/regenerar_tokens_google_drive.py
scp -P 2222 tools/db_utils/token.pickle tools/db_utils/token.json \
    root@208.76.221.20:/var/www/vhosts/edefrutos2020.com/edf_catalogotablas/tools/db_utils/
```

Si PyDrive2 rechaza el `token.json` traducido, usa `setup_google_drive.py` (flujo PyDrive nativo).

### Dependencias

`requirements.txt` (producción) NO lista `PyDrive2` ni `oauth2client` (sí están en
`requirements-python310-090925.txt`). Verifica en el servidor:
`.venv/bin/pip show pydrive2 oauth2client`.

### Pendiente (refactor, requiere pruebas contra Drive real)

1. Migrar los consumidores de `google_drive_utils.py` a `google_drive_utils_v2.py`.
2. Borrar `google_drive_utils.py`, `pydrive2`, `oauth2client`, `token.json`.
3. Un módulo, una librería, un formato de token.
4. Unificar dependencias entre los `requirements*.txt`.
