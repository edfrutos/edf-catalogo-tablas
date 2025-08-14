#!/usr/bin/env python3
"""
Script simple para iniciar el servidor Flask
"""

from wsgi import app

if __name__ == "__main__":
    print("🚀 Iniciando servidor Flask en puerto 5001...")
    app.run(debug=False, port=5001, host="0.0.0.0")
