# Script: launcher_fixed.py
# Descripción: [Explica brevemente qué hace el script]
# Uso: python3 launcher_fixed.py [opciones]
# Requiere: [librerías externas, si aplica]
# Variables de entorno: [si aplica]
# Autor: [Tu nombre o equipo] - 2025-06-28

import logging
import os
import socket
import sys
import threading
import time
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
    logger.info(f"Ejecutándose como aplicación empaquetada desde: {base_path}")
else:
    # Estamos en desarrollo
    base_path = os.path.dirname(os.path.abspath(__file__))
    logger.info(f"Ejecutándose en modo desarrollo desde: {base_path}")

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

    logger.info("PyWebView importado correctamente")
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
        logger.info("Iniciando aplicación EDF CatalogoJoyero...")

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

        window = webview.create_window(
            "EDF CatalogoJoyero",
            f"http://127.0.0.1:{port}",
            width=1200,
            height=800,
            min_size=(800, 600),
            text_select=True,
            confirm_close=True,
        )

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
