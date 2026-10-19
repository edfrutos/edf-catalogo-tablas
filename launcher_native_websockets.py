#!/usr/bin/env python3
"""
Lanzador nativo para EDF Catálogo de Tablas
Ejecuta la aplicación web Flask en una ventana nativa de macOS
con soporte para WebSockets en tiempo real
"""

import os
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path

import requests
import webview


class _EdfApi:
    """API JS -> Python expuesta a la ventana pywebview (enlaces externos y guardado de archivos)."""

    def open_external(self, url):
        import webbrowser
        from urllib.parse import urlparse
        if urlparse(str(url)).scheme not in ("http", "https"):
            return False
        webbrowser.open(str(url))
        return True

    def save_file(self, url, filename=""):
        import os
        import shutil
        import urllib.request
        from urllib.parse import urlparse, unquote
        import webview

        p = urlparse(str(url))
        if p.scheme != "http" or p.hostname not in ("127.0.0.1", "localhost"):
            return False
        name = os.path.basename(unquote(filename or p.path)) or "archivo"
        if not webview.windows:
            return False
        fd = getattr(webview, "FileDialog", None)
        dialog = fd.SAVE if fd is not None else webview.SAVE_DIALOG
        dest = webview.windows[0].create_file_dialog(dialog, save_filename=name)
        if not dest:
            return False
        dest = dest if isinstance(dest, str) else dest[0]
        with urllib.request.urlopen(str(url), timeout=300) as r, open(dest, "wb") as f:
            shutil.copyfileobj(r, f)
        return True

# Cargar variables de entorno desde el .env empaquetado en la propia app.
# Ruta explícita (en vez de load_dotenv() a secas): sin esto, python-dotenv
# busca .env subiendo desde el directorio de trabajo del proceso, así que si
# se lanza el ejecutable desde una carpeta que tenga su propio .env por
# encima (p.ej. un clon del repo en el disco de quien lo prueba), ese .env
# ajeno pisa (override=True) la configuración real empaquetada en el .app.
try:
    from dotenv import load_dotenv

    if getattr(sys, "frozen", False):
        _app_root = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    else:
        _app_root = os.path.dirname(os.path.abspath(__file__))
    _env_path = os.path.join(_app_root, ".env")

    _user_env = Path.home() / "Library" / "Application Support" / "EDF_Catalogo" / ".env"
    if getattr(sys, "frozen", False) and _user_env.is_file():
        _env_path = str(_user_env)  # .env del usuario, fuera del bundle firmado
    load_dotenv(_env_path, override=True)  # pyright: ignore[reportUnusedCallResult]
    print(f"✅ Variables de entorno cargadas desde {_env_path}")
except ImportError:
    print("⚠️  python-dotenv no disponible, usando variables de entorno del sistema")
except Exception as e:
    print(f"⚠️  Error al cargar .env: {e}")

# Configurar directorios escribibles ANTES de cualquier importación
if getattr(sys, "frozen", False):
    # Estamos en una aplicación empaquetada
    # Convención macOS: los logs van a ~/Library/Logs/<App> (visibles en Consola.app)
    log_dir = Path.home() / "Library" / "Logs" / "EDF_Catalogo"
    log_dir.mkdir(parents=True, exist_ok=True)
    os.environ["LOG_DIR"] = str(log_dir)
    os.environ["FLASK_LOG_DIR"] = str(log_dir)
    print(f"📝 Directorio de logs configurado: {log_dir}")
    # Nota: las sesiones de Flask no se configuran aquí. En modo empaquetado las fija
    # app/extensions.py (writable_dir -> ~/Library/Application Support/EDF_Catalogo/flask_session).

    # Configurar entorno de producción
    os.environ["FLASK_ENV"] = "production"
    os.environ["FLASK_DEBUG"] = "0"
    print("🔧 Configurado entorno de producción")
    # Desde Finder el cwd es "/" (solo lectura): las rutas relativas ("logs"...) fallaban
    _work_dir = Path.home() / "Library" / "Application Support" / "EDF_Catalogo"
    _work_dir.mkdir(parents=True, exist_ok=True)
    os.chdir(_work_dir)
    print(f"📂 Directorio de trabajo: {_work_dir}")


# Cadenas de la interfaz nativa (diálogo de cierre, menús de macOS) en español.
# Claves definidas en webview/localization.py de pywebview 6.x.
_ES_STRINGS = {
    "global.quitConfirmation": "¿Seguro que quieres salir?",
    "global.ok": "Aceptar",
    "global.quit": "Salir",
    "global.cancel": "Cancelar",
    "global.saveFile": "Guardar archivo",
    "cocoa.menu.about": "Acerca de",
    "cocoa.menu.services": "Servicios",
    "cocoa.menu.view": "Visualización",
    "cocoa.menu.edit": "Edición",
    "cocoa.menu.hide": "Ocultar",
    "cocoa.menu.hideOthers": "Ocultar otros",
    "cocoa.menu.showAll": "Mostrar todo",
    "cocoa.menu.quit": "Salir de",
    "cocoa.menu.fullscreen": "Entrar en pantalla completa",
    "cocoa.menu.cut": "Cortar",
    "cocoa.menu.copy": "Copiar",
    "cocoa.menu.paste": "Pegar",
    "cocoa.menu.selectAll": "Seleccionar todo",
}


PORT = 5004  # fijo a propósito: cambiar de puerto cambia el origen y se perderían cookies y localStorage


def _port_is_free(port=PORT):
    """True si nadie escucha en 127.0.0.1:port (evita hablar con un servidor ajeno)."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        return sock.connect_ex(("127.0.0.1", port)) != 0


def _show_error(message):
    """Diálogo nativo de macOS (aún no hay ventana pywebview); si falla, solo consola."""
    print(f"❌ {message}")
    if sys.platform == "darwin":
        script = (
            'display dialog (system attribute "EDF_MSG") with title '
            '"EDF Catálogo de Tablas" buttons {"Aceptar"} default button 1 with icon stop'
        )
        try:
            subprocess.run(
                ["osascript", "-e", script],
                env={**os.environ, "EDF_MSG": message},
                timeout=120,
                check=False,
            )
        except Exception:
            pass


def start_flask_server():
    """Inicia el servidor Flask en segundo plano"""
    try:
        from wsgi import app

        # Configuración específica para pywebview
        app.config.update(
            {
                "SESSION_COOKIE_SECURE": False,  # HTTP en 127.0.0.1 (sin TLS)
                "SESSION_COOKIE_HTTPONLY": True,  # No accesible desde JavaScript
                "SESSION_COOKIE_SAMESITE": "Lax",
                "SESSION_COOKIE_DOMAIN": None,  # Sin dominio específico
                "SESSION_COOKIE_PATH": "/",  # Ruta de la cookie
                "PERMANENT_SESSION_LIFETIME": 14400,  # 4 horas
            }
        )

        app.run(
            debug=False, port=PORT, host="127.0.0.1", use_reloader=False, threaded=True
        )
    except Exception as e:
        print(f"❌ Error al iniciar el servidor Flask: {e}")
        sys.exit(1)


def wait_for_server():
    """Espera a que el servidor Flask esté listo"""
    max_attempts = 30
    for attempt in range(max_attempts):
        try:
            response = requests.get(f"http://127.0.0.1:{PORT}", timeout=1)
            if response.status_code in [200, 302]:
                print(f"✅ Servidor Flask listo (intento {attempt + 1})")
                return True
        except requests.exceptions.RequestException:
            pass

        time.sleep(1)
        if attempt % 5 == 0:
            print(
                # pyright: ignore[reportImplicitStringConcatenation]
                f"⏳ Esperando servidor Flask... "
                f"(intento {attempt + 1}/{max_attempts})"
            )

    print("❌ Timeout esperando al servidor Flask")
    return False


def main():
    """Función principal de la aplicación"""
    print("🚀 Iniciando EDF Catálogo de Tablas (Aplicación Nativa WebSockets)")
    print("=" * 60)

    if not _port_is_free():
        _show_error(
            f"El puerto {PORT} ya está en uso. Probablemente hay otra copia de la "
            "aplicación abierta (o un servidor local). Ciérrala e inténtalo de nuevo."
        )
        sys.exit(1)

    # Iniciar el servidor Flask en un hilo separado
    server_thread = threading.Thread(target=start_flask_server)
    server_thread.daemon = True
    server_thread.start()

    # Esperar a que el servidor esté listo
    print("⏳ Iniciando servidor Flask...")
    if not wait_for_server():
        print("❌ No se pudo conectar al servidor Flask")
        sys.exit(1)

    try:
        # Crear la ventana nativa
        print("🖥️  Creando ventana nativa...")

        # Configuración básica para pywebview
        window_config = {
            "title": "EDF Catálogo de Tablas",
            "url": f"http://127.0.0.1:{PORT}",
            "width": 1400,
            "height": 900,
            "resizable": True,
            "min_size": (800, 600),
            "text_select": True,
            "confirm_close": True,
            # Se pasa a create_window (no a start): cada ventana copia las cadenas al crearse
            "localization": _ES_STRINGS,
        }

        # Crear la ventana nativa
        webview.create_window(
            **window_config, js_api=_EdfApi()
        )  # pyright: ignore[reportUnusedCallResult]

        print("✅ Ventana nativa creada")
        print("🖥️  Aplicación web ejecutándose en ventana nativa")
        print("🌐 WebSockets habilitados para comunicación en tiempo real")
        print("🛑 Cierra la ventana para salir")
        print("-" * 60)

        # Iniciar la aplicación con configuración mejorada
        # private_mode=False: WebKit conserva cookies y localStorage entre arranques
        # (por defecto pywebview es privado y pedía login en cada apertura).
        # En macOS pywebview usa el almacén por defecto de WebKit y no usa storage_path.
        webview.start(  # pyright: ignore[reportArgumentType]
            debug=os.environ.get("EDF_WEBVIEW_DEBUG") == "1",
            gui="native",
            private_mode=False,
        )

    except Exception as e:
        print(f"❌ Error al crear la ventana nativa: {e}")
        print("🔄 Intentando abrir en navegador como fallback...")

        # Fallback: abrir en navegador
        import webbrowser

        webbrowser.open(
            f"http://127.0.0.1:{PORT}"
        )  # pyright: ignore[reportUnusedCallResult]

        # Mantener el servidor corriendo
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Aplicación detenida")


if __name__ == "__main__":
    main()
