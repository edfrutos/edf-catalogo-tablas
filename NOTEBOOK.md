# NOTEBOOK — edf_catalogotablas

> Estado del proyecto · última actualización: 2026-05-08

---

## Qué es esto

Aplicación web Flask para gestión de **catálogos de datos** con soporte de imágenes, documentos, multimedia y usuarios con roles (admin / user). Backend MongoDB (Atlas), almacenamiento de archivos en AWS S3 con fallback local.

Stack: Flask 3.0.2 · PyMongo · Flask-Login · Gunicorn · Bootstrap 5 · Bootstrap Icons.

---

## Arquitectura resumida

```
wsgi.py → app/factory.py (create_app)
              ├── Blueprints: main, auth, catalogs, admin, api, users…
              ├── MongoDB (app/database.py) + fallback (app/data_fallback.py)
              ├── S3/boto3 (app/extensions.py)
              ├── CSP / HSTS (app/security_middleware.py)
              └── ProxyFix (werkzeug) — para nginx/Caddy
```

Rutas clave:
| Ruta | Blueprint | Quién accede |
|---|---|---|
| `/catalogs/` | `catalogs_bp` | todos los usuarios |
| `/catalogs/view/<id>` | `catalogs_bp` | todos |
| `/catalogs/add-row/<id>` | `catalogs_bp` | admin |
| `/admin/catalogo/spreadsheets/<id>` | `admin_bp` | admin |
| `/dashboard_user` | `main_bp` | redirige a `/catalogs/` |

---

## Estado actual — lo que funciona

- [x] Login / logout / cambio de contraseña temporal
- [x] Vista de catálogos en tarjetas (`/catalogs/`) para admin y usuarios normales
- [x] Vista detalle de catálogo con tabla paginada y búsqueda
- [x] Añadir fila (documentos, multimedia, imágenes) — `catalogs.add_row`
- [x] Imágenes: se muestran en columna "Imágenes" de `ver_tabla.html`
- [x] Multimedia: reproductor de vídeo/audio con presigned URL de S3; fallback a archivo local si S3 no lo tiene
- [x] Documentos: PDF/Word/Excel/Markdown con previsualización
- [x] CSP headers con `media-src` para S3 y blob:
- [x] `dashboard_user` redirige directamente a la lista de catálogos
- [x] Botón "Añadir fila" visible en `ver_catalogo.html` (admin) cuando el catálogo está vacío o no

---

## Correcciones aplicadas en esta sesión (2026-05-08)

| Archivo | Cambio |
|---|---|
| `app/extensions.py` | `SESSION_COOKIE_DOMAIN = None` (era `"127.0.0.1"`, rompía cookies en dominio real) |
| `app/factory.py` | Añadido `ProxyFix(x_for=1, x_proto=1, x_host=1)` para nginx/Caddy |
| `run_server.py` | `debug=False` por defecto; solo activo si `DEBUG=1` en entorno |
| `app/templates/admin/ver_catalogo.html` | Botón "Añadir fila" en barra de acciones + CTA en estado vacío |
| `.gitignore` | Añadido `.claude/worktrees/` |

Correcciones de sesiones anteriores (resumen):
- `main_routes.py` — `agregar_fila()`: documentos se guardaban en clave incorrecta (`Documentos_2`). Corregido.
- `main_routes.py` — multimedia usaba guardado local en vez de `handle_file_upload()` (S3-aware).
- `security_middleware.py` — añadido `media-src` para S3; `img-src` ampliado a `https:`.
- `admin_routes.py` — proxy S3: `head_object` antes de presigned URL; fallback correcto a `static/uploads/`.
- `ver_tabla.html` — columna "Imágenes" renderiza `row._imagenes` en vez del campo vacío.
- `agregar_fila.html` / `add_row.html` — evitar campo de texto para header "Imágenes".

---

## Pendiente / deuda técnica

### Alta prioridad (antes del primer despliegue real)
- [ ] **nginx/Caddy config** — no está versionada. Crearla en `/deploy/` o documentarla en `DESPLIEGUE.md`.
- [ ] **Verificar `.env` de producción** — `SECRET_KEY` ≥ 32 chars, `USE_S3=true`, `MONGO_URI` a Atlas.
- [ ] **Test de sesión en dominio real** — después del fix de `SESSION_COOKIE_DOMAIN`, probar login en el subdominio objetivo.
- [ ] **Systemd service file** — `/etc/systemd/system/edefrutos2025.service` no está en el repo.

### Media prioridad
- [ ] `agregar_fila.html` (ruta `main.agregar_fila`) es la versión legacy usada por usuarios normales desde `ver_tabla.html`. Evaluar unificarla con `catalogs/add_row.html`.
- [ ] `run_server_multi.py` — revisar si sigue siendo necesario o es dead code.
- [ ] `launcher_native_websockets.py` / `launcher_web.py` en raíz — duplicados de `app/launcher/`. Limpiar.
- [ ] Paginación del lado servidor — actualmente se carga toda la colección en memoria y se pagina en JS.
- [ ] Tests unitarios — directorio `tests/` existe pero vacío de cobertura real.

### Baja prioridad / mejoras
- [ ] Columna "Imágenes" en `add_row`: actualmente el campo hardcoded `name="images"` acepta hasta 3 imágenes. Considerar campo dinámico.
- [ ] CSP: `img-src https:` es amplio — acotar a dominios S3 específicos cuando el entorno esté fijo.
- [ ] `WARP.md` — ignorado por `.gitignore`, revisar si tiene contenido útil para mover a `DESPLIEGUE.md`.

---

## Cómo arrancar en desarrollo

```bash
# Con el venv del sistema (Python 3.11)
/Library/Frameworks/Python.framework/Versions/3.11/bin/python3.11 run_server.py
# → http://localhost:5100

# Con DEBUG activo
DEBUG=1 python3.11 run_server.py
```

## Cómo arrancar en producción

```bash
# Gunicorn — 4 workers, puerto 5100 (nginx hace proxy inverso)
gunicorn -w 4 -b 0.0.0.0:5100 wsgi:app

# O vía systemd
systemctl restart edefrutos2025
```

---

## Variables de entorno requeridas

Ver `.env.example` para la lista completa. Las críticas:

```
SECRET_KEY=<mínimo 32 chars aleatorios>
MONGO_URI=mongodb+srv://...
USE_S3=true
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_REGION=eu-south-2
AWS_BUCKET_NAME=...
```
