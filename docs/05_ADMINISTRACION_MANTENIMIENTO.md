# Administración y mantenimiento

## Panel de administración

Incluye gestión de catálogos, usuarios, mantenimiento y herramientas auxiliares.

## Validaciones recomendadas

```bash
python -m py_compile app/routes/main_routes.py app/routes/catalogs_routes.py app/routes/admin_routes.py
```

## Limpieza

No deben versionarse:

- `.venv/`
- `logs/`
- `flask_session/`
- `app_data/*.json`
- backups locales
- snapshots locales
- documentación histórica duplicada
