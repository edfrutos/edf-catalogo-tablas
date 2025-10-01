#!/usr/bin/env python3
"""
Lanzador nativo para EDF Catálogo de Tablas
Ejecuta la aplicación web Flask en una ventana nativa de macOS
con soporte para WebSockets en tiempo real
"""

import os
import sys
import tempfile
import threading
import time
from pathlib import Path

import requests
import webview

# Configurar directorios escribibles ANTES de cualquier importación
if getattr(sys, "frozen", False):
    # Estamos en una aplicación empaquetada
    temp_dir = Path(tempfile.gettempdir()) / "edf_catalogo_logs"
    temp_dir.mkdir(exist_ok=True)
    os.environ["LOG_DIR"] = str(temp_dir)
    os.environ["FLASK_LOG_DIR"] = str(temp_dir)
    print(f"📝 Directorio de logs configurado: {temp_dir}")

    # Configurar directorio de sesiones
    session_dir = temp_dir / "flask_session"
    session_dir.mkdir(exist_ok=True)
    os.environ["SESSION_FILE_DIR"] = str(session_dir)
    print(f"📝 Directorio de sesiones configurado: {session_dir}")

    # Configurar entorno de producción
    os.environ["FLASK_ENV"] = "production"
    os.environ["FLASK_DEBUG"] = "0"
    print("🔧 Configurado entorno de producción")


def start_flask_server():
    """Inicia el servidor Flask en segundo plano"""
    try:
        from wsgi import app

        # Configuración específica para pywebview
        app.config.update(
            {
                "SESSION_COOKIE_SECURE": False,  # HTTP para pywebview
                "SESSION_COOKIE_HTTPONLY": False,  # Acceso desde JavaScript
                "SESSION_COOKIE_SAMESITE": None,  # Sin SameSite
                "SESSION_COOKIE_DOMAIN": None,  # Sin dominio específico
            }
        )

        app.run(debug=False, port=5004, host="127.0.0.1", use_reloader=False)
    except Exception as e:
        print(f"❌ Error al iniciar el servidor Flask: {e}")
        sys.exit(1)


def wait_for_server():
    """Espera a que el servidor Flask esté listo"""
    max_attempts = 30
    for attempt in range(max_attempts):
        try:
            response = requests.get("http://127.0.0.1:5004", timeout=1)
            if response.status_code in [200, 302]:
                print(f"✅ Servidor Flask listo (intento {attempt + 1})")
                return True
        except requests.exceptions.RequestException:
            pass

        time.sleep(1)
        if attempt % 5 == 0:
            print(
                f"⏳ Esperando servidor Flask... "
                f"(intento {attempt + 1}/{max_attempts})"
            )

    print("❌ Timeout esperando al servidor Flask")
    return False


def main():
    """Función principal de la aplicación"""
    print("🚀 Iniciando EDF Catálogo de Tablas (Aplicación Nativa WebSockets)")
    print("=" * 60)

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
            "title": "EDF Catálogo de Tablas - Aplicación Web Nativa",
            "url": "http://127.0.0.1:5004",
            "width": 1400,
            "height": 900,
            "resizable": True,
            "min_size": (800, 600),
            "text_select": True,
            "confirm_close": True,
        }

        # Crear la ventana nativa
        webview.create_window(**window_config)

        print("✅ Ventana nativa creada")
        print("🖥️  Aplicación web ejecutándose en ventana nativa")
        print("🌐 WebSockets habilitados para comunicación en tiempo real")
        print("🛑 Cierra la ventana para salir")
        print("-" * 60)

        # Iniciar la aplicación con configuración mejorada
        webview.start(debug=True, gui="native")

    except Exception as e:
        print(f"❌ Error al crear la ventana nativa: {e}")
        print("🔄 Intentando abrir en navegador como fallback...")

        # Fallback: abrir en navegador
        import webbrowser

        webbrowser.open("http://127.0.0.1:5004")

        # Mantener el servidor corriendo
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Aplicación detenida")


if __name__ == "__main__":
    main()
