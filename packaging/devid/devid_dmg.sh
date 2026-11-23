#!/usr/bin/env bash
# Genera el DMG de descarga directa de TablaTeca: edición de tienda (SQLite local, sin
# cuentas), firmada con Developer ID, con Hardened Runtime, notarizada y grapada.
#
# Uso (desde la raíz del repositorio, en un Mac con Apple silicon):
#   DEV_ID=<SHA-1 del certificado Developer ID Application> NOTARY=<perfil de notarytool> \
#     packaging/devid/devid_dmg.sh
#
# Variables opcionales:
#   MAS_MARKETING_VERSION  versión que se muestra (por defecto 1.0)
#   MAS_BUILD_NUMBER       número de build (por defecto 1)
#   PYTHON                 intérprete 3.10 para crear el entorno (por defecto python3.10)
#
# Resultado: dist-devid/TablaTeca-<versión>.dmg
#
# Notas:
# - El spec incluye el .env de la raíz dentro de la app. Durante la compilación el .env
#   real se aparta y se usa uno sin secretos; al terminar (o si algo falla) se restaura.
# - Sin sandbox, los datos van a ~/Library/Application Support/EDF_Catalogo/tablateca.sqlite3.
# - Usa el SHA-1 en DEV_ID: si hay dos certificados con el mismo nombre, codesign falla
#   con "ambiguous".
# Compatible con el bash 3.2 de macOS.
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

: "${DEV_ID:?Exporta DEV_ID con el SHA-1 del certificado Developer ID Application}"
: "${NOTARY:?Exporta NOTARY con el nombre del perfil de notarytool (xcrun notarytool store-credentials)}"
export MAS_MARKETING_VERSION="${MAS_MARKETING_VERSION:-1.0}"
export MAS_BUILD_NUMBER="${MAS_BUILD_NUMBER:-1}"
PYTHON="${PYTHON:-python3.10}"
ENT="$ROOT/packaging/devid/entitlements-devid.plist"
VENV="$ROOT/.venv-devid"
DIST="$ROOT/dist-devid"
APP="$DIST/TablaTeca.app"
DMG="$DIST/TablaTeca-${MAS_MARKETING_VERSION}.dmg"

WORK="$(mktemp -d)"
ENV_MOVED=0
cleanup() {
  if [ "$ENV_MOVED" = 1 ] && [ -f "$WORK/env.real" ]; then
    mv -f "$WORK/env.real" "$ROOT/.env"
    echo "    .env original restaurado"
  fi
  rm -rf "$WORK"
}
trap cleanup EXIT

firmar() {
  codesign --force --options runtime --timestamp --entitlements "$ENT" --sign "$DEV_ID" "$1"
}

echo "==> 0/6 Comprobaciones previas"
[ "$(uname -m)" = "arm64" ] || { echo "Hace falta un Mac con Apple silicon (el spec genera arm64)" >&2; exit 1; }
security find-identity -v -p codesigning | grep -q "$DEV_ID" \
  || { echo "No encuentro la identidad $DEV_ID en el llavero" >&2; exit 1; }
command -v "$PYTHON" >/dev/null || { echo "No encuentro $PYTHON (brew install python@3.10)" >&2; exit 1; }

echo "==> 1/6 Entorno Python ($VENV)"
[ -x "$VENV/bin/python" ] || "$PYTHON" -m venv "$VENV"
"$VENV/bin/python" -m pip install -q --upgrade pip
"$VENV/bin/python" -m pip install -q -r requirements_python310.txt
"$VENV/bin/python" -c "import pkg_resources, altgraph, PyInstaller" \
  || { echo "El entorno no puede importar PyInstaller (¿setuptools >= 81?)" >&2; exit 1; }

echo "==> 2/6 .env sin secretos durante la compilación"
if [ -f .env ]; then
  mv .env "$WORK/env.real"
  ENV_MOVED=1
fi
cat > .env <<'EOF'
FLASK_ENV=production
MONGODB_DB=edf_catalogotablas
DISABLE_MONITORING=false
TZ=Europe/Madrid
PYTHONPATH=.
EOF

echo "==> 3/6 Compilando con PyInstaller"
rm -rf "$DIST" "$ROOT/build-devid"
"$VENV/bin/python" -m PyInstaller packaging/mas/TablaTeca_mas.spec --clean --noconfirm \
  --distpath "$DIST" --workpath "$ROOT/build-devid"
rm -f .env
if [ "$ENV_MOVED" = 1 ]; then
  mv "$WORK/env.real" .env
  ENV_MOVED=0
fi
[ -x "$APP/Contents/MacOS/TablaTeca" ] || { echo "PyInstaller no generó $APP" >&2; exit 1; }
SECRETOS=0
while IFS= read -r -d '' f; do
  if grep -qE '^(MONGO_URI|SECRET_KEY|FLASK_SECRET_KEY|BREVO_|MAIL_PASSWORD|AWS_|GEMINI_API_KEY|GOOGLE_CLIENT_SECRET)' "$f"; then
    echo "Secretos en $f" >&2
    SECRETOS=1
  fi
done < <(find "$APP" -name .env -type f -print0)
[ "$SECRETOS" = 0 ] || { echo "Abortado: la app contiene secretos" >&2; exit 1; }

echo "==> 4/6 Firmando con Developer ID (de dentro hacia fuera)"
n=0
while IFS= read -r -d '' f; do
  if [ -d "$f" ]; then
    firmar "$f" >/dev/null; n=$((n + 1))
  elif file -b "$f" | grep -q 'Mach-O'; then
    firmar "$f" >/dev/null; n=$((n + 1))
  fi
done < <(find "$APP/Contents" -depth \( -type f -o -type d -name '*.framework' \) \
           ! -path "$APP/Contents/MacOS/TablaTeca" -print0)
echo "    $n elementos firmados"
firmar "$APP"
codesign --verify --deep --strict --verbose=2 "$APP"

echo "==> 5/6 Notarizando la app (tarda unos minutos)"
ditto -c -k --keepParent "$APP" "$WORK/app.zip"
xcrun notarytool submit "$WORK/app.zip" --keychain-profile "$NOTARY" --wait
xcrun stapler staple "$APP"
spctl -a -vvv -t exec "$APP"

echo "==> 6/6 DMG firmado y notarizado"
mkdir "$WORK/dmg"
ditto "$APP" "$WORK/dmg/TablaTeca.app"
ln -s /Applications "$WORK/dmg/Applications"
hdiutil create -volname "TablaTeca" -srcfolder "$WORK/dmg" -ov -format UDZO "$DMG"
codesign --force --timestamp --sign "$DEV_ID" "$DMG"
xcrun notarytool submit "$DMG" --keychain-profile "$NOTARY" --wait
xcrun stapler staple "$DMG"
spctl -a -vvv -t install "$DMG"
xcrun stapler validate "$DMG"
ls -lh "$DMG"
echo "Listo: $DMG"
