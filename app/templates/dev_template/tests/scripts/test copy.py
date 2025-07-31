from flask import Flask
import logging

# Configuración de registro
logging.basicConfig(
    filename='/test_app.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

app = Flask(__name__)

@app.route('/')
def hello_world():
    app.logger.info("Página de inicio visitada")
    return '¡Hola! La aplicación Flask de prueba está funcionando.'

@app.route('/error')
def test_error():
    try:
        # Provocar un error deliberado
        1/0
    except Exception as e:
        app.logger.error(f"Error de prueba: {str(e)}")
        return f"Error generado para pruebas: {str(e)}"

if __name__ == '__main__':
    app.run(debug=True, port=5001)