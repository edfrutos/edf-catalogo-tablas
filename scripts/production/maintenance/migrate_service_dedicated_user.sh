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
#   ./migrate_service_dedicated_user.sh check     # solo diagnostico, no cambia nada
#   ./migrate_service_dedicated_user.sh apply      # aplica la migracion
#   ./migrate_service_dedicated_user.sh rollback   # revierte al backup del unit file
#
# El modo "apply" aborta ANTES de tocar systemd si el usuario destino no
# puede ejecutar el interprete python del .venv (caso tipico: el .venv usa
# un python compilado con pyenv bajo /root/.pyenv, intransitable para un
# usuario no-root).

set -euo pipefail

SERVICE_NAME="catalogotablas.service"
APP_DIR="/var/www/vhosts/edefrutos2020.com/edf_catalogotablas"
SVC_USER="ede2020"
SVC_GROUP="psacln"
BACKUP_DIR="/root/catalogotablas-service-migration"

MODE="${1:-}"
if [[ "$MODE" != "check" && "$MODE" != "apply" && "$MODE" != "rollback" ]]; then
  echo "Uso: $0 {check|apply|rollback}" >&2
  exit 1
fi

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
run_apply() {
  run_check

  require_unit_path
  mkdir -p "$BACKUP_DIR"
  TS="$(date +%Y%m%d%H%M%S)"
  cp -a "$UNIT_PATH" "$BACKUP_DIR/$(basename "$UNIT_PATH").bak.$TS"
  log "Backup del unit file guardado en $BACKUP_DIR/$(basename "$UNIT_PATH").bak.$TS"

  log "Cambiando propietario de $APP_DIR a $SVC_USER:$SVC_GROUP"
  chown -R "$SVC_USER:$SVC_GROUP" "$APP_DIR"

  log "Prueba funcional: ¿puede $SVC_USER ejecutar el python del venv?"
  VENV_PY="$APP_DIR/.venv/bin/python3"
  if ! sudo -u "$SVC_USER" "$VENV_PY" -V; then
    echo "ABORTA: $SVC_USER no puede ejecutar $VENV_PY (probable pyenv bajo /root)." >&2
    echo "El unit file NO se ha tocado, el servicio sigue corriendo como antes." >&2
    echo "La propiedad de $APP_DIR ya quedo como $SVC_USER:$SVC_GROUP; eso no rompe nada" >&2
    echo "(root sigue pudiendo leer/ejecutar todo), pero soluciona esto antes de reintentar." >&2
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
  echo "Rollback aplicado. Nota: la propiedad de $APP_DIR se quedo en $SVC_USER:$SVC_GROUP;"
  echo "eso es inofensivo con el servicio corriendo de nuevo como root."
}

case "$MODE" in
  check) run_check ;;
  apply) run_apply ;;
  rollback) run_rollback ;;
esac
