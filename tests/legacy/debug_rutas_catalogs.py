#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import logging
import requests
import re
import json
from bs4 import BeautifulSoup
import time
from pymongo import MongoClient
import certifi
from bson.objectid import ObjectId

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Configuración
BASE_URL = "http://127.0.0.1:5001"
ADMIN_EMAIL = "admin@example.com"
ADMIN_PASSWORD = "admin123"

# Cargar configuración
try:
    from config import Config
    MONGO_URI = Config.MONGO_URI
except ImportError:
    MONGO_URI = os.environ.get('MONGO_URI', 'mongodb+srv://edfrutos:3Utitwr3piFt4LVf@cluster0.abpvipa.mongodb.net/app_catalogojoyero_nueva?retryWrites=true&w=majority&appName=Cluster0')

os.environ['SSL_CERT_FILE'] = certifi.where()

def conectar_mongodb():
    """Establece conexión con MongoDB y retorna el cliente y la base de datos."""
    try:
        client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
        db = client.get_database()
        logger.info("✅ Conexión a MongoDB establecida correctamente")
        return client, db
    except Exception as e:
        logger.error(f"❌ Error al conectar a MongoDB: {str(e)}")
        return None, None

def obtener_csrf_token(html):
    """Extrae el token CSRF del HTML de la página."""
    soup = BeautifulSoup(html, 'html.parser')
    csrf_input = soup.find('input', {'name': 'csrf_token'})
    if csrf_input:
        return csrf_input.get('value')
    return None

def iniciar_sesion(session, email, password):
    """Inicia sesión en la aplicación y retorna los detalles de la sesión."""
    try:
        # Obtener la página de login para extraer el token CSRF
        response = session.get(f"{BASE_URL}/login")
        response.raise_for_status()
        
        csrf_token = obtener_csrf_token(response.text)
        if not csrf_token:
            logger.warning("No se pudo obtener el token CSRF")
        
        # Datos para el inicio de sesión
        login_data = {
            "email": email,
            "password": password,
            "csrf_token": csrf_token
        }
        
        # Enviar solicitud de inicio de sesión
        login_response = session.post(f"{BASE_URL}/login", data=login_data, allow_redirects=True)
        login_response.raise_for_status()
        
        # Verificar si el inicio de sesión fue exitoso
        if "dashboard" in login_response.url or "admin" in login_response.url:
            logger.info(f"✅ Inicio de sesión exitoso como {email}")
            
            # Obtener detalles de la sesión
            session_info = {
                "url_final": login_response.url,
                "cookies": dict(session.cookies),
                "headers": dict(login_response.headers)
            }
            
            # Intentar obtener información del usuario desde la página
            try:
                user_info_response = session.get(f"{BASE_URL}/admin/maintenance/dashboard_user")
                soup = BeautifulSoup(user_info_response.text, 'html.parser')
                user_info = {}
                
                # Buscar información del usuario en la página
                username_elem = soup.find('span', {'class': 'username'})
                if username_elem:
                    user_info['username'] = username_elem.text.strip()
                
                role_elem = soup.find('span', {'class': 'role'})
                if role_elem:
                    user_info['role'] = role_elem.text.strip()
                
                session_info['user_info'] = user_info
            except Exception as e:
                logger.warning(f"No se pudo obtener información del usuario: {str(e)}")
            
            return True, session_info
        else:
            logger.warning(f"❌ Inicio de sesión fallido como {email}")
            return False, None
    
    except requests.RequestException as e:
        logger.error(f"Error durante el inicio de sesión: {str(e)}")
        return False, None

def verificar_rutas_catalogs(session):
    """Verifica todas las rutas relacionadas con catálogos y registra los resultados."""
    rutas = [
        "/catalogs",
        "/catalogs/",
        "/catalogs/create"
    ]
    
    resultados = {}
    
    for ruta in rutas:
        try:
            url = f"{BASE_URL}{ruta}"
            logger.info(f"Verificando ruta: {url}")
            
            response = session.get(url)
            
            resultados[ruta] = {
                "status_code": response.status_code,
                "url_final": response.url,
                "redirect": response.url != url,
                "content_length": len(response.text),
                "error_message": None
            }
            
            # Buscar mensajes de error específicos
            soup = BeautifulSoup(response.text, 'html.parser')
            error_messages = []
            
            for alert in soup.find_all('div', {'class': ['alert', 'alert-danger']}):
                error_messages.append(alert.text.strip())
            
            if error_messages:
                resultados[ruta]["error_message"] = error_messages
            
            # Verificar si hay mensajes específicos en el HTML
            if "Error interno: ruta no encontrada o mal configurada" in response.text:
                resultados[ruta]["error_interno"] = True
            
            if "No tiene permisos para acceder a esta página" in response.text:
                resultados[ruta]["error_permisos"] = True
            
            logger.info(f"Resultado para {ruta}: {response.status_code} - {'Redirección a ' + response.url if response.url != url else 'Sin redirección'}")
        
        except Exception as e:
            logger.error(f"Error al verificar ruta {ruta}: {str(e)}")
            resultados[ruta] = {
                "status_code": None,
                "error": str(e)
            }
    
    return resultados

def verificar_catalogo_especifico(session, db):
    """Verifica el acceso a un catálogo específico."""
    try:
        # Buscar un catálogo en la base de datos
        catalogo = db.catalogs.find_one({})
        
        if not catalogo:
            logger.warning("No se encontraron catálogos en la base de datos")
            return None
        
        catalog_id = str(catalogo["_id"])
        logger.info(f"Verificando acceso al catálogo con ID: {catalog_id}")
        
        # Intentar acceder al catálogo
        url = f"{BASE_URL}/catalogs/{catalog_id}"
        response = session.get(url)
        
        resultado = {
            "catalog_id": catalog_id,
            "status_code": response.status_code,
            "url_final": response.url,
            "redirect": response.url != url,
            "content_length": len(response.text),
            "error_message": None,
            "catalog_data": {
                "name": catalogo.get("name", "N/A"),
                "created_by": catalogo.get("created_by", "N/A"),
                "headers": catalogo.get("headers", []),
                "rows_count": len(catalogo.get("rows", []))
            }
        }
        
        # Buscar mensajes de error específicos
        soup = BeautifulSoup(response.text, 'html.parser')
        error_messages = []
        
        for alert in soup.find_all('div', {'class': ['alert', 'alert-danger']}):
            error_messages.append(alert.text.strip())
        
        if error_messages:
            resultado["error_message"] = error_messages
        
        # Verificar si hay mensajes específicos en el HTML
        if "Error interno: ruta no encontrada o mal configurada" in response.text:
            resultado["error_interno"] = True
        
        if "No tiene permisos para acceder a esta página" in response.text:
            resultado["error_permisos"] = True
        
        logger.info(f"Resultado para catálogo {catalog_id}: {response.status_code} - {'Redirección a ' + response.url if response.url != url else 'Sin redirección'}")
        
        return resultado
    
    except Exception as e:
        logger.error(f"Error al verificar catálogo específico: {str(e)}")
        return None

def verificar_plantillas_catalogs():
    """Verifica la existencia y estructura de las plantillas relacionadas con catálogos."""
    plantillas = [
        "catalogs.html",
        "ver_catalogo.html",
        "editar_catalogo.html",
        "agregar_fila.html",
        "editar_fila.html"
    ]
    
    resultados = {}
    
    for plantilla in plantillas:
        ruta_plantilla = f"app/templates/{plantilla}"
        ruta_admin_plantilla = f"app/templates/admin/{plantilla}"
        
        resultado = {
            "existe": False,
            "ruta": None,
            "tamaño": None,
            "error": None
        }
        
        try:
            # Verificar en la carpeta principal de plantillas
            if os.path.exists(ruta_plantilla):
                resultado["existe"] = True
                resultado["ruta"] = ruta_plantilla
                resultado["tamaño"] = os.path.getsize(ruta_plantilla)
            
            # Verificar en la carpeta de admin
            elif os.path.exists(ruta_admin_plantilla):
                resultado["existe"] = True
                resultado["ruta"] = ruta_admin_plantilla
                resultado["tamaño"] = os.path.getsize(ruta_admin_plantilla)
            
            logger.info(f"Plantilla {plantilla}: {'✅ Encontrada en ' + resultado['ruta'] if resultado['existe'] else '❌ No encontrada'}")
        
        except Exception as e:
            resultado["error"] = str(e)
            logger.error(f"Error al verificar plantilla {plantilla}: {str(e)}")
        
        resultados[plantilla] = resultado
    
    return resultados

def verificar_blueprints():
    """Verifica la configuración de los blueprints en app.py."""
    try:
        with open("app.py", "r") as f:
            contenido = f.read()
        
        # Buscar registro de blueprints
        import re
        
        # Buscar importación del blueprint de catálogos
        import_match = re.search(r"from\s+app\.routes\.catalogs_routes\s+import\s+catalogs_bp", contenido)
        
        # Buscar registro del blueprint
        register_match = re.search(r"app\.register_blueprint\(\s*catalogs_bp\s*(?:,\s*url_prefix\s*=\s*['\"](.+)['\"]\s*)?\)", contenido)
        
        resultado = {
            "importado": bool(import_match),
            "registrado": bool(register_match),
            "url_prefix": register_match.group(1) if register_match and register_match.groups() else None
        }
        
        logger.info(f"Blueprint catalogs_bp: {'✅ Importado' if resultado['importado'] else '❌ No importado'}, {'✅ Registrado' if resultado['registrado'] else '❌ No registrado'}, URL prefix: {resultado['url_prefix'] or 'No especificado'}")
        
        return resultado
    
    except Exception as e:
        logger.error(f"Error al verificar blueprints: {str(e)}")
        return None

def verificar_sesion_usuario(session):
    """Verifica los detalles de la sesión del usuario."""
    try:
        # Obtener información de la sesión
        response = session.get(f"{BASE_URL}/admin/maintenance/dashboard_user")
        
        # Extraer información de la sesión del HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Buscar scripts que contengan información de la sesión
        scripts = soup.find_all('script')
        session_info = {}
        
        for script in scripts:
            if script.string and "var userInfo" in script.string:
                # Extraer información del usuario del script
                try:
                    user_info_match = re.search(r"var\s+userInfo\s*=\s*({.+?});", script.string, re.DOTALL)
                    if user_info_match:
                        user_info_json = user_info_match.group(1)
                        # Convertir a formato JSON válido
                        user_info_json = user_info_json.replace("'", "\"")
                        session_info["user_info"] = json.loads(user_info_json)
                except Exception as e:
                    logger.warning(f"No se pudo extraer información del usuario del script: {str(e)}")
        
        # Obtener información de las cookies
        session_info["cookies"] = dict(session.cookies)
        
        # Verificar si hay una cookie de sesión
        session_cookie = session.cookies.get("edefrutos2025_session")
        session_info["session_cookie_present"] = bool(session_cookie)
        
        logger.info(f"Información de sesión: Cookie de sesión presente: {session_info['session_cookie_present']}")
        
        return session_info
    
    except Exception as e:
        logger.error(f"Error al verificar sesión de usuario: {str(e)}")
        return None

def main():
    """Función principal que ejecuta el diagnóstico de rutas de catálogos."""
    logger.info("Iniciando diagnóstico de rutas de catálogos...")
    
    # Conectar a MongoDB
    client, db = conectar_mongodb()
    if client is None:
        logger.error("No se pudo conectar a MongoDB. Abortando.")
        return False
    
    try:
        # Crear sesión para mantener las cookies
        session = requests.Session()
        
        # Iniciar sesión con las credenciales de administrador
        login_success, session_info = iniciar_sesion(session, ADMIN_EMAIL, ADMIN_PASSWORD)
        
        if not login_success:
            logger.error("No se pudo iniciar sesión como administrador. Abortando.")
            return False
        
        # Verificar rutas de catálogos
        rutas_result = verificar_rutas_catalogs(session)
        
        # Verificar acceso a un catálogo específico
        catalogo_result = verificar_catalogo_especifico(session, db)
        
        # Verificar plantillas
        plantillas_result = verificar_plantillas_catalogs()
        
        # Verificar blueprints
        blueprints_result = verificar_blueprints()
        
        # Verificar sesión de usuario
        sesion_result = verificar_sesion_usuario(session)
        
        # Generar informe detallado
        logger.info("\n=== INFORME DE DIAGNÓSTICO ===")
        
        logger.info("\n1. RUTAS DE CATÁLOGOS")
        for ruta, resultado in rutas_result.items():
            status = resultado.get("status_code")
            status_str = f"{status} ({'OK' if status == 200 else 'ERROR'})"
            redirect_str = f"Redirección a {resultado.get('url_final')}" if resultado.get("redirect") else "Sin redirección"
            error_str = f"Error: {resultado.get('error_message')}" if resultado.get("error_message") else ""
            
            logger.info(f"  - {ruta}: {status_str}, {redirect_str} {error_str}")
            
            if resultado.get("error_interno"):
                logger.warning(f"    ⚠️ Se detectó mensaje 'Error interno: ruta no encontrada o mal configurada'")
            
            if resultado.get("error_permisos"):
                logger.warning(f"    ⚠️ Se detectó mensaje 'No tiene permisos para acceder a esta página'")
        
        if catalogo_result:
            logger.info("\n2. CATÁLOGO ESPECÍFICO")
            catalog_id = catalogo_result.get("catalog_id")
            status = catalogo_result.get("status_code")
            status_str = f"{status} ({'OK' if status == 200 else 'ERROR'})"
            redirect_str = f"Redirección a {catalogo_result.get('url_final')}" if catalogo_result.get("redirect") else "Sin redirección"
            error_str = f"Error: {catalogo_result.get('error_message')}" if catalogo_result.get("error_message") else ""
            
            logger.info(f"  - Catálogo {catalog_id}: {status_str}, {redirect_str} {error_str}")
            
            if catalogo_result.get("error_interno"):
                logger.warning(f"    ⚠️ Se detectó mensaje 'Error interno: ruta no encontrada o mal configurada'")
            
            if catalogo_result.get("error_permisos"):
                logger.warning(f"    ⚠️ Se detectó mensaje 'No tiene permisos para acceder a esta página'")
            
            # Mostrar datos del catálogo
            catalog_data = catalogo_result.get("catalog_data", {})
            logger.info(f"  - Datos del catálogo:")
            logger.info(f"    * Nombre: {catalog_data.get('name')}")
            logger.info(f"    * Creado por: {catalog_data.get('created_by')}")
            logger.info(f"    * Número de columnas: {len(catalog_data.get('headers', []))}")
            logger.info(f"    * Número de filas: {catalog_data.get('rows_count')}")
        
        logger.info("\n3. PLANTILLAS")
        for plantilla, resultado in plantillas_result.items():
            status_str = "✅ Encontrada" if resultado.get("existe") else "❌ No encontrada"
            ruta_str = f"en {resultado.get('ruta')}" if resultado.get("ruta") else ""
            tamaño_str = f"({resultado.get('tamaño')} bytes)" if resultado.get("tamaño") else ""
            
            logger.info(f"  - {plantilla}: {status_str} {ruta_str} {tamaño_str}")
        
        if blueprints_result:
            logger.info("\n4. BLUEPRINTS")
            importado_str = "✅ Importado" if blueprints_result.get("importado") else "❌ No importado"
            registrado_str = "✅ Registrado" if blueprints_result.get("registrado") else "❌ No registrado"
            prefix_str = f"con prefix '{blueprints_result.get('url_prefix')}'" if blueprints_result.get("url_prefix") else "sin prefix específico"
            
            logger.info(f"  - Blueprint catalogs_bp: {importado_str}, {registrado_str}, {prefix_str}")
        
        if sesion_result:
            logger.info("\n5. SESIÓN DE USUARIO")
            cookie_str = "✅ Presente" if sesion_result.get("session_cookie_present") else "❌ Ausente"
            
            logger.info(f"  - Cookie de sesión: {cookie_str}")
            
            user_info = sesion_result.get("user_info", {})
            if user_info:
                logger.info(f"  - Información del usuario:")
                for key, value in user_info.items():
                    logger.info(f"    * {key}: {value}")
        
        # Diagnóstico y recomendaciones
        logger.info("\n=== DIAGNÓSTICO Y RECOMENDACIONES ===")
        
        # Verificar problemas comunes
        problemas = []
        
        # 1. Verificar problemas de rutas
        ruta_catalogs = rutas_result.get("/catalogs", {})
        if ruta_catalogs.get("status_code") != 200 and not ruta_catalogs.get("redirect"):
            problemas.append("La ruta /catalogs no está funcionando correctamente")
        
        # 2. Verificar problemas de plantillas
        plantillas_faltantes = [p for p, r in plantillas_result.items() if not r.get("existe")]
        if plantillas_faltantes:
            problemas.append(f"Faltan las siguientes plantillas: {', '.join(plantillas_faltantes)}")
        
        # 3. Verificar problemas de blueprints
        if blueprints_result:
            if not blueprints_result.get("importado"):
                problemas.append("El blueprint catalogs_bp no está importado en app.py")
            if not blueprints_result.get("registrado"):
                problemas.append("El blueprint catalogs_bp no está registrado en app.py")
        
        # 4. Verificar problemas de sesión
        if sesion_result and not sesion_result.get("session_cookie_present"):
            problemas.append("No hay cookie de sesión presente")
        
        # Mostrar problemas encontrados
        if problemas:
            logger.warning("Se encontraron los siguientes problemas:")
            for i, problema in enumerate(problemas, 1):
                logger.warning(f"{i}. {problema}")
        else:
            logger.info("No se encontraron problemas evidentes en la configuración")
        
        # Recomendaciones
        logger.info("\nRecomendaciones:")
        
        if plantillas_faltantes:
            logger.info("1. Crear las plantillas faltantes:")
            for plantilla in plantillas_faltantes:
                logger.info(f"   - Crear app/templates/{plantilla}")
        
        if blueprints_result and (not blueprints_result.get("importado") or not blueprints_result.get("registrado")):
            logger.info("2. Verificar la configuración del blueprint en app.py:")
            logger.info("   - Asegurarse de que se importa: from app.routes.catalogs_routes import catalogs_bp")
            logger.info("   - Asegurarse de que se registra: app.register_blueprint(catalogs_bp)")
        
        logger.info("3. Verificar la función check_catalog_permission en app/routes/catalogs_routes.py:")
        logger.info("   - Asegurarse de que maneja correctamente los permisos")
        logger.info("   - Verificar que la sesión contiene la información necesaria (username, email, role)")
        
        logger.info("4. Reiniciar la aplicación Flask para aplicar los cambios:")
        logger.info("   $ pkill -f 'python.*ejecutar_flask_directo.py'")
        logger.info("   $ python3 ejecutar_flask_directo.py")
        
        return True
    
    except Exception as e:
        logger.error(f"Error durante el diagnóstico: {str(e)}")
        return False
    
    finally:
        if client:
            client.close()
            logger.info("Conexión a MongoDB cerrada")

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
