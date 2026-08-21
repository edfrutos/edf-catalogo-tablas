#!/bin/bash
# Migra catalogotablas.service de correr como root a correr como el usuario
# propio de la subscription de Plesk (ede2020:psacln), que ya es dueño de
# /var/www/vhosts/edefrutos2020.com/edf_catalogotablas (verificado con
# `ls -la /var/www/vhosts/edefrutos2020.com/`) y para el que Plesk ya sabe
# hacer backups correctamente (el backup de Plesk falla ahora mismo con
# "Permission denied" en flask_session/* porque esos ficheros los crea el
# servicio como root:root).
#
# OJO: no confundir con el directorio hermano
# catalogotablas.edefrutos2020.com (un vhost/subdominio aparte, casi vacio,
# propiedad de ede2020:psaserv) — ese "psaserv" NO es el grupo a usar aqui.
#
# Ejecutar como root en el servidor de produccion.
#
# Uso:
#   ./migrate_service_dedicated_user.sh check       # solo diagnostico, no cambia nada
#   ./migrate_service_dedicated_user.sh fix-pyenv   # abre paso minimo a /root/.pyenv/versions/<ver>
#   ./migrate_service_dedicated_user.sh apply        # aplica la migracion
#   ./migrate_service_dedicated_user.sh rollback     # revierte al backup del unit file
#
# El .venv de produccion usa un python compilado con pyenv bajo
# /root/.pyenv/versions/<ver> (build hecho en su dia como root), intransitable
# para un usuario no-root. "apply" corre "fix-pyenv" automaticamente antes de
# tocar systemd: abre solo TRAVESIA (chmod o+x, sin lectura) en la cadena
# /root -> .../.pyenv -> .../versions -> .../<ver>, y dentro de esa version
# concreta aplica lectura+travesia recursiva (chmod -R o+rX). No se toca nada
# mas de /root — sigue sin poderse listar ni leer nada fuera de esa ruta
# exacta, y sigue sin poder ESCRIBIRSE ahi. Si aun asi el usuario destino no
# puede ejecutar el interprete, "apply" aborta antes de tocar systemd.

set -euo pipefail

SERVICE_NAME="catalogotablas.service"
APP_DIR="/var/www/vhosts/edefrutos2020.com/edf_catalogotablas"
SVC_USER="ede2020"
SVC_GROUP="psacln"
BACKUP_DIR="/root/catalogotablas-service-migration"

MODE="${1:-}"
case "$MODE" in
  check|fix-pyenv|apply|rollback) ;;
  *)
    echo "Uso: $0 {check|fix-pyenv|apply|rollback}" >&2
    exit 1
    ;;
esac

if [[ $EUID -ne 0 ]]; then
  echo "Este script debe ejecutarse como root (necesita useradd/chown/systemctl)." >&2
  exit 1
fi

log() { echo -e "\n=== $* ==="; }

require_unit_path() {
  UNIT_PATH="$(systemctl show -p FragmentPath --value "$SERVICE_NAME" 2>/dev/null || true)"
  if [[ -z "$UNIT_PATH" || ! -f "$UNIT_PATH" ]]; then
    echo "No se pudo localizar el unit file de $SERVICE_NAME (systemctl show -p FragmentPath)." >&2
    exit 1
  fi
}

# ---------------------------------------------------------------------------
run_check() {
  log "Usuario/grupo destino"
  id "$SVC_USER" || { echo "El usuario $SVC_USER no existe. Aborta y revisa el nombre correcto."; exit 1; }

  require_unit_path
  log "Unit file: $UNIT_PATH"
  cat "$UNIT_PATH"

  log "Directiva User=/Group= actual en el unit"
  grep -E "^(User|Group)=" "$UNIT_PATH" || echo "(ninguna -> corre como root, el default de systemd)"

  log "Propietario actual de $APP_DIR (nivel superior)"
  stat -c '%U:%G %a %n' "$APP_DIR"

  log "Propietario de subdirectorios/ficheros con estado (logs, flask_session, app_data, uploads, .venv, .env)"
  for p in logs flask_session app_data app/static/uploads .venv .env; do
    if [[ -e "$APP_DIR/$p" ]]; then
      stat -c '%U:%G %a %n' "$APP_DIR/$p"
    else
      echo "(no existe) $APP_DIR/$p"
    fi
  done

  log "Resolucion del interprete python del venv"
  VENV_PY="$APP_DIR/.venv/bin/python3"
  if [[ -e "$VENV_PY" ]]; then
    REAL_PY="$(readlink -f "$VENV_PY")"
    echo "$VENV_PY -> $REAL_PY"
    if [[ "$REAL_PY" == /root/* ]]; then
      echo "AVISO: el interprete real vive bajo /root — un usuario no-root no podra"
      echo "atravesar ese directorio (permisos tipicos drwx------ de /root). Hay que"
      echo "resolver esto (mover/reinstalar pyenv en una ruta compartida, p.ej. /opt/pyenv)"
      echo "ANTES de lanzar 'apply', o el servicio no arrancara con el nuevo usuario."
    fi
  else
    echo "No existe $VENV_PY — revisa la ruta real del venv/ExecStart antes de continuar."
  fi

  log "EnvironmentFile= referenciado por el unit (si lo hay)"
  ENV_FILE_LINE="$(grep -E "^EnvironmentFile=" "$UNIT_PATH" || true)"
  if [[ -n "$ENV_FILE_LINE" ]]; then
    ENV_FILE_PATH="${ENV_FILE_LINE#EnvironmentFile=}"
    ENV_FILE_PATH="${ENV_FILE_PATH#-}"  # el prefijo '-' en systemd marca "opcional"
    echo "$ENV_FILE_LINE"
    [[ -e "$ENV_FILE_PATH" ]] && stat -c '%U:%G %a %n' "$ENV_FILE_PATH"
  else
    echo "(ninguno; probablemente usa $APP_DIR/.env vía load_dotenv() en el propio codigo)"
  fi

  log "Proceso actualmente escuchando en 127.0.0.1:5100"
  ss -ltnp 2>/dev/null | grep ":5100" || echo "(no se ve el proceso — ¿corre bajo otro puerto/systemd-run?)"

  log "Diagnostico completado. Revisa los avisos antes de correr 'apply'."
}

# ---------------------------------------------------------------------------
# Abre paso MINIMO bajo /root hasta el interprete real del venv:
#   - o+x (sin r) en /root, /root/.pyenv, /root/.pyenv/versions -> no listable,
#     solo atravesable si ya conoces la ruta exacta.
#   - o+rX recursivo SOLO dentro de /root/.pyenv/versions/<version> -> lectura
#     y ejecucion (donde ya la habia) del propio interprete/stdlib, nada mas
#     de /root queda expuesto.
# No toca permisos de escritura en ningun punto de la cadena.
fix_pyenv_access() {
  local venv_py="$APP_DIR/.venv/bin/python3"
  if [[ ! -e "$venv_py" ]]; then
    echo "No existe $venv_py — nada que hacer."
    return 0
  fi

  local real_py version_dir
  real_py="$(readlink -f "$venv_py")"
  if [[ "$real_py" != /root/* ]]; then
    echo "$venv_py -> $real_py (no vive bajo /root, no hace falta tocar nada)."
    return 0
  fi

  if [[ "$real_py" =~ ^(/root/\.pyenv/versions/[^/]+)/ ]]; then
    version_dir="${BASH_REMATCH[1]}"
  else
    echo "No reconozco el patron /root/.pyenv/versions/<version>/... en $real_py" >&2
    echo "Ajusta permisos a mano antes de continuar (revisa con: readlink -f $venv_py)." >&2
    return 1
  fi

  log "Abriendo paso minimo hasta $version_dir"
  local d="$version_dir" chain=()
  while [[ "$d" != "/" ]]; do
    chain+=("$d")
    d="$(dirname "$d")"
  done
  local i
  for ((i = ${#chain[@]} - 1; i >= 0; i--)); do
    if [[ "${chain[$i]}" == "$version_dir" ]]; then
      chmod -R o+rX "$version_dir"
    else
      chmod o+x "${chain[$i]}"
    fi
    stat -c '%a %n' "${chain[$i]}"
  done

  log "Verificando resultado"
  sudo -u "$SVC_USER" test -x "$real_py" && echo "OK: $SVC_USER puede atravesar hasta $real_py"
}

# ---------------------------------------------------------------------------
run_apply() {
  run_check

  require_unit_path
  mkdir -p "$BACKUP_DIR"
  TS="$(date +%Y%m%d%H%M%S)"
  cp -a "$UNIT_PATH" "$BACKUP_DIR/$(basename "$UNIT_PATH").bak.$TS"
  log "Backup del unit file guardado en $BACKUP_DIR/$(basename "$UNIT_PATH").bak.$TS"

  log "Cambiando propietario de $APP_DIR a $SVC_USER:$SVC_GROUP"
  chown -R "$SVC_USER:$SVC_GROUP" "$APP_DIR"

  fix_pyenv_access

  log "Prueba funcional: ¿puede $SVC_USER ejecutar el python del venv?"
  VENV_PY="$APP_DIR/.venv/bin/python3"
  if ! sudo -u "$SVC_USER" "$VENV_PY" -V; then
    echo "ABORTA: $SVC_USER no puede ejecutar $VENV_PY." >&2
    echo "El unit file NO se ha tocado, el servicio sigue corriendo como antes." >&2
    echo "La propiedad de $APP_DIR ya quedo como $SVC_USER:$SVC_GROUP; eso no rompe nada" >&2
    echo "(root sigue pudiendo leer/ejecutar todo), pero revisa el intercambio de pyenv" >&2
    echo "a mano (fix-pyenv ya se intento automaticamente) antes de reintentar." >&2
    exit 1
  fi

  if grep -qE "^\[Service\]" "$UNIT_PATH"; then
    if grep -qE "^User=" "$UNIT_PATH"; then
      sed -i "s/^User=.*/User=$SVC_USER/" "$UNIT_PATH"
    else
      sed -i "/^\[Service\]/a User=$SVC_USER" "$UNIT_PATH"
    fi
    if grep -qE "^Group=" "$UNIT_PATH"; then
      sed -i "s/^Group=.*/Group=$SVC_GROUP/" "$UNIT_PATH"
    else
      sed -i "/^\[Service\]/a Group=$SVC_GROUP" "$UNIT_PATH"
    fi
  else
    echo "ABORTA: el unit file no tiene seccion [Service] reconocible; editalo a mano." >&2
    exit 1
  fi

  log "Unit file actualizado"
  cat "$UNIT_PATH"

  log "Recargando systemd y reiniciando el servicio"
  systemctl daemon-reload
  systemctl restart "$SERVICE_NAME"
  sleep 2

  log "Estado del servicio"
  systemctl status "$SERVICE_NAME" --no-pager || true

  log "Comprobacion HTTP local"
  curl -s -o /dev/null -w "HTTP %{http_code}\n" http://127.0.0.1:5100/ || echo "curl fallo — revisa journalctl"

  log "Ultimas 50 lineas de journalctl"
  journalctl -u "$SERVICE_NAME" -n 50 --no-pager

  log "Si todo se ve bien, verifica tambien el proximo backup de Plesk (ya no deberia"
  echo "dar 'Permission denied' en flask_session/*). Si algo falla, corre:"
  echo "  $0 rollback"
}

# ---------------------------------------------------------------------------
run_rollback() {
  require_unit_path
  LATEST_BACKUP="$(ls -t "$BACKUP_DIR"/*.bak.* 2>/dev/null | head -n1 || true)"
  if [[ -z "$LATEST_BACKUP" ]]; then
    echo "No hay backup en $BACKUP_DIR — no hay nada que revertir automaticamente." >&2
    exit 1
  fi
  log "Restaurando $LATEST_BACKUP -> $UNIT_PATH"
  cp -a "$LATEST_BACKUP" "$UNIT_PATH"
  systemctl daemon-reload
  systemctl restart "$SERVICE_NAME"
  sleep 2
  systemctl status "$SERVICE_NAME" --no-pager || true
  echo "Rollback aplicado. Notas:"
  echo "- La propiedad de $APP_DIR se quedo en $SVC_USER:$SVC_GROUP; inofensivo con el"
  echo "  servicio de nuevo como root (root sigue accediendo a todo igual)."
  echo "- Si 'apply' llego a correr fix-pyenv, /root/.pyenv/versions/<ver> quedo con"
  echo "  o+rX (y sus directorios padre con o+x). Eso no compromete nada sensible (es"
  echo "  solo el propio interprete Python), pero si quieres revertirlo tambien:"
  echo "    chmod o-x /root /root/.pyenv /root/.pyenv/versions"
  echo "    chmod -R o-rwx /root/.pyenv/versions/<ver>"
}

case "$MODE" in
  check) run_check ;;
  fix-pyenv) fix_pyenv_access ;;
  apply) run_apply ;;
  rollback) run_rollback ;;
esac
