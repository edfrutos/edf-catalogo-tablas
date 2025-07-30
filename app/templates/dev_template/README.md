# Plantilla de Desarrollo Flask/MongoDB: Estructura de Testing

Esta plantilla incluye una estructura de tests reutilizable para proyectos Flask con MongoDB, basada en buenas prácticas y ejemplos reales del proyecto edf_catalogotablas.

## Estructura recomendada

```bash
dev_template/
├── tests/
│   ├── conftest.py
│   ├── integration/
│   │   ├── README.md
│   │   ├── test_admin_api.py
│   │   ├── test_admin_dashboard.py
│   │   ├── test_admin_panel.py
│   │   ├── test_admin_panel_actions.py
│   │   ├── test_admin_panel_actions_full.py
│   │   ├── test_app_integration.py
│   │   ├── test_auth.py
│   │   ├── test_auth_routes.py
│   │   ├── test_blueprints_smoke.py
│   │   ├── test_catalogs_crud.py
│   │   ├── test_catalogs_routes.py
│   │   ├── test_catalogs_rows.py
│   │   ├── test_gdrive.py
│   │   ├── test_gdrive_upload.py
│   │   ├── test_gdrive_v2.py
│   │   ├── test_login_direct.py
│   │   ├── test_main_routes.py
│   │   ├── test_maintenance_dashboard.py
│   │   ├── test_mongo.py
│   │   ├── test_mongo_connection.py
│   │   ├── test_mongodb_integration.py
│   │   ├── test_s3_cors.py
│   │   ├── test_session_direct.py
│   │   ├── test_session_integration.py
│   │   ├── test_session_simple.py
│   │   └── test_upload_simple.py
│   └── app/
│       └── routes/
│           ├── test_admin_routes_func.py
│           ├── test_auth_routes_func.py
│           ├── test_auth_user_flow_func.py
│           ├── test_catalogs_crud_func.py
│           ├── test_catalogs_routes_func.py
│           ├── test_emergency_routes_func.py
│           ├── test_errors_routes_func.py
│           ├── test_flash_func.py
│           ├── test_image_routes_func.py
│           ├── test_main_routes_func.py
│           ├── test_session_routes.py
│           ├── test_session_routes_test.py
│           └── test_usuarios_routes_func.py
```

## Descripción de los archivos clave

- `conftest.py`: Configura los fixtures globales de pytest, carga el entorno y prepara la app Flask y la conexión MongoDB para testing.
- `integration/`: Tests de integración de alto nivel (API, dashboard, login, mantenimiento, etc.)
- `app/routes/`: Tests funcionales de rutas específicas de la app.

## ¿Cómo usar esta plantilla?

1. Copia el directorio `tests/` a tu nuevo proyecto.
2. Ajusta los imports en `conftest.py` y los tests para que apunten a los módulos reales de tu proyecto (por ejemplo, `from app import create_app`).
3. Personaliza o elimina los tests que sean demasiado específicos.
4. Ejecuta los tests con:

   ```bash
   pytest tests/
   ```

## Ventajas

- Arranque inmediato de testing profesional en nuevos proyectos.
- Ejemplos de integración y uso de fixtures reutilizables.
- Buenas prácticas de organización y cobertura funcional.

---

**Incluye este README y la estructura de tests en tu plantilla de desarrollo para maximizar la calidad y mantenibilidad desde el inicio.**
