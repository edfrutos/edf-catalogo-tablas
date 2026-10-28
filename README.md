# TablaTeca (antes «EDF Catálogo de Tablas»)

Gestor de catálogos y tablas con documentos, imágenes y multimedia por fila. Interfaz web (Flask) y aplicación nativa para macOS (pywebview + PyInstaller).

## Ediciones

| | **Mac App Store** (edición de tienda) | **Web / DMG con Developer ID** |
|---|---|---|
| Acceso | Se abre directamente: **sin inicio de sesión ni gestión de usuarios** (un único usuario local) | Usuarios, roles y permisos |
| Datos | **100 % local**: base SQLite en el contenedor de la app | MongoDB |
| Archivos | Carpeta `uploads` local | Local o AWS S3 |
| Copias de seguridad | Local (la exportación/importación en ZIP está pendiente) | Google Drive y copias locales |
| Red | No necesita servidor ni cuenta | Servidor propio o MongoDB Atlas |

La edición de tienda se activa con `EDF_EDITION=store` (o con el marcador `EDITION` dentro del paquete). En ella la app solo escucha en `127.0.0.1` y la sesión local solo se abre con el token de arranque que genera el propio launcher; ver `app/store_edition.py`.

### Dónde guarda los datos la edición de tienda

La app está en el sandbox de macOS, así que los datos viven en su contenedor:

```
~/Library/Containers/com.edefrutos.tablateca/Data/Library/Application Support/EDF_Catalogo/
  ├── (base SQLite)
  └── uploads/        # imágenes, documentos y multimedia
~/Library/Logs/EDF_Catalogo/launcher.log
```

Desinstalar la app no borra el contenedor; para empezar de cero hay que eliminar esa carpeta.

## Características

- Catálogos con columnas personalizables y filas con imágenes, documentos (PDF, TXT, MD…) y multimedia.
- Visor de PDF integrado (pdf.js incluido en la app, sin CDN), visor de imágenes y de Markdown.
- Miniatura por catálogo y búsqueda/ordenación en la tabla de filas.
- Aplicación nativa para macOS.
- Solo edición web/DMG: gestión de usuarios y permisos, MongoDB, AWS S3 y copia de seguridad en Google Drive.

## Documentación

- **[NOTEBOOK.md](./NOTEBOOK.md)** — Características, funcionalidades y mejoras del proyecto
- **[docs/](./docs/)** — Documentación completa (guías, despliegue, seguridad, etc.)
- **[packaging/mas/](./packaging/mas/)** — Empaquetado y firma de la edición Mac App Store

## Inicio rápido (desarrollo)

```bash
# Instalar dependencias
pip install -r requirements.txt

# Edición web (usuarios + MongoDB): configurar variables de entorno
cp .env.example .env  # si existe
python run_server.py

# Edición de tienda en local (sin login, SQLite)
EDF_EDITION=store python run_server.py
```

## Compilación de la edición Mac App Store

El `.pkg` firmado se genera con el flujo de GitHub Actions `build_macos_mas.yml` (lanzado a mano con *Run workflow* sobre `main`; los cambios que no tocan `packaging/mas/**` no lo disparan solos). El resultado es el artefacto `TablaTeca-MAS.pkg`, que se sube a App Store Connect con Transporter. El número de «Acerca de» muestra la versión y el número de build.

## Licencia

Este proyecto está bajo la Licencia MIT.
