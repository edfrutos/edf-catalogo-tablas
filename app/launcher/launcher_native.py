#!/usr/bin/env python3
"""
Lanzador nativo para EDF Catálogo de Tablas
Usa PyWebView para crear una aplicación de escritorio nativa
"""

import os
import sys
import tempfile
from pathlib import Path

# Configurar directorios escribibles ANTES de cualquier importación
if getattr(sys, "frozen", False):
    # Estamos en una aplicación empaquetada
    temp_dir = Path(tempfile.gettempdir()) / "edf_catalogo_logs"
    temp_dir.mkdir(exist_ok=True)
    os.environ["LOG_DIR"] = str(temp_dir)
    # Forzar también las rutas específicas que podría usar Flask
    os.environ["FLASK_LOG_DIR"] = str(temp_dir)
    print(f"📝 Directorio de logs configurado: {temp_dir}")

    # Configurar también el directorio de sesiones
    session_dir = temp_dir / "flask_session"
    session_dir.mkdir(exist_ok=True)
    os.environ["SESSION_FILE_DIR"] = str(session_dir)
    print(f"📝 Directorio de sesiones configurado: {session_dir}")

    # Configurar entorno para que coincida más con producción
    os.environ["FLASK_ENV"] = "production"  # Usar configuración de producción
    os.environ["FLASK_DEBUG"] = "0"  # Deshabilitar debug
    print(f"🔧 Configurado entorno de producción")  # noqa: F541

import threading
import time

import requests
import webview


def start_flask_server():
    """Inicia el servidor Flask en segundo plano"""
    try:
        from wsgi import app

        app.run(debug=False, port=5001, host="127.0.0.1", use_reloader=False)
    except Exception as e:
        print(f"❌ Error al iniciar el servidor Flask: {e}")
        sys.exit(1)


def wait_for_server():
    """Espera a que el servidor Flask esté listo"""
    max_attempts = 30
    for attempt in range(max_attempts):
        try:
            response = requests.get("http://127.0.0.1:5001", timeout=1)
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
    print("🚀 Iniciando EDF Catálogo de Tablas (Versión Nativa)")
    print("=" * 50)

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
        webview.create_window(
            title="EDF Catálogo de Tablas",
            url="http://127.0.0.1:5001",
            width=1400,
            height=900,
            resizable=True,
            min_size=(800, 600),
            text_select=True,
            confirm_close=True,
        )

        print("✅ Ventana nativa creada")
        print("🖥️  Aplicación ejecutándose en ventana nativa")
        print("🛑 Cierra la ventana para salir")
        print("-" * 50)

        # Iniciar la aplicación
        webview.start(debug=False)

    except Exception as e:
        print(f"❌ Error al crear la ventana nativa: {e}")
        print("🔄 Intentando abrir en navegador como fallback...")

        # Fallback: abrir en navegador
        import webbrowser

        webbrowser.open("http://127.0.0.1:5001")

        # Mantener el servidor corriendo
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Aplicación detenida")


if __name__ == "__main__":
    main()
