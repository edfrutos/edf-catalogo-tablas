# Google Drive y backups

## Google Drive

El proyecto contiene utilidades para integración con Google Drive.

Las credenciales y tokens no deben versionarse.

## Backups

Los backups locales y snapshots no deben versionarse.

Directorios ignorados:

- `_backups_limpieza_*`
- `_snapshots_funcionales/`
- `backups/`
- `tools/db_utils/backups/`

## Archivos sensibles

No deben subirse:

- `credentials*.json`
- `token*.json`
- `token.pickle`
- `.env`
- claves privadas
