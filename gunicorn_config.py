# Gunicorn configuration file - Basic version
import multiprocessing
import os

# Obtener el número de núcleos de CPU disponibles
try:
    workers = multiprocessing.cpu_count() * 2 + 1
except Exception:
    workers = 3  # Valor por defecto si no se puede determinar

# Server socket
bind = "127.0.0.1:8002"
backlog = 2048

# Worker processes - Configuración básica
workers = 2  # Reducido a un valor bajo y seguro
worker_class = "sync"  # Modo síncrono básico
threads = 1
timeout = 120
keepalive = 2
max_requests = 1000
max_requests_jitter = 50

# Server mechanics
daemon = False
raw_env = [
    "PYTHONPATH=/var/www/vhosts/edefrutos2025.xyz/httpdocs",
    "FLASK_APP=wsgi.py",
    "FLASK_ENV=production",
]
pidfile = "/var/www/vhosts/edefrutos2025.xyz/tmp/gunicorn.pid"
umask = 0o002  # Permisos de archivo: 775 para directorios, 664 para archivos
user = "www-data"
group = "www-data"
tmp_upload_dir = "/var/www/vhosts/edefrutos2025.xyz/tmp/uploads"

# Logging
log_dir = "/logs"
if not os.path.exists(log_dir):
    os.makedirs(log_dir, exist_ok=True)

errorlog = os.path.join(log_dir, "gunicorn_error.log")
accesslog = os.path.join(log_dir, "gunicorn_access.log")
loglevel = (
    "warning"  # Reducido a 'warning' para disminuir I/O de disco y tamaño de logs
)
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" "%({X-Forwarded-For}i)s" %(L)ss'

# Process naming
proc_name = "edefrutos2025_gunicorn"


# Server hooks
def on_starting(server):
    """Ejecutar cuando el maestro arranca"""
    server.log.info("Iniciando servidor Gunicorn para edefrutos2025")


def when_ready(server):
    """Ejecutar cuando los workers están listos"""
    server.log.info(f"Workers listos. Sirviendo en {bind}")


def post_fork(server, worker):
    """Después de que un worker se ha bifurcado"""
    server.log.info(f"Worker {worker.pid} iniciado")


def worker_int(worker):
    """Cuando un worker recibe una señal de interrupción"""
    worker.log.info("Worker recibió señal de interrupción")


def worker_abort(worker):
    """Cuando un worker es abortado"""
    worker.log.warning("Worker abortado")


def pre_request(worker, req):
    """Antes de procesar una petición"""
    pass


def post_request(worker, req, environ, resp):
    """Después de procesar una petición"""
    pass


def child_exit(server, worker):
    """Cuando un worker muere"""
    try:
        server.log.warning(f"Worker {worker.pid} ha terminado")
    except Exception:
        pass


# Configuración adicional para depuración
if os.environ.get("FLASK_ENV") == "development":
    loglevel = "warning"
    reload = True
    reload_engine = "auto"
