# Catálogo de Tablas #

Aplicación Flask para la gestión de catálogos de tablas con autenticación, gestión de usuarios y almacenamiento en MongoDB.

## 🚀 Características Principales ##

- **Gestión de Usuarios**: Sistema de autenticación con roles (admin/user)
- **CRUD de Catálogos**: Creación, lectura, actualización y eliminación de catálogos
- **Importación/Exportación**: Soporte para Excel y CSV
- **Almacenamiento**: Imágenes en sistema de archivos local o S3
- **Monitoreo**: Sistema integrado de logging y monitoreo

## 🛠️ Estructura del Proyecto ##

```
./edf_catalogotablas/
├── app/                    # Código principal de la aplicación
│   ├── routes/             # Rutas de la aplicación
│   ├── static/             # Archivos estáticos (CSS, JS, imágenes)
│   ├── templates/          # Plantillas HTML
│   └── utils/              # Utilidades de la aplicación
├── config/                 # Archivos de configuración
├── docs/                   # Documentación del proyecto
├── models/                 # Modelos de datos
├── scripts/                # Scripts de utilidad
│   ├── db_utils/           # Utilidades de base de datos
│   ├── hooks/              # Hooks para PyInstaller
│   └── maintenance/        # Scripts de mantenimiento
├── tests/                  # Pruebas automatizadas
│   ├── integration/        # Pruebas de integración
│   └── unit/               # Pruebas unitarias
└── tools/                  # Herramientas de desarrollo
```

## 🚀 Instalación ##

1. **Clonar el repositorio**

   ```bash
   git clone https://github.com/edfrutos/edf_catalogotablas.git
   cd edf_catalogotablas
   ```

2. **Crear y activar entorno virtual**

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # En Windows: .venv\Scripts\activate
   ```

3. **Instalar dependencias**

   ```bash
   pip install -r requirements.txt
   ```

4. **Configurar variables de entorno**
   Copiar el archivo `.env.example` a `.env` y configurar según sea necesario.

5. **Iniciar la aplicación**

   ```bash
   python run.py
   ```

   O para producción:

   ```bash
   gunicorn --bind 0.0.0.0:5000 wsgi:app
   ```

## 📦 Dependencias Principales ##

- **Backend**: Flask, Flask-Login, Flask-PyMongo
- **Base de datos**: PyMongo
- **Autenticación**: bcrypt, Flask-Session
- **Procesamiento de datos**: pandas, openpyxl
- **Despliegue**: gunicorn

## 🤖 Ejecución de Pruebas ##

Para ejecutar las pruebas unitarias:

```bash
pytest tests/unit/
```

---

## 🍏 Build y Despliegue de la App macOS EDFCatalogoTablas ##

### Build Local Automático ###

1. Asegúrate de tener Python 3.10+ y [PyInstaller](https://pyinstaller.org/) instalado.
2. Ejecuta el script de build:

   ```bash
   ./build_mac_app.sh
   ```

   Esto generará el bundle en `dist/EDFCatalogoTablas.app`.

### Build Automático en GitHub Actions (CI) ###

- Cada push a `master` lanzará un workflow que construye la app en macOS y deja el bundle como artefacto descargable.
- El workflow está en `.github/workflows/mac_build.yml`.

### Instrucciones para Usuarios Finales ###

1. Descarga o clona el repositorio.
2. Si solo quieres la app, descarga `EDFCatalogoTablas.app` desde la carpeta `dist/` o desde los artefactos de GitHub Actions.
3. Haz doble clic para ejecutar. Si ves advertencia de seguridad, ve a Preferencias del Sistema → Seguridad y permite la app.
4. Para distribución profesional, firma la app con tu Apple ID.

---

Para pruebas de integración:

```bash
pytest tests/integration/
```

---

## Creación y Distribución Profesional de una App para macOS ##

Guía práctica y detallada para desarrollar, empaquetar, firmar, notarizar y distribuir una aplicación profesional para macOS a partir de un proyecto Python (ejemplo: EDFCatalogoTablas).

## Tabla de Contenidos Técnica ##

- [Catálogo de Tablas](#catálogo-de-tablas)
  - [🚀 Características Principales](#-características-principales)
  - [🛠️ Estructura del Proyecto](#️-estructura-del-proyecto)
  - [🚀 Instalación](#-instalación)
  - [📦 Dependencias Principales](#-dependencias-principales)
  - [🤖 Ejecución de Pruebas](#-ejecución-de-pruebas)
  - [🍏 Build y Despliegue de la App macOS EDFCatalogoTablas](#-build-y-despliegue-de-la-app-macos-edfcatalogotablas)
    - [Build Local Automático](#build-local-automático)
    - [Build Automático en GitHub Actions (CI)](#build-automático-en-github-actions-ci)
    - [Instrucciones para Usuarios Finales](#instrucciones-para-usuarios-finales)
  - [Creación y Distribución Profesional de una App para macOS](#creación-y-distribución-profesional-de-una-app-para-macos)
  - [Tabla de Contenidos Técnica](#tabla-de-contenidos-técnica)
  - [1. Requisitos Previos](#1-requisitos-previos)
  - [2. Preparación del Entorno de Desarrollo](#2-preparación-del-entorno-de-desarrollo)
  - [3. Empaquetado de la App (PyInstaller)](#3-empaquetado-de-la-app-pyinstaller)
    - [Recursos Estáticos y Plantillas](#recursos-estáticos-y-plantillas)
  - [4. Automatización del Build](#4-automatización-del-build)
    - [Script Bash (`build_mac_app.sh`)](#script-bash-build_mac_appsh)
    - [Automatización en CI (GitHub Actions)](#automatización-en-ci-github-actions)
  - [5. Firma de la App](#5-firma-de-la-app)
    - [a) Solicita tu Certificado](#a-solicita-tu-certificado)
    - [b) Firma la App](#b-firma-la-app)
    - [c) Verifica la Firma](#c-verifica-la-firma)
  - [6. Notarización con Apple](#6-notarización-con-apple)
    - [a) Comprime la App](#a-comprime-la-app)
    - [b) Sube a Notarización](#b-sube-a-notarización)
    - [c) Adjunta la Notarización ("staple")](#c-adjunta-la-notarización-staple)
  - [7. Creación de un Instalador DMG](#7-creación-de-un-instalador-dmg)
  - [8. Distribución y Buenas Prácticas](#8-distribución-y-buenas-prácticas)
  - [9. Recursos y Enlaces Útiles](#9-recursos-y-enlaces-útiles)
  - [📝 Guía de Contribución](#-guía-de-contribución)
  - [📄 Licencia](#-licencia)
  - [✨ Agradecimientos](#-agradecimientos)
- [🔒 Gestión de Archivos Sensibles y Restauración](#-gestión-de-archivos-sensibles-y-restauración)
  - [1. Archivos Sensibles Locales](#1-archivos-sensibles-locales)
  - [2. Archivos de Ejemplo](#2-archivos-de-ejemplo)
  - [3. Respaldo y Restauración Local](#3-respaldo-y-restauración-local)
  - [4. Tabla Resumen](#4-tabla-resumen)
  - [5. Recomendaciones](#5-recomendaciones)
  - [🧭 Cómo Generar y Mantener un Índice Automático en Markdown](#-cómo-generar-y-mantener-un-índice-automático-en-markdown)

## 1. Requisitos Previos ##

- **Apple ID** y [Apple Developer Program](https://developer.apple.com/programs/) (para firma y notarización)
- **Xcode** y Xcode Command Line Tools (`xcode-select --install`)
- **Python 3.10+**
- **Homebrew** ([instalar](https://brew.sh/))
- **PyInstaller** (`pip install pyinstaller`)
- (Opcional) [create-dmg](https://github.com/create-dmg/create-dmg) para crear DMG instalables

## 2. Preparación del Entorno de Desarrollo ##

1. **Clona el repositorio:**

   ```bash
   git clone https://github.com/edfrutos/edf_catalogotablas.git
   cd edf_catalogotablas
   ```

2. **Crea y activa un entorno virtual:**

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Instala las dependencias:**

   ```bash
   pip install -r requirements.txt
   ```

4. **Instala PyInstaller:**

   ```bash
   pip install pyinstaller
   ```

## 3. Empaquetado de la App (PyInstaller) ##

- Asegúrate de tener un archivo `.spec` bien configurado o usa el comando básico:

  ```bash
  pyinstaller --onefile --windowed app.py
  ```

- Para proyectos complejos, usa el archivo `edf_catalogotablas.spec` y ejecuta:

  ```bash
  pyinstaller edf_catalogotablas.spec
  ```

- El resultado estará en `dist/EDFCatalogoTablas.app`

### Recursos Estáticos y Plantillas ###

- Asegúrate de incluir todos los archivos necesarios (templates, static) en el `.spec` usando `datas=[...]`.
- [Documentación oficial PyInstaller](https://pyinstaller.org/en/stable/spec-files.html)

## 4. Automatización del Build ##

### Script Bash (`build_mac_app.sh`) ###

```bash
#!/bin/bash
set -e

echo "Limpiando builds anteriores..."
rm -rf build dist EDFCatalogoTablas.app

echo "Instalando dependencias..."
pip install -r requirements.txt

echo "Ejecutando PyInstaller..."
pyinstaller edf_catalogotablas.spec

echo "Build completado. El bundle está en dist/EDFCatalogoTablas.app"
```

### Automatización en CI (GitHub Actions) ###

- `.github/workflows/mac_build.yml`:

```yaml
name: Build macOS App

on:
  push:
    branches: [ master ]

jobs:
  build:
    runs-on: macos-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: pip install -r requirements.txt pyinstaller
      - name: Build App
        run: pyinstaller edf_catalogotablas.spec
      - name: Upload artifact
        uses: actions/upload-artifact@v3
        with:
          name: EDFCatalogoTablas.app
          path: dist/EDFCatalogoTablas.app
```

## 5. Firma de la App ##

### a) Solicita tu Certificado ###

- Desde [Apple Developer Certificates](https://developer.apple.com/account/resources/certificates/list), crea un certificado **Developer ID Application** y añádelo a tu llavero (Keychain Access).

### b) Firma la App ###

```bash
codesign --deep --force --verify --verbose \
  --sign "Developer ID Application: Tu Nombre (XXXXXXXXXX)" \
  dist/EDFCatalogoTablas.app
```

### c) Verifica la Firma ###

```bash
codesign --verify --deep --strict --verbose=2 dist/EDFCatalogoTablas.app
```

- Más info: [Apple Code Signing Guide](https://developer.apple.com/documentation/security/notarizing_macos_software_before_distribution)

## 6. Notarización con Apple ##

### a) Comprime la App ###

```bash
cd dist
zip -r EDFCatalogoTablas.zip EDFCatalogoTablas.app
```

### b) Sube a Notarización ###

```bash
xcrun notarytool submit EDFCatalogoTablas.zip \
  --apple-id "tu-email@apple.com" \
  --team-id "XXXXXXXXXX" \
  --password "app-specific-password" \
  --wait
```

- Genera una [contraseña específica de app](https://support.apple.com/en-us/HT204397).

### c) Adjunta la Notarización ("staple") ###

```bash
xcrun stapler staple EDFCatalogoTablas.app
```

- Más info: [Apple Notarization Guide](https://developer.apple.com/documentation/security/notarizing_macos_software_before_distribution)

## 7. Creación de un Instalador DMG ##

- Instala `create-dmg`:

  ```bash
  brew install create-dmg
  ```

- Crea el DMG:

  ```bash
  create-dmg dist/EDFCatalogoTablas.app
  ```

- [Guía create-dmg](https://github.com/create-dmg/create-dmg)

## 8. Distribución y Buenas Prácticas ##

- Comparte el `.dmg` o `.zip` firmado y notarizado.
- Incluye el archivo `LICENSE` (MIT, GPL, etc.) en el paquete.
- Proporciona instrucciones para usuarios sobre cómo permitir la app en Preferencias del Sistema si Gatekeeper la bloquea.
- Si distribuyes a gran escala, considera automatizar la subida a tu web o a servicios como AWS S3.

## 9. Recursos y Enlaces Útiles ##

- [Apple Developer Program](https://developer.apple.com/programs/)
- [Documentación oficial notarización](https://developer.apple.com/documentation/security/notarizing_macos_software_before_distribution)
- [PyInstaller Docs](https://pyinstaller.org/en/stable/)
- [create-dmg](https://github.com/create-dmg/create-dmg)
- [Automatización con GitHub Actions](https://docs.github.com/en/actions)
- [Soporte Apple: Contraseñas específicas de app](https://support.apple.com/en-us/HT204397)

---

**Autor:** Eugenio De Frutos Sánchez — 2025  
Licencia: MIT

## 📝 Guía de Contribución ##

1. Haz un fork del proyecto
2. Crea una rama para tu característica (`git checkout -b feature/AmazingFeature`)
3. Haz commit de tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Haz push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📄 Licencia ##

Este proyecto está bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para más detalles.

## ✨ Agradecimientos ##

- A todos los contribuyentes que han ayudado a mejorar este proyecto.
- A la comunidad de código abierto por las herramientas y bibliotecas utilizadas.

---

# 🔒 Gestión de Archivos Sensibles y Restauración #

Este proyecto **no incluye archivos sensibles ni credenciales reales** en el repositorio por seguridad. Para que la aplicación funcione correctamente después de clonar el proyecto, sigue estos pasos:

## 1. Archivos Sensibles Locales ##

> ⚠️ **Advertencia de seguridad:** Los archivos como `.env`, configuraciones con contraseñas, tokens, claves API, etc., **NO están en el repositorio**.
> Por seguridad, estos archivos están listados en `.gitignore` y nunca se suben a git.
> Si tienes un backup local (por ejemplo, en `sensitive_backup/`), puedes restaurar fácilmente tus archivos sensibles.

## 2. Archivos de Ejemplo ##

- El repositorio incluye archivos de ejemplo como `.env.example` o `config_debug_example.py`.
- Tras clonar, **copia el archivo de ejemplo y edítalo con tus datos reales**:

  ```sh
  cp .env.example .env
  # Edita .env y añade tus credenciales
  cp dev_template/tests/legacy/config_debug_example.py dev_template/tests/legacy/config_debug.py
  # Edita config_debug.py con tus credenciales
  ```

## 3. Respaldo y Restauración Local ##

- Puedes usar el script `tools/backup_sensitive_files.sh` para hacer un respaldo local de tus archivos sensibles:

  ```sh
  bash tools/backup_sensitive_files.sh
  # Esto crea sensitive_backup/ SOLO en tu máquina local
  ```

- **Nunca subas `sensitive_backup/` al repositorio** (ya está en `.gitignore`).
- Si necesitas restaurar tras una limpieza o pérdida accidental, copia los archivos desde `sensitive_backup/` a su ubicación original.

## 4. Tabla Resumen ##

| Archivo/directorio           | ¿Se sube a git? | ¿Se debe crear tras clonar? | ¿Es seguro para backup? |
|-----------------------------|:---------------:|:---------------------------:|:-----------------------:|
| `.env`                      | ❌              | ✅ (manual/copia ejemplo)    | Solo local/cifrado      |
| `sensitive_backup/`         | ❌              | ❌ (solo local, nunca remoto)| Solo local/cifrado      |
| `.env.example`              | ✅              | ✅ (para copiar estructura)  | Sí, sin datos reales    |
| `config_debug.py`           | ❌              | ✅ (manual/copia ejemplo)    | Solo local/cifrado      |
| `config_debug_example.py`   | ✅              | ✅ (estructura)              | Sí, sin datos reales    |

## 5. Recomendaciones ##

- **Nunca subas archivos sensibles al repositorio**.
- Haz backups cifrados de tus archivos sensibles fuera del proyecto (gestor de contraseñas, almacenamiento seguro, etc.).
- Si colaboras con otros, comparte solo los archivos de ejemplo y nunca los reales.
- Documenta cualquier archivo sensible nuevo que requiera el proyecto.

> ⚠️ **Recuerda:** Si subes accidentalmente un archivo sensible, **elimínalo de la historia de git** y cambia inmediatamente las credenciales expuestas.

---

## 🧭 Cómo Generar y Mantener un Índice Automático en Markdown ##

Un índice automático enlaza cada sección del documento con su título, facilitando la navegación. Markdown puro no lo genera automáticamente, pero existen herramientas y extensiones que lo hacen por ti.

**Herramientas Útiles:**

- **VSCode:**
    - Extensión [Markdown All in One](https://marketplace.visualstudio.com/items?itemName=yzhang.markdown-all-in-one): genera y actualiza el índice (TOC) con un clic.
- **GitHub:**
    - Los enlaces internos funcionan usando el slug del título (minúsculas, sin tildes, espacios a guion, sin signos). Ejemplo: `# Mi sección especial` → `#mi-seccion-especial`.
- **CLI:**
    - [doctoc](https://github.com/thlorenz/doctoc) o [markdown-toc](https://github.com/jonschlinkert/markdown-toc) generan índices desde terminal.

**Buenas Prácticas:**

- Usa títulos únicos y descriptivos.
- Mantén el índice actualizado tras añadir o mover secciones.
- Comprueba los enlaces tras cambios grandes.

**Ejemplo de Enlace Interno:**

```markdown
[Instalacion](#2-instalacion)
```

> 💡 *Recuerda: los slugs de GitHub eliminan tildes y caracteres especiales, y convierten espacios en guiones.*
