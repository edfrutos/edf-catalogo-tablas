#!/usr/bin/env python3
"""
Lanzador para la aplicación web empaquetada
Abre automáticamente el navegador cuando el servidor esté listo
"""

import os
import sys  # noqa: F401
import threading
import time
import webbrowser


def open_browser():
    """Abre el navegador después de un breve delay"""
    time.sleep(2)  # Esperar a que el servidor se inicie
    try:
        _ = webbrowser.open("http://localhost:5001")
        print("🌐 Navegador abierto en http://localhost:5001")
    except Exception as e:
        print(f"⚠️  No se pudo abrir el navegador automáticamente: {e}")
        print("🌐 Abre manualmente: http://localhost:5001")


def main():
    print("🚀 Iniciando EDF Catálogo de Tablas (Versión Web)")
    print("=" * 50)

    # Iniciar el navegador en un hilo separado
    browser_thread = threading.Thread(target=open_browser)
    browser_thread.daemon = True
    browser_thread.start()

    # Importar y ejecutar el servidor Flask con la configuración correcta
    try:
        # Importar desde wsgi pero aplicar configuración especial de sesiones
        # Aplicar la misma configuración de sesiones que la app nativa
        from wsgi import app

        if getattr(sys, "frozen", False):
            app.config["SESSION_TYPE"] = "filesystem"
            app.config["SESSION_FILE_DIR"] = os.path.join(
                os.path.dirname(sys.executable), "flask_session"
            )
            app.config["SESSION_FILE_THRESHOLD"] = 0
            app.config["SESSION_FILE_MODE"] = 0o600
            app.config["SESSION_COOKIE_DOMAIN"] = "127.0.0.1"
            app.config["SESSION_COOKIE_PATH"] = "/"

            # Asegurar que el directorio de sesiones existe
            if app.config.get("SESSION_FILE_DIR"):
                os.makedirs(app.config["SESSION_FILE_DIR"], exist_ok=True)

        print("✅ Servidor Flask iniciado en puerto 5001")
        print("📱 Accede a la aplicación en tu navegador")
        print("🛑 Presiona Ctrl+C para detener el servidor")
        print("-" * 50)

        app.run(debug=False, port=5001, host="0.0.0.0", threaded=True)

    except KeyboardInterrupt:
        print("\n🛑 Servidor detenido por el usuario")
    except Exception as e:
        print(f"❌ Error al iniciar el servidor: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
