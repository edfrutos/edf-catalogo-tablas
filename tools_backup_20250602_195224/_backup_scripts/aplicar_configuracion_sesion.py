#!/usr/bin/env python3
# Script para aplicar la configuración de sesión directamente en la aplicación
# Ejecutar con: python aplicar_configuracion_sesion.py

import os
import sys
import logging
from flask import Flask, session
from flask_session import Session

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

# Configuración de sesión optimizada
CONFIGURACION_SESION = {
    'SESSION_TYPE': 'filesystem',
    'SESSION_FILE_DIR': 'flask_session',
    'SESSION_COOKIE_NAME': 'edefrutos2025_session',
    'SESSION_COOKIE_SECURE': False,  # Deshabilitado para desarrollo
    'SESSION_COOKIE_HTTPONLY': True,
    'SESSION_COOKIE_SAMESITE': 'Lax',
    'SESSION_PERMANENT': True,
    'PERMANENT_SESSION_LIFETIME': 86400,  # 24 horas en segundos
    'SESSION_REFRESH_EACH_REQUEST': True,
    'SESSION_USE_SIGNER': False,
    'SECRET_KEY': 'desarrollo_clave_secreta_fija_12345'
}

def crear_app_prueba():
    """Crea una aplicación Flask de prueba con la configuración de sesión optimizada"""
    app = Flask(__name__)
    
    # Aplicar configuración de sesión
    for key, value in CONFIGURACION_SESION.items():
        app.config[key] = value
    
    # Asegurarse de que el directorio de sesiones existe y es absoluto
    if not os.path.isabs(app.config['SESSION_FILE_DIR']):
        app.config['SESSION_FILE_DIR'] = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            app.config['SESSION_FILE_DIR']
        )
    
    os.makedirs(app.config['SESSION_FILE_DIR'], exist_ok=True)
    
    # Inicializar Flask-Session
    Session(app)
    
    @app.route('/')
    def index():
        session['prueba'] = 'valor_de_prueba'
        return f"""
        <h1>Prueba de Sesión</h1>
        <p>Sesión establecida: {session.get('prueba')}</p>
        <p>Configuración aplicada:</p>
        <pre>{app.config}</pre>
        """
    
    return app

def actualizar_session_config():
    """Actualiza el archivo session_config.py con la configuración optimizada"""
    try:
        ruta_config = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'session_config.py')
        
        with open(ruta_config, 'w') as f:
            f.write("# Configuración de sesión optimizada para Flask\n")
            f.write("# Generado automáticamente por aplicar_configuracion_sesion.py\n\n")
            
            for key, value in CONFIGURACION_SESION.items():
                if isinstance(value, str):
                    f.write(f"{key} = '{value}'\n")
                else:
                    f.write(f"{key} = {value}\n")
        
        logging.info(f"✅ Archivo session_config.py actualizado correctamente en: {ruta_config}")
        return True
    except Exception as e:
        logging.error(f"❌ Error al actualizar session_config.py: {e}")
        import traceback
        logging.error(traceback.format_exc())
        return False

def verificar_permisos_directorio_sesiones():
    """Verifica y corrige los permisos del directorio de sesiones"""
    try:
        directorio = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            CONFIGURACION_SESION['SESSION_FILE_DIR']
        )
        
        if not os.path.exists(directorio):
            os.makedirs(directorio, exist_ok=True)
            logging.info(f"✅ Directorio de sesiones creado: {directorio}")
        
        # Verificar permisos
        if os.access(directorio, os.R_OK | os.W_OK):
            logging.info(f"✅ Permisos correctos en directorio de sesiones: {directorio}")
        else:
            logging.warning(f"⚠️ Corrigiendo permisos en directorio de sesiones: {directorio}")
            os.chmod(directorio, 0o755)  # rwxr-xr-x
            
        # Verificar si el servidor web puede acceder al directorio
        try:
            import pwd
            import grp
            
            # Intentar obtener el usuario del servidor web (www-data en muchos sistemas)
            try:
                www_data_uid = pwd.getpwnam('www-data').pw_uid
                www_data_gid = grp.getgrnam('www-data').gr_gid
                
                # Cambiar propietario del directorio
                os.chown(directorio, www_data_uid, www_data_gid)
                logging.info(f"✅ Propietario del directorio cambiado a www-data")
            except KeyError:
                logging.warning("⚠️ No se pudo encontrar el usuario www-data, omitiendo cambio de propietario")
        except ImportError:
            logging.warning("⚠️ No se pudieron importar módulos pwd/grp, omitiendo verificación de usuario")
        
        return True
    except Exception as e:
        logging.error(f"❌ Error al verificar permisos del directorio de sesiones: {e}")
        import traceback
        logging.error(traceback.format_exc())
        return False

def aplicar_configuracion():
    """Aplica la configuración de sesión optimizada"""
    logging.info("🔧 Aplicando configuración de sesión optimizada...")
    
    # Actualizar session_config.py
    if actualizar_session_config():
        logging.info("✅ Configuración de sesión actualizada en session_config.py")
    else:
        logging.error("❌ No se pudo actualizar la configuración de sesión")
    
    # Verificar permisos del directorio de sesiones
    if verificar_permisos_directorio_sesiones():
        logging.info("✅ Permisos del directorio de sesiones verificados y corregidos")
    else:
        logging.error("❌ No se pudieron verificar/corregir los permisos del directorio de sesiones")
    
    logging.info("✅ Configuración de sesión aplicada correctamente")
    logging.info("📌 Ahora debes reiniciar la aplicación para que los cambios surtan efecto")
    logging.info("📌 Ejecuta: pkill -f 'python -m flask run' && python -m flask run --host=0.0.0.0 --port=5000 --debug")

if __name__ == '__main__':
    aplicar_configuracion()
