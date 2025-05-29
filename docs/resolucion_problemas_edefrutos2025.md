# Resolución de Problemas en la Aplicación Web edefrutos2025.xyz

## Diagnóstico y Solución de Errores en una Aplicación Flask con WSGI

### Contexto Inicial

El sitio web edefrutos2025.xyz estaba experimentando un error 500 que impedía su correcto funcionamiento. Tras un análisis de la situación, identificamos que el problema estaba relacionado con la configuración del entorno y la carga de variables necesarias para el funcionamiento de la aplicación Flask.

### Proceso de Resolución

#### 1. Identificación del Problema Principal

El problema central era que la aplicación no podía acceder a las variables de entorno necesarias para su funcionamiento. Esto se debía a que:
- El archivo `.env` estaba vacío o no existía en el servidor
- El archivo WSGI no estaba configurado para cargar las variables de entorno
- Las configuraciones de Apache no estaban correctamente establecidas

#### 2. Implementación del Archivo de Variables de Entorno

Creamos un archivo `.env` completo con todas las configuraciones necesarias:

```
# Configuración general de Flask
FLASK_SECRET_KEY=MBZl1W45ute3UEMCXPlL9JzcR7XsTeUi-4ZI6KCd79M
FLASK_ENV=production
FLASK_DEBUG=False

# Configuración de MongoDB
MONGO_URI=mongodb+srv://edfrutos:rYjwUC6pUNrLtbaI@cluster0.pmokh.mongodb.net/?retryWrites=true&w=majority

# Configuración de correo electrónico
MAIL_SERVER=smtp-relay.brevo.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=admin@edefrutos.me
MAIL_PASSWORD=********
MAIL_DEFAULT_SENDER_NAME=Administrador
MAIL_DEFAULT_SENDER_EMAIL=admin@edefrutos.me
MAIL_DEBUG=False

# Configuración de rutas
PYTHONPATH=.

# Configuración de AWS S3
AWS_ACCESS_KEY_ID=********************
AWS_SECRET_ACCESS_KEY=********
AWS_REGION=eu-central-1
S3_BUCKET_NAME=edf-catalogo-tablas
```

Ajustamos importantes valores para producción:
- Cambiamos `FLASK_ENV` a "production"
- Desactivamos `FLASK_DEBUG` para seguridad

#### 3. Configuración de Permisos

Establecimos los permisos adecuados para el archivo `.env`:
```bash
sudo chmod 640 /.env
sudo chown edefrutos2025:www-data /.env
```

Esto garantiza que:
- El archivo sea legible por el propietario y el grupo
- El usuario web (www-data) pueda leer las variables
- No sea accesible para otros usuarios del sistema

#### 4. Mejora del Archivo WSGI

Reescribimos completamente el archivo `wsgi.py` para que cargara correctamente las variables de entorno antes de inicializar la aplicación:

```python
import sys
import os
from dotenv import load_dotenv

# Añadir la ruta de la aplicación al path de Python
sys.path.insert(0, "/var/www/vhosts/edefrutos2025.xyz/httpdocs")

# Cargar variables de entorno desde .env
dotenv_path = os.path.join("/var/www/vhosts/edefrutos2025.xyz/httpdocs", ".env")
load_dotenv(dotenv_path)

# Configurar el entorno virtual
python_home = "/.venv"
python_bin = os.path.join(python_home, "bin")

# Establecer variables de entorno para el entorno virtual
os.environ["VIRTUAL_ENV"] = python_home
os.environ["PATH"] = python_bin + os.pathsep + os.environ.get("PATH", "")

# Importar la aplicación
from app import app as application
```

Este archivo realiza varias funciones críticas:
1. Carga las variables desde el archivo `.env`
2. Configura correctamente el entorno virtual de Python
3. Establece la ruta del proyecto en el path de Python
4. Importa la aplicación Flask como "application" (nombre requerido por WSGI)

#### 5. Verificación de Dependencias

Comprobamos que el paquete `python-dotenv` estaba correctamente instalado:
```bash
sudo -u edefrutos2025 /.venv/bin/pip install python-dotenv
```

Confirmamos que ya estaba disponible, lo que era necesario para cargar las variables de entorno.

#### 6. Aplicación de Cambios

Reiniciamos el servidor Apache para aplicar todos los cambios realizados:
```bash
sudo systemctl restart apache2
```

#### 7. Validación del Funcionamiento

Verificamos que la aplicación funcionaba correctamente mediante:
```bash
curl -s -o /dev/null -w "%{http_code}" https://edefrutos2025.xyz/
```

Obtuvimos un código 200 (éxito), y pudimos confirmar que el contenido se mostraba correctamente.

### Lecciones Aprendidas

Este proceso de resolución de problemas resalta varios aspectos importantes:

1. **Gestión de Configuración**: Las variables de entorno son críticas para el funcionamiento de aplicaciones Flask y deben gestionarse correctamente en producción.

2. **Seguridad**: Los archivos de configuración que contienen credenciales deben tener permisos restrictivos.

3. **Integración WSGI**: Es fundamental configurar correctamente la carga de variables de entorno en el archivo WSGI antes de inicializar la aplicación.

4. **Entornos Virtuales**: La correcta configuración del entorno virtual de Python es esencial para el funcionamiento de aplicaciones web.

5. **Diagnóstico Sistemático**: El proceso de resolución requirió un enfoque sistemático, revisando cada componente individualmente hasta encontrar la causa raíz.

### Conclusión

El sitio web edefrutos2025.xyz ahora funciona correctamente gracias a una adecuada configuración de variables de entorno, permisos y ajustes del archivo WSGI. La aplicación ahora muestra su página principal "Bienvenido a Catalogo de Tablas" y está lista para ser utilizada por los usuarios.

La clave para resolver problemas similares está en entender la interacción entre los diferentes componentes (Flask, WSGI, Apache, variables de entorno) y asegurarse de que cada uno esté correctamente configurado y tenga acceso a los recursos que necesita.
