# Script: test_app.py
# Descripción: [Explica brevemente qué hace el script]
# Uso: python3 test_app.py [opciones]
# Requiere: [librerías externas, si aplica]
# Variables de entorno: [si aplica]
# Autor: EDF Developer - 2025-05-28

from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    return "¡Hola, mundo! Prueba de servidor Gunicorn funcionando."

@app.route('/health')
def health():
    return "OK", 200

if __name__ == "__main__":
    app.run(host='127.0.0.1', port=5001, debug=False)
