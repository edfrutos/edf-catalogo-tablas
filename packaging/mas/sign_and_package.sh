#!/usr/bin/env bash
# Firma TablaTeca.app para la Mac App Store y genera el .pkg firmado.
#
# Uso:
#   packaging/mas/sign_and_package.sh <TablaTeca.app> <salida.pkg>
#
# Variables de entorno (modo real):
#   APP_SIGN_IDENTITY        SHA-1 o nombre de "Apple Distribution: ..."
#   INSTALLER_SIGN_IDENTITY  nombre de "3rd Party Mac Developer Installer: ..."
#   PROVISIONING_PROFILE     ruta al .provisionprofile (Mac App Store Connect)
#   KEYCHAIN_PATH            (opcional) llavero donde están las identidades
#
# Modo de prueba sin secretos (lo usan las PRs):
#   MAS_AD_HOC=1             firma ad hoc, sin perfil y sin firmar el .pkg.
#                            Sirve para comprobar la estructura del bundle,
#                            los entitlements y productbuild, no para subir.
#
# Compatible con bash 3.2 (el de macOS).
set -Eeuo pipefail

# En GitHub Actions los logs no siempre son accesibles: el fallo se publica
# también como anotación (inocua fuera de Actions, solo imprime una línea).
trap 'echo "::error title=sign_and_package.sh::falló en la línea $LINENO: ${BASH_COMMAND}"' ERR

# Ejecuta un comando y, si falla, publica su salida como anotación.
run_annotated() {
  local out
  if ! out="$("$@" 2>&1)"; then
    echo "$out"
    echo "::error title=$1 falló::${out//$'\n'/%0A}"
    return 1
  fi
  [ -n "$out" ] && echo "$out"
  return 0
}

APP_PATH="${1:?Uso: sign_and_package.sh <TablaTeca.app> <salida.pkg>}"
PKG_PATH="${2:?Uso: sign_and_package.sh <TablaTeca.app> <salida.pkg>}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AD_HOC="${MAS_AD_HOC:-0}"

[ -d "$APP_PATH" ] || { echo "No existe $APP_PATH" >&2; exit 1; }
APP_PATH="${APP_PATH%/}"

INFO_PLIST="$APP_PATH/Contents/Info.plist"
PLISTBUDDY=/usr/libexec/PlistBuddy
BUNDLE_ID="$($PLISTBUDDY -c 'Print :CFBundleIdentifier' "$INFO_PLIST")"
MAIN_EXEC="$($PLISTBUDDY -c 'Print :CFBundleExecutable' "$INFO_PLIST")"

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

if [ "$AD_HOC" = "1" ]; then
  echo "⚠️  Modo ad hoc: el resultado NO sirve para subirlo a App Store Connect"
  APP_SIGN_IDENTITY="-"
  TS_FLAG="--timestamp=none"
  TEAM_ID="TEAMID0000"
  APP_ID="$TEAM_ID.$BUNDLE_ID"
else
  : "${APP_SIGN_IDENTITY:?Falta APP_SIGN_IDENTITY}"
  : "${INSTALLER_SIGN_IDENTITY:?Falta INSTALLER_SIGN_IDENTITY}"
  : "${PROVISIONING_PROFILE:?Falta PROVISIONING_PROFILE}"
  [ -f "$PROVISIONING_PROFILE" ] || { echo "No existe el perfil $PROVISIONING_PROFILE" >&2; exit 1; }
  TS_FLAG="--timestamp"

  echo "📄 Leyendo el perfil de aprovisionamiento..."
  # security cms es lo habitual; openssl smime sirve de alternativa si falla
  if ! cms_err="$(security cms -D -i "$PROVISIONING_PROFILE" 2>&1 >"$WORK/profile.plist")"; then
    echo "⚠️  security cms falló: $cms_err"
    if ! ossl_err="$(openssl smime -inform der -verify -noverify -in "$PROVISIONING_PROFILE" -out "$WORK/profile.plist" 2>&1)"; then
      detalle="security cms: ${cms_err}
openssl smime: ${ossl_err}
tamaño: $(wc -c < "$PROVISIONING_PROFILE") bytes
tipo: $(file -b "$PROVISIONING_PROFILE")"
      echo "::error title=No se pudo leer el perfil de aprovisionamiento::${detalle//$'\n'/%0A}"
      exit 1
    fi
  fi
  APP_ID="$($PLISTBUDDY -c 'Print :Entitlements:com.apple.application-identifier' "$WORK/profile.plist")"
  TEAM_ID="$($PLISTBUDDY -c 'Print :Entitlements:com.apple.developer.team-identifier' "$WORK/profile.plist")"
  if [ "$APP_ID" != "$TEAM_ID.$BUNDLE_ID" ]; then
    echo "🛑 El perfil es para '$APP_ID' pero el bundle es '$TEAM_ID.$BUNDLE_ID'" >&2
    exit 1
  fi
  echo "   Equipo: $TEAM_ID · App: $APP_ID"

  # El perfil solo vale para los certificados que contiene: si la identidad de
  # firma no está entre ellos, Apple rechaza el paquete (error 90284).
  if printf '%s' "$APP_SIGN_IDENTITY" | grep -qE '^[0-9A-Fa-f]{40}$'; then
    WANT_SHA="$(printf '%s' "$APP_SIGN_IDENTITY" | tr 'a-f' 'A-F')"
    FOUND=0
    LISTA=""
    n=0
    while $PLISTBUDDY -c "Print :DeveloperCertificates:$n" "$WORK/profile.plist" > "$WORK/devcert.der" 2>/dev/null; do
      sha="$(shasum -a 1 "$WORK/devcert.der" | awk '{ print toupper($1) }')"
      info="$(openssl x509 -inform der -in "$WORK/devcert.der" -noout -subject -enddate 2>/dev/null | tr '\n' ' ')"
      echo "   Certificado #$n del perfil: $sha $info"
      LISTA="${LISTA}#$n $sha $info
"
      [ "$sha" = "$WANT_SHA" ] && FOUND=1
      n=$((n + 1))
    done
    if [ "$FOUND" != 1 ]; then
      detalle="Identidad de firma usada: $WANT_SHA
Certificados que contiene el perfil:
$LISTA"
      echo "::error title=El perfil no contiene el certificado de firma::${detalle//$'\n'/%0A}"
      exit 1
    fi
    echo "   ✔ El certificado de firma está en el perfil"
  fi
  cp "$PROVISIONING_PROFILE" "$APP_PATH/Contents/embedded.provisionprofile"
fi

KEYCHAIN_ARGS=()
if [ -n "${KEYCHAIN_PATH:-}" ]; then
  KEYCHAIN_ARGS=(--keychain "$KEYCHAIN_PATH")
fi

# --- Entitlements finales ---------------------------------------------------
MAIN_ENT="$WORK/entitlements-main.plist"
CHILD_ENT="$HERE/entitlements-mas-child.plist"
cp "$HERE/entitlements-mas.plist" "$MAIN_ENT"
$PLISTBUDDY -c "Add :com.apple.application-identifier string $APP_ID" "$MAIN_ENT"
$PLISTBUDDY -c "Add :com.apple.developer.team-identifier string $TEAM_ID" "$MAIN_ENT"

sign() {
  run_annotated codesign --force "$TS_FLAG" --sign "$APP_SIGN_IDENTITY" \
    ${KEYCHAIN_ARGS[@]+"${KEYCHAIN_ARGS[@]}"} "$@"
}

# Ordena rutas de más profunda a menos (se firma de dentro hacia fuera)
deepest_first() {
  awk '{ print length($0) "\t" $0 }' | sort -rn | cut -f2-
}

# --- 1. Mach-O sueltos (bibliotecas y ejecutables anidados) -------------------
echo "🔏 Firmando binarios anidados..."
MAIN_EXEC_PATH="$APP_PATH/Contents/MacOS/$MAIN_EXEC"
LIBS=0
EXECS=0
while IFS= read -r f; do
  [ "$f" = "$MAIN_EXEC_PATH" ] && continue
  kind="$(file -b "$f")"
  case "$kind" in
    *Mach-O*executable*)
      sign --entitlements "$CHILD_ENT" "$f"
      EXECS=$((EXECS + 1))
      ;;
    *Mach-O*)
      sign "$f"
      LIBS=$((LIBS + 1))
      ;;
  esac
done < <(find "$APP_PATH" -type f -print | deepest_first)
echo "   bibliotecas: $LIBS · ejecutables anidados: $EXECS"

# --- 2. Bundles anidados (frameworks, helpers) ------------------------------
echo "🔏 Firmando bundles anidados..."
while IFS= read -r d; do
  sign "$d"
done < <(find "$APP_PATH" -mindepth 1 -type d \
           \( -name '*.framework' -o -name '*.app' -o -name '*.xpc' -o -name '*.bundle' \) \
           -print | deepest_first)

# --- 3. La app principal con sus entitlements -------------------------------
echo "🔏 Firmando $APP_PATH..."
sign --entitlements "$MAIN_ENT" "$APP_PATH"

echo "🔍 Verificando la firma..."
run_annotated codesign --verify --deep --strict --verbose=2 "$APP_PATH"
codesign -d --entitlements :- "$APP_PATH" 2>/dev/null > "$WORK/final-entitlements.plist" || true
if ! grep -q 'com.apple.security.app-sandbox' "$WORK/final-entitlements.plist"; then
  echo "🛑 La app firmada no lleva el entitlement de sandbox" >&2
  exit 1
fi
echo "   Entitlements aplicados a la app principal:"
sed 's/^/   | /' "$WORK/final-entitlements.plist"

# --- 4. Paquete instalable ---------------------------------------------------
echo "📦 Creando $PKG_PATH..."
rm -f "$PKG_PATH"
if [ "$AD_HOC" = "1" ]; then
  run_annotated productbuild --component "$APP_PATH" /Applications "$PKG_PATH"
else
  run_annotated productbuild --component "$APP_PATH" /Applications \
    --sign "$INSTALLER_SIGN_IDENTITY" \
    ${KEYCHAIN_ARGS[@]+"${KEYCHAIN_ARGS[@]}"} \
    "$PKG_PATH"
  run_annotated pkgutil --check-signature "$PKG_PATH"
fi

echo "✅ Listo: $PKG_PATH"
