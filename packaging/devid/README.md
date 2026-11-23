# TablaTeca · descarga directa (Developer ID)

DMG de la edición de tienda (SQLite local, sin cuentas) para distribuirla fuera de la
Mac App Store: firmada con Developer ID, con Hardened Runtime, notarizada y grapada.
Es la que se descarga desde <https://efjdev.com/tablateca/>.

## Requisitos

- Mac con Apple silicon (el spec genera arm64; la app pide macOS 12 o posterior).
- `python3.10` (`brew install python@3.10`).
- Certificado *Developer ID Application* en el llavero.
- Perfil de `notarytool` guardado: `xcrun notarytool store-credentials <perfil> …`.

## Uso

```bash
DEV_ID=<SHA-1 del certificado> NOTARY=<perfil> packaging/devid/devid_dmg.sh
```

El resultado queda en `dist-devid/TablaTeca-<versión>.dmg`. La versión sale de
`MAS_MARKETING_VERSION` (por defecto `1.0`).

Usa el SHA-1 en `DEV_ID` (`security find-identity -v -p codesigning`): si hay dos
certificados con el mismo nombre, `codesign` falla con *ambiguous*.

## Qué hace

1. Crea o reutiliza `.venv-devid` e instala `requirements_python310.txt`.
2. Aparta el `.env` real y compila con uno sin secretos: el spec mete el `.env` dentro de
   la app. El original se restaura al terminar, también si algo falla.
3. Compila con `packaging/mas/TablaTeca_mas.spec` y comprueba que la app no lleva secretos.
4. Firma todos los binarios de dentro hacia fuera con `entitlements-devid.plist`.
5. Notariza y grapa la app.
6. Crea el DMG, lo firma, lo notariza y lo grapa.

## Diferencias con la edición de la Mac App Store

- Sin sandbox: los datos van a `~/Library/Application Support/EDF_Catalogo/tablateca.sqlite3`
  (en la tienda, al contenedor de la app).
- Hardened Runtime con dos excepciones que Python necesita: memoria ejecutable sin firmar
  y desactivar la validación de bibliotecas.
