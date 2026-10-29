"""Conexión opcional con Google Drive para la edición de tienda.

Diseño:
- El usuario aporta su propio ``credentials.json`` (cliente OAuth de tipo «Aplicación de
  escritorio» creado en su proyecto de Google Cloud). La app no lleva secretos embebidos.
- Autorización con el flujo de aplicación instalada: PKCE + redirección a ``127.0.0.1``.
  El navegador del sistema abre la pantalla de Google; el código vuelve a un servidor
  temporal que solo escucha en loopback y se cierra al terminar o a los 3 minutos.
- Alcance mínimo ``drive.file``: la app solo ve los archivos que ella misma crea.
- Solo se usa ``requests`` (ya incluido en el paquete): sin librerías de Google adicionales.
- Nada sale de la máquina salvo lo que el usuario inicia (conectar o subir una copia) y va
  directamente a Google; el desarrollador no recibe nada.
- Los tokens se guardan en el contenedor de la app con permisos 0600 y nunca se registran.
"""

from __future__ import annotations

import base64
import hashlib
import json
import logging
import os
import secrets
import threading
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlencode, urlsplit

import requests
from requests import RequestException

logger = logging.getLogger(__name__)

SCOPE = "https://www.googleapis.com/auth/drive.file"
AUTH_URI = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URI = "https://oauth2.googleapis.com/token"
REVOKE_URI = "https://oauth2.googleapis.com/revoke"
DRIVE_FILES = "https://www.googleapis.com/drive/v3/files"
DRIVE_UPLOAD = "https://www.googleapis.com/upload/drive/v3/files"
CARPETA_DRIVE = "TablaTeca"
MAX_CREDENCIALES = 20_000
ESPERA_AUTORIZACION = 180  # segundos

_PAGINA_OK = (
    "<!doctype html><meta charset='utf-8'><title>TablaTeca</title>"
    "<body style='font-family:-apple-system,sans-serif;text-align:center;margin-top:15vh'>"
    "<h2>Listo</h2><p>Ya puedes cerrar esta pestaña y volver a TablaTeca.</p></body>"
)
_PAGINA_ERROR = (
    "<!doctype html><meta charset='utf-8'><title>TablaTeca</title>"
    "<body style='font-family:-apple-system,sans-serif;text-align:center;margin-top:15vh'>"
    "<h2>No se pudo conectar</h2><p>Vuelve a TablaTeca para ver el motivo.</p></body>"
)

_lock = threading.Lock()
_flujo: dict = {"esperando": False, "error": "", "url": "", "cancelar": None}


class DriveError(Exception):
    """Error con mensaje apto para mostrar al usuario (nunca incluye tokens)."""


class PermisoCaducado(DriveError):
    """El permiso (refresh token) ya no es válido: caducó o se revocó."""


# ------------------------------------------------------------------ almacenamiento
def directorio() -> str:
    explicito = os.environ.get("EDF_STORE_DRIVE_DIR")
    if explicito:
        path = explicito
    else:
        from app.utils.paths import user_data_dir

        path = os.path.join(user_data_dir(), "google_drive")
    os.makedirs(path, exist_ok=True)
    return path


def _ruta(nombre: str) -> str:
    return os.path.join(directorio(), nombre)


def _escribir_privado(ruta: str, contenido: str) -> None:
    """Escritura atómica con permisos 0600."""
    parcial = ruta + ".parte"
    fd = os.open(parcial, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(contenido)
    os.replace(parcial, ruta)
    os.chmod(ruta, 0o600)


def _leer_json(ruta: str) -> dict | None:
    try:
        with open(ruta, encoding="utf-8") as f:
            datos = json.load(f)
        return datos if isinstance(datos, dict) else None
    except (OSError, ValueError):
        return None


def _borrar(ruta: str) -> None:
    try:
        os.remove(ruta)
    except OSError:
        pass


# ------------------------------------------------------------------ credentials.json
def validar_credenciales(contenido: bytes) -> dict:
    """Devuelve {"client_id", "client_secret"} o lanza DriveError con el motivo."""
    if len(contenido) > MAX_CREDENCIALES:
        raise DriveError("El archivo es demasiado grande para ser un credentials.json.")
    try:
        datos = json.loads(contenido.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        raise DriveError("El archivo no es un JSON válido.") from None
    if not isinstance(datos, dict):
        raise DriveError("El archivo no tiene el formato de credentials.json.")
    if "installed" not in datos:
        if "web" in datos:
            raise DriveError(
                "Ese cliente es de tipo «Aplicación web». Crea uno de tipo «Aplicación de escritorio»."
            )
        raise DriveError("No es un credentials.json de Google (falta la sección «installed»).")
    cliente = datos["installed"]
    client_id = cliente.get("client_id") if isinstance(cliente, dict) else None
    client_secret = cliente.get("client_secret") if isinstance(cliente, dict) else None
    if not (isinstance(client_id, str) and client_id.endswith(".apps.googleusercontent.com")):
        raise DriveError("El client_id del archivo no es válido.")
    if not (isinstance(client_secret, str) and client_secret):
        raise DriveError("Falta el client_secret en el archivo.")
    return {"client_id": client_id, "client_secret": client_secret}


def guardar_credenciales(contenido: bytes) -> None:
    cliente = validar_credenciales(contenido)
    cancelar()
    _borrar(_ruta("token.json"))  # un cliente nuevo invalida la autorización anterior
    _escribir_privado(_ruta("credentials.json"), json.dumps({"installed": cliente}))


def _cliente() -> dict:
    datos = _leer_json(_ruta("credentials.json"))
    cliente = datos.get("installed") if datos else None
    if not isinstance(cliente, dict) or not cliente.get("client_id") or not cliente.get("client_secret"):
        raise DriveError("Primero sube tu credentials.json.")
    return cliente


def quitar_credenciales() -> None:
    desconectar()
    _borrar(_ruta("credentials.json"))


# ------------------------------------------------------------------ estado
def estado() -> dict:
    with _lock:
        esperando, error, url = _flujo["esperando"], _flujo["error"], _flujo["url"]
    token = _leer_json(_ruta("token.json"))
    return {
        "credenciales": _leer_json(_ruta("credentials.json")) is not None,
        "conectado": bool(token and token.get("refresh_token")),
        "esperando": esperando,
        "error": error,
        "url": url if esperando else "",
    }


# ------------------------------------------------------------------ autorización
def _pkce() -> tuple[str, str]:
    verificador = secrets.token_urlsafe(64)
    desafio = base64.urlsafe_b64encode(hashlib.sha256(verificador.encode("ascii")).digest())
    return verificador, desafio.decode("ascii").rstrip("=")


def _post_token(datos: dict) -> dict:
    try:
        r = requests.post(TOKEN_URI, data=datos, timeout=30)
    except RequestException:
        raise DriveError("No se pudo contactar con Google. Comprueba la conexión.") from None
    try:
        cuerpo = r.json()
    except ValueError:
        cuerpo = {}
    if r.status_code != 200:
        if cuerpo.get("error") == "invalid_grant":
            raise PermisoCaducado("La autorización ha caducado o se revocó. Vuelve a conectar con Google.")
        raise DriveError("Google rechazó la solicitud de autorización.")
    return cuerpo


def _guardar_token(cuerpo: dict, anterior: dict | None = None) -> None:
    refresh = cuerpo.get("refresh_token") or (anterior or {}).get("refresh_token")
    acceso = cuerpo.get("access_token")
    if not refresh or not acceso:
        raise DriveError("Google no devolvió el permiso permanente. Vuelve a conectar.")
    caduca = time.time() + int(cuerpo.get("expires_in", 3600)) - 30
    _escribir_privado(
        _ruta("token.json"),
        json.dumps({"refresh_token": refresh, "access_token": acceso, "expires_at": caduca}),
    )


def cancelar() -> None:
    with _lock:
        parar = _flujo["cancelar"]
        _flujo.update(esperando=False, url="", cancelar=None)
    if parar:
        parar.set()


def iniciar_autorizacion(abrir=webbrowser.open) -> str:
    """Prepara el servidor de retorno en loopback, abre el navegador y devuelve la URL."""
    cliente = _cliente()
    cancelar()
    verificador, desafio = _pkce()
    state = secrets.token_urlsafe(24)
    parar = threading.Event()

    class _Retorno(BaseHTTPRequestHandler):
        def do_GET(self):  # noqa: N802
            consulta = parse_qs(urlsplit(self.path).query)
            if "code" not in consulta and "error" not in consulta:
                self.send_response(404)
                self.end_headers()
                return  # p. ej. /favicon.ico: no es la respuesta de Google
            correcto, mensaje = False, ""
            if consulta.get("state", [""])[0] != state:
                mensaje = "La respuesta de Google no corresponde a esta solicitud."
            elif "error" in consulta:
                mensaje = "No concediste el acceso a Google Drive."
            else:
                try:
                    cuerpo = _post_token(
                        {
                            "code": consulta["code"][0],
                            "client_id": cliente["client_id"],
                            "client_secret": cliente["client_secret"],
                            "redirect_uri": redirect_uri,
                            "grant_type": "authorization_code",
                            "code_verifier": verificador,
                        }
                    )
                    if SCOPE not in str(cuerpo.get("scope", "")).split():
                        raise DriveError("No se concedió el permiso de Drive necesario.")
                    _guardar_token(cuerpo)
                    correcto = True
                except DriveError as exc:
                    mensaje = str(exc)
            with _lock:
                _flujo.update(esperando=False, error="" if correcto else mensaje, url="")
            pagina = (_PAGINA_OK if correcto else _PAGINA_ERROR).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(pagina)))
            self.end_headers()
            self.wfile.write(pagina)
            parar.set()

        def log_message(self, *args):  # la URL lleva el código: no se registra
            pass

    servidor = HTTPServer(("127.0.0.1", 0), _Retorno)
    servidor.timeout = 1
    redirect_uri = f"http://127.0.0.1:{servidor.server_address[1]}/"
    url = AUTH_URI + "?" + urlencode(
        {
            "client_id": cliente["client_id"],
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": SCOPE,
            "state": state,
            "code_challenge": desafio,
            "code_challenge_method": "S256",
            "access_type": "offline",
            "prompt": "consent",
        }
    )
    with _lock:
        _flujo.update(esperando=True, error="", url=url, cancelar=parar)

    def _servir():
        limite = time.time() + ESPERA_AUTORIZACION
        try:
            while not parar.is_set() and time.time() < limite:
                servidor.handle_request()
        finally:
            servidor.server_close()
            with _lock:
                if _flujo["cancelar"] is parar:
                    if _flujo["esperando"]:
                        _flujo["error"] = "Se agotó el tiempo de espera. Inténtalo de nuevo."
                    _flujo.update(esperando=False, url="", cancelar=None)

    threading.Thread(target=_servir, daemon=True, name="drive-oauth").start()
    try:
        abrir(url)
    except Exception:  # noqa: BLE001 - el usuario dispone del enlace manual
        logger.warning("No se pudo abrir el navegador automáticamente")
    return url


# ------------------------------------------------------------------ uso de la API
def _token_de_acceso() -> str:
    token = _leer_json(_ruta("token.json"))
    if not token or not token.get("refresh_token"):
        raise DriveError("Drive no está conectado.")
    if token.get("access_token") and float(token.get("expires_at", 0)) > time.time() + 60:
        return token["access_token"]
    cliente = _cliente()
    try:
        cuerpo = _post_token(
            {
                "client_id": cliente["client_id"],
                "client_secret": cliente["client_secret"],
                "refresh_token": token["refresh_token"],
                "grant_type": "refresh_token",
            }
        )
    except PermisoCaducado:
        _borrar(_ruta("token.json"))
        raise
    _guardar_token(cuerpo, anterior=token)
    return cuerpo["access_token"]


def _api(metodo: str, url: str, token: str, **kw):
    try:
        r = getattr(requests, metodo)(
            url, headers={"Authorization": f"Bearer {token}", **kw.pop("headers", {})}, **kw
        )
    except RequestException:
        raise DriveError("No se pudo contactar con Google Drive. Comprueba la conexión.") from None
    if r.status_code in (401, 403):
        raise DriveError("Google Drive rechazó el acceso. Vuelve a conectar la cuenta.")
    if r.status_code >= 400:
        raise DriveError(f"Google Drive devolvió un error ({r.status_code}).")
    return r


def _carpeta(token: str) -> str:
    r = _api(
        "get",
        DRIVE_FILES,
        token,
        params={
            "q": f"name = '{CARPETA_DRIVE}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false",
            "fields": "files(id)",
            "pageSize": 1,
        },
        timeout=30,
    )
    existentes = r.json().get("files", [])
    if existentes:
        return existentes[0]["id"]
    r = _api(
        "post",
        DRIVE_FILES,
        token,
        params={"fields": "id"},
        json={"name": CARPETA_DRIVE, "mimeType": "application/vnd.google-apps.folder"},
        timeout=30,
    )
    return r.json()["id"]


def subir(ruta: str, nombre: str) -> dict:
    """Sube ``ruta`` a la carpeta TablaTeca de Drive (subida reanudable en una sola petición)."""
    token = _token_de_acceso()
    carpeta = _carpeta(token)
    tamano = os.path.getsize(ruta)
    inicio = _api(
        "post",
        DRIVE_UPLOAD,
        token,
        params={"uploadType": "resumable", "fields": "id,name"},
        headers={
            "Content-Type": "application/json; charset=UTF-8",
            "X-Upload-Content-Type": "application/zip",
            "X-Upload-Content-Length": str(tamano),
        },
        data=json.dumps({"name": nombre, "parents": [carpeta]}),
        timeout=30,
    )
    destino = inicio.headers.get("Location")
    if not destino:
        raise DriveError("Google Drive no devolvió la dirección de subida.")
    with open(ruta, "rb") as f:
        r = _api(
            "put",
            destino,
            token,
            headers={"Content-Type": "application/zip"},
            data=f,
            timeout=(10, 900),
        )
    cuerpo = r.json()
    return {"id": cuerpo.get("id", ""), "name": cuerpo.get("name", nombre)}


def desconectar() -> None:
    """Revoca el permiso en Google (mejor esfuerzo) y borra el token local."""
    cancelar()
    token = _leer_json(_ruta("token.json"))
    if token and token.get("refresh_token"):
        try:
            requests.post(REVOKE_URI, data={"token": token["refresh_token"]}, timeout=15)
        except RequestException:
            logger.info("No se pudo revocar el permiso en Google; se borra solo el token local")
    _borrar(_ruta("token.json"))
