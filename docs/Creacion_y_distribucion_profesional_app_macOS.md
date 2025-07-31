# Creación y distribución profesional de una app para macOS

Guía práctica y detallada para desarrollar, empaquetar, firmar, notarizar y distribuir una aplicación profesional para macOS a partir de un proyecto Python (ejemplo: EDFCatalogoTablas).

---

## Índice
1. [Requisitos previos](#requisitos-previos)
2. [Preparación del entorno de desarrollo](#preparación-del-entorno-de-desarrollo)
3. [Empaquetado de la app (PyInstaller)](#empaquetado-de-la-app-pyinstaller)
4. [Automatización del build](#automatización-del-build)
5. [Firma de la app](#firma-de-la-app)
6. [Notarización con Apple](#notarización-con-apple)
7. [Creación de un instalador DMG](#creación-de-un-instalador-dmg)
8. [Distribución y buenas prácticas](#distribución-y-buenas-prácticas)
9. [Recursos y enlaces útiles](#recursos-y-enlaces-útiles)

---

## 1. Requisitos previos

- **Apple ID** y [Apple Developer Program](https://developer.apple.com/programs/) (para firma y notarización)
- **Xcode** y Xcode Command Line Tools (`xcode-select --install`)
- **Python 3.10+**
- **Homebrew** ([instalar](https://brew.sh/))
- **PyInstaller** (`pip install pyinstaller`)
- (Opcional) [create-dmg](https://github.com/create-dmg/create-dmg) para crear DMG instalables

---

## 2. Preparación del entorno de desarrollo

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

---

## 3. Empaquetado de la app (PyInstaller)

- Asegúrate de tener un archivo `.spec` bien configurado o usa el comando básico:
  ```bash
  pyinstaller --onefile --windowed app.py
  ```
- Para proyectos complejos, usa el archivo `edf_catalogotablas.spec` y ejecuta:
  ```bash
  pyinstaller edf_catalogotablas.spec
  ```
- El resultado estará en `dist/EDFCatalogoTablas.app`

### Recursos estáticos y plantillas
- Asegúrate de incluir todos los archivos necesarios (templates, static) en el `.spec` usando `datas=[...]`.
- [Documentación oficial PyInstaller](https://pyinstaller.org/en/stable/spec-files.html)

---

## 4. Automatización del build

### Script Bash (`build_mac_app.sh`)
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

### Automatización en CI (GitHub Actions)
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

---

## 5. Firma de la app

### a) Solicita tu certificado
- Desde [Apple Developer Certificates](https://developer.apple.com/account/resources/certificates/list), crea un certificado **Developer ID Application** y añádelo a tu llavero (Keychain Access).

### b) Firma la app
```bash
codesign --deep --force --verify --verbose \
  --sign "Developer ID Application: Tu Nombre (XXXXXXXXXX)" \
  dist/EDFCatalogoTablas.app
```

### c) Verifica la firma
```bash
codesign --verify --deep --strict --verbose=2 dist/EDFCatalogoTablas.app
```

- Más info: [Apple Code Signing Guide](https://developer.apple.com/documentation/security/notarizing_macos_software_before_distribution)

---

## 6. Notarización con Apple

### a) Comprime la app
```bash
cd dist
zip -r EDFCatalogoTablas.zip EDFCatalogoTablas.app
```

### b) Sube a notarización
```bash
xcrun notarytool submit EDFCatalogoTablas.zip \
  --apple-id "tu-email@apple.com" \
  --team-id "XXXXXXXXXX" \
  --password "app-specific-password" \
  --wait
```
- Genera una [contraseña específica de app](https://support.apple.com/en-us/HT204397).

### c) Adjunta la notarización (“staple”)
```bash
xcrun stapler staple EDFCatalogoTablas.app
```

- Más info: [Apple Notarization Guide](https://developer.apple.com/documentation/security/notarizing_macos_software_before_distribution)

---

## 7. Creación de un instalador DMG

- Instala `create-dmg`:
  ```bash
  brew install create-dmg
  ```
- Crea el DMG:
  ```bash
  create-dmg dist/EDFCatalogoTablas.app
  ```
- [Guía create-dmg](https://github.com/create-dmg/create-dmg)

---

## 8. Distribución y buenas prácticas

- Comparte el `.dmg` o `.zip` firmado y notarizado.
- Incluye el archivo `LICENSE` (MIT, GPL, etc.) en el paquete.
- Proporciona instrucciones para usuarios sobre cómo permitir la app en Preferencias del Sistema si Gatekeeper la bloquea.
- Si distribuyes a gran escala, considera automatizar la subida a tu web o a servicios como AWS S3.

---

## 9. Recursos y enlaces útiles

- [Apple Developer Program](https://developer.apple.com/programs/)
- [Documentación oficial notarización](https://developer.apple.com/documentation/security/notarizing_macos_software_before_distribution)
- [PyInstaller Docs](https://pyinstaller.org/en/stable/)
- [create-dmg](https://github.com/create-dmg/create-dmg)
- [Automatización con GitHub Actions](https://docs.github.com/en/actions)
- [Soporte Apple: Contraseñas específicas de app](https://support.apple.com/en-us/HT204397)

---

**Autor:** Eugenio De Frutos Sanchez — 2025  
Licencia: MIT
