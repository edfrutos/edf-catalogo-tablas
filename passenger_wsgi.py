import sys
import os

# Añadir el directorio actual al path de Python
INTERP = os.path.join(os.getcwd(), '.venv', 'bin', 'python')
if sys.executable != INTERP:
    os.execl(INTERP, INTERP, *sys.argv)

sys.path.append(os.getcwd())

# Importar la aplicación WSGI
from wsgi import application
