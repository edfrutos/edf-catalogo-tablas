# Script: launcher.py
# Descripción: [Explica brevemente qué hace el script]
# Uso: python3 launcher.py [opciones]
# Requiere: [librerías externas, si aplica]
# Variables de entorno: [si aplica]
# Autor: [Tu nombre o equipo] - 2025-06-28

import sys
import os
import threading
import time
import socket
import logging
import traceback

# Configurar logging básico
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("launcher")

# Verificar si estamos en un ejecutable congelado
if getattr(sys, "frozen", False):
    # Estamos en un ejecutable
    base_path = os.path.dirname(sys.executable)
    # Para aplicaciones empaquetadas, necesitamos ir al directorio Resources
    if os.path.basename(base_path) == "MacOS":
        base_path = os.path.join(os.path.dirname(base_path), "..", "Resources")
        # Verificar que la ruta existe
        if not os.path.exists(base_path):
            # Intentar ruta alternativa
            base_path = os.path.join(
                os.path.dirname(os.path.dirname(base_path)), "Resources"
            )
    logger.info(f"Ejecutándose como aplicación empaquetada desde: {base_path}")
else:
    # Estamos en desarrollo
    base_path = os.path.dirname(os.path.abspath(__file__))
    logger.info(f"Ejecutándose en modo desarrollo desde: {base_path}")

# Configurar directorio de trabajo
os.chdir(base_path)
logger.info(f"Directorio de trabajo configurado: {os.getcwd()}")

# Configurar directorio de logs
logs_dir = os.path.join(base_path, "logs")
try:
    os.makedirs(logs_dir, exist_ok=True)
    log_file = os.path.join(logs_dir, "launcher.log")

    # Configurar logging a archivo
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.INFO)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    logger.info("Sistema de logging configurado correctamente")
except Exception as e:
    logger.warning(f"No se pudo configurar logging a archivo: {e}")

# Importar módulos necesarios
try:
    import webview

    logger.info(f"PyWebView importado correctamente")
except ImportError as e:
    logger.error(f"Error importando PyWebView: {e}")
    sys.exit(1)

try:
    from main_app import app

    logger.info("main_app importado correctamente")
except ImportError as e:
    logger.error(f"Error importando main_app: {e}")
    sys.exit(1)

# Configurar GUI para macOS
if sys.platform == "darwin":
    os.environ["PYWEBVIEW_GUI"] = "cocoa"
    logger.info("Configurado PYWEBVIEW_GUI=cocoa para macOS")


def find_free_port(default_port=5000):
    """Encuentra un puerto libre para Flask"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind(("127.0.0.1", default_port))
        sock.close()
        return default_port
    except OSError:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
        sock.close()
        return port


def run_flask(port):
    """Ejecuta el servidor Flask"""
    try:
        logger.info(f"Iniciando Flask en puerto {port}")
        app.run(
            host="127.0.0.1", port=port, threaded=True, debug=False, use_reloader=False
        )
    except Exception as e:
        logger.error(f"Error al iniciar Flask: {e}")
        logger.error(traceback.format_exc())


def main():
    """Función principal"""
    try:
        logger.info("Iniciando aplicación EDF CatálogoDeTablas...")

        # Encontrar puerto libre
        port = find_free_port()
        logger.info(f"Puerto seleccionado: {port}")

        # Iniciar Flask en un hilo separado
        flask_thread = threading.Thread(target=run_flask, args=(port,), daemon=True)
        flask_thread.start()
        logger.info("Hilo de Flask iniciado")

        # Esperar a que Flask esté listo
        time.sleep(3)
        logger.info("Esperando a que Flask esté listo...")

        # Crear ventana webview
        logger.info("Creando ventana webview...")

        # Determinar el icono a usar
        icon_path = None
        possible_icons = [
            "app/static/favicon.icns",
            "app/static/favicon.ico",
            "app/static/icon.icns",
            "app/static/icon.ico",
        ]

        for icon in possible_icons:
            if os.path.exists(icon):
                icon_path = icon
                logger.info(f"Icono encontrado: {icon_path}")
                break

        if not icon_path:
            logger.warning("No se encontró ningún icono")

        # Configuración de tamaño de ventana
        # Detectar si estamos ejecutando desde terminal o como app empaquetada
        is_frozen = getattr(sys, "frozen", False)

        if is_frozen:
            # Aplicación empaquetada: usar tamaño más grande para compensar
            WINDOW_WIDTH = 1900  # Más grande para compensar el factor de escala
            WINDOW_HEIGHT = 1200  # Más grande para compensar el factor de escala
            logger.info(
                f"Modo aplicación empaquetada: usando tamaño {WINDOW_WIDTH}x{WINDOW_HEIGHT}"
            )
        else:
            # Ejecutando desde terminal: usar tamaño ajustado para PyWebView
            WINDOW_WIDTH = 1848  # Resultará en ~1680 píxeles
            WINDOW_HEIGHT = 1155  # Resultará en ~1050 píxeles
            logger.info(
                f"Modo desarrollo: usando tamaño {WINDOW_WIDTH}x{WINDOW_HEIGHT}"
            )

        # Crear ventana sin intentar establecer el icono en macOS
        window = webview.create_window(
            title="EDF CatálogoDeTablas",
            url=f"http://127.0.0.1:{port}",
            width=WINDOW_WIDTH,
            height=WINDOW_HEIGHT,
            min_size=(800, 600),
            text_select=True,
            confirm_close=True,
        )
        logger.info("Ventana webview creada correctamente")

        logger.info("Ventana webview creada, iniciando...")

        # Iniciar webview
        if sys.platform == "darwin":
            try:
                webview.start(gui="cocoa", debug=False)
            except Exception as e:
                logger.error(f"Error con gui=cocoa: {e}")
                try:
                    webview.start(debug=False)
                except Exception as e2:
                    logger.error(f"Error iniciando webview: {e2}")
                    raise
        else:
            webview.start(debug=False)

        logger.info("Aplicación finalizada")

    except Exception as e:
        logger.error(f"Error en main(): {e}")
        logger.error(traceback.format_exc())
        raise


if __name__ == "__main__":
    main()
