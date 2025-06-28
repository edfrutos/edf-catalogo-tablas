# Script: launcher_original_backup.py
# Descripción: [Explica brevemente qué hace el script]
# Uso: python3 launcher_original_backup.py [opciones]
# Requiere: [librerías externas, si aplica]
# Variables de entorno: [si aplica]
# Autor: [Tu nombre o equipo] - 2025-06-28

import sys
import os
import threading
import time
import socket
import logging
import traceback

# Asegurarse de que pywebview esté instalado
try:
    import webview
except ImportError:
    print("Error: PyWebView no está instalado. Instalando...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pywebview"])
    import webview

# Verificar la versión de pywebview
try:
    print(f"PyWebView versión: {webview.__version__}")
except AttributeError:
    print("PyWebView instalado, pero no se pudo obtener la versión")

# Intentar crear un archivo de registro básico antes de cualquier otra cosa
try:
    # Crear directorio logs si no existe
    logs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
    os.makedirs(logs_dir, exist_ok=True)
    
    log_file = os.path.join(logs_dir, 'launcher.log')
    with open(log_file, 'w') as f:
        f.write('Inicio de registro - Antes de importar módulos\n')
        f.write(f'Python: {sys.version}\n')
        f.write(f'Sistema operativo: {sys.platform}\n')
        f.write(f'Directorio de trabajo: {os.getcwd()}\n')
        f.write(f'Modo congelado: {getattr(sys, "frozen", False)}\n')
except Exception as e:
    print(f"Error al crear archivo de registro inicial: {e}")
    traceback.print_exc()

# Asegurarse de que los módulos necesarios estén instalados
required_modules = ['flask-wtf', 'wtforms', 'email_validator', 'werkzeug', 'flask-session', 'flask-login', 'flask-mail']
for module in required_modules:
    try:
        module_name = module.replace('-', '_')
        imported_module = __import__(module_name)
        print(f"Módulo {module} importado correctamente: {imported_module}")
    except ImportError as e:
        print(f"Error: {module} no está instalado. Instalando... Error: {e}")
        try:
            import subprocess
            subprocess.check_call([sys.executable, "-m", "pip", "install", module])
            imported_module = __import__(module_name)
            print(f"Módulo {module} instalado e importado correctamente: {imported_module}")
        except Exception as e:
            print(f"Error al instalar {module}: {e}")

# Ahora importamos el resto de módulos
try:
    from main_app import app
    from app.extensions import init_extensions
except Exception as e:
    with open(log_file, 'a') as f:
        f.write(f"Error al importar módulos: {e}\n")
        f.write(traceback.format_exc())
    print(f"Error al importar módulos: {e}")
    traceback.print_exc()
    sys.exit(1)

# Configurar logging para depuración
logging.basicConfig(level=logging.DEBUG, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('launcher')

# Forzar Cocoa como GUI en macOS
if sys.platform == 'darwin':
    os.environ['PYWEBVIEW_GUI'] = 'cocoa'
    logger.info("Configurado PYWEBVIEW_GUI=cocoa para macOS")

# Asegurarse de que Flask-Login esté inicializado
try:
    logger.info("Inicializando extensiones manualmente desde launcher.py")
    
    # Configurar Flask para usar sesiones
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'clave_secreta_desarrollo')
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['SESSION_PERMANENT'] = True
    app.config['SESSION_USE_SIGNER'] = True
    app.config['SESSION_KEY_PREFIX'] = 'edf_catalogo:'
    
    # Asegurarse de que el directorio de sesiones existe
    if getattr(sys, 'frozen', False):
        session_dir = os.path.join(os.path.dirname(sys.executable), 'flask_session')
    else:
        session_dir = os.path.join(os.getcwd(), 'flask_session')
    
    if not os.path.exists(session_dir):
        os.makedirs(session_dir)
    
    app.config['SESSION_FILE_DIR'] = session_dir
    logger.info(f"Directorio de sesiones configurado: {session_dir}")
    
    # Inicializar extensiones
    init_extensions(app)
    logger.info("Extensiones inicializadas correctamente")
    
    # Verificar que login_manager está correctamente inicializado
    from flask_login import LoginManager
    if hasattr(app, 'login_manager'):
        logger.info(f"login_manager inicializado correctamente: {app.login_manager}")
    else:
        logger.error("app.login_manager no está definido")
    
    # Verificar que la sesión está configurada correctamente
    from flask_session import Session
    if hasattr(app, 'session_interface'):
        logger.info(f"Sesión configurada correctamente: {app.session_interface}")
    else:
        logger.error("app.session_interface no está definido")
        
    # Configurar un manejador de errores para depuración
    @app.errorhandler(Exception)
    def handle_exception(e):
        logger.error(f"Error no manejado: {str(e)}")
        logger.error(traceback.format_exc())
        return str(e), 500
except Exception as e:
    logger.error(f"Error al inicializar extensiones: {e}")
    logger.error(traceback.format_exc())

# Configurar archivo de registro para la aplicación empaquetada
try:
    # Añadir más información al archivo de registro
    with open(log_file, 'a') as f:
        f.write('\nConfigurando sistema de registro formal\n')
    
    # Configurar el registro
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    
    # Configurar el registro para todos los loggers
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(file_handler)
    
    # Añadir también a nuestro logger específico y al de Flask
    logger.addHandler(file_handler)
    app.logger.addHandler(file_handler)
    
    logger.info(f"Logs guardados en: {log_file}")
    
    # Registrar información del sistema
    logger.info(f"Sistema operativo: {sys.platform}")
    logger.info(f"Python: {sys.version}")
    logger.info(f"Directorio de trabajo: {os.getcwd()}")
    logger.info(f"Modo congelado: {getattr(sys, 'frozen', False)}")
    
    # Registrar información de la aplicación
    logger.info(f"Configuración de Flask: {app.config}")
    
    # Registrar información de las extensiones
    if hasattr(app, 'extensions'):
        logger.info(f"Extensiones de Flask: {app.extensions}")
    else:
        logger.error("app.extensions no está definido")
except Exception as e:
    with open(log_file, 'a') as f:
        f.write(f"Error al configurar el registro formal: {e}\n")
        f.write(traceback.format_exc())
    print(f"Error al configurar el registro: {e}")
    traceback.print_exc()

def find_free_port(default_port=5000):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind(('127.0.0.1', default_port))
        sock.close()
        return default_port
    except OSError:
        sock.bind(('127.0.0.1', 0))
        port = sock.getsockname()[1]
        sock.close()
        return port

def run_flask(port):
    try:
        # IMPORTANTE: debug=False y use_reloader=False
        logger.info(f"Iniciando Flask en puerto {port}")
        app.run(host='127.0.0.1', port=port, threaded=True, debug=False, use_reloader=False)
    except Exception as e:
        logger.error(f"Error al iniciar Flask: {e}")
        logger.error(traceback.format_exc())

def main():
    try:
        with open(log_file, 'a') as f:
            f.write('\nIniciando función main()\n')
            f.write(f'Python: {sys.version}\n')
            f.write(f'Sistema operativo: {sys.platform}\n')
            f.write(f'Directorio de trabajo: {os.getcwd()}\n')
            f.write(f'Modo congelado: {getattr(sys, "frozen", False)}\n')
            f.write(f'Ruta del ejecutable: {sys.executable}\n')
            f.write(f'Argumentos: {sys.argv}\n')
            f.write(f'Módulos importados: {list(sys.modules.keys())}\n')
        
        logger.info("Iniciando aplicación...")
        port = find_free_port()
        logger.info(f"Puerto seleccionado: {port}")
        
        with open(log_file, 'a') as f:
            f.write(f'Puerto seleccionado: {port}\n')
        
        # Configurar Flask para usar cookies de sesión
        app.config['SESSION_TYPE'] = 'filesystem'
        app.config['SESSION_PERMANENT'] = True
        app.config['SESSION_USE_SIGNER'] = True
        app.config['SESSION_KEY_PREFIX'] = 'edf_catalogo:'
        
        # Asegurarse de que el directorio de sesiones existe
        if getattr(sys, 'frozen', False):
            session_dir = os.path.join(os.path.dirname(sys.executable), 'flask_session')
        else:
            session_dir = os.path.join(os.getcwd(), 'flask_session')
        
        if not os.path.exists(session_dir):
            os.makedirs(session_dir)
        
        app.config['SESSION_FILE_DIR'] = session_dir
        logger.info(f"Directorio de sesiones configurado: {session_dir}")
        
        # Iniciar el servidor Flask en un hilo separado
        flask_thread = threading.Thread(target=run_flask, args=(port,), daemon=True)
        flask_thread.start()
        logger.info("Hilo de Flask iniciado")
        
        with open(log_file, 'a') as f:
            f.write('Hilo de Flask iniciado\n')
        
        # Aumentar el tiempo de espera para asegurar que Flask esté listo
        time.sleep(5)  # Aumentado a 5 segundos para dar más tiempo
        logger.info("Tiempo de espera completado")
        
        with open(log_file, 'a') as f:
            f.write('Tiempo de espera completado\n')
        
        # Crear ventana webview en todos los casos
        logger.info("Creando ventana webview...")
        
        with open(log_file, 'a') as f:
            f.write('Intentando crear ventana webview...\n')
        
        # Configurar opciones de webview para mejorar la compatibilidad
        # Algunas versiones de webview no tienen el atributo config
        try:
            webview.config.debug = True
            webview.config.use_frozen_path = True
        except AttributeError:
            # Si no existe config, continuamos sin configurar estas opciones
            with open(log_file, 'a') as f:
                f.write('webview.config no está disponible en esta versión\n')
        
        # Crear la ventana con opciones adicionales
        window = webview.create_window(
            'EDF CatalogoJoyero', 
            f'http://127.0.0.1:{port}', 
            width=1200, 
            height=800,
            min_size=(800, 600),
            text_select=True,
            confirm_close=True
        )
        logger.info("Ventana webview creada")
        
        with open(log_file, 'a') as f:
            f.write('Ventana webview creada\n')
        
        logger.info("Iniciando webview...")
        
        with open(log_file, 'a') as f:
            f.write('Iniciando webview...\n')
        
        # Iniciar webview con opciones específicas para macOS
        if sys.platform == 'darwin':
            with open(log_file, 'a') as f:
                f.write('Iniciando webview con gui=cocoa\n')
            try:
                webview.start(gui='cocoa', debug=True)
            except Exception as e:
                with open(log_file, 'a') as f:
                    f.write(f'Error al iniciar webview con gui=cocoa: {e}\n')
                    f.write(traceback.format_exc())
                # Intentar con otro GUI
                with open(log_file, 'a') as f:
                    f.write('Intentando iniciar webview con gui=qt\n')
                try:
                    webview.start(gui='qt', debug=True)
                except Exception as e:
                    with open(log_file, 'a') as f:
                        f.write(f'Error al iniciar webview con gui=qt: {e}\n')
                        f.write(traceback.format_exc())
                    # Último intento sin especificar GUI
                    with open(log_file, 'a') as f:
                        f.write('Intentando iniciar webview sin especificar GUI\n')
                    webview.start(debug=True)
        else:
            webview.start(debug=True)
            
        logger.info("Webview finalizado")
        
        with open(log_file, 'a') as f:
            f.write('Webview finalizado\n')
    except Exception as e:
        with open(log_file, 'a') as f:
            f.write(f"Error en main(): {e}\n")
            f.write(traceback.format_exc())
        logger.error(f"Error en main(): {e}", exc_info=True)
        raise

if __name__ == '__main__':
    main()
