#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import logging
import requests
import json
from pymongo import MongoClient
import certifi
from bs4 import BeautifulSoup
import re

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# URLs de la aplicación
BASE_URL = 'http://127.0.0.1:8002'
ADMIN_URL = f'{BASE_URL}/admin/'
USER_URL = f'{BASE_URL}/dashboard_user'
CATALOGS_URL = f'{BASE_URL}/catalogs/'
LOGIN_URL = f'{BASE_URL}/login'
TABLES_URL = f'{BASE_URL}/tables'

# Cargar configuración
try:
    from config import Config
    MONGO_URI = Config.MONGO_URI
except ImportError:
    MONGO_URI = os.environ.get('MONGO_URI', 'mongodb+srv://admin:admin123@cluster0.pmokh.mongodb.net/app_catalogojoyero_nueva?retryWrites=true&w=majority')

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

def verificar_rutas_principales():
    """Verifica el acceso a las rutas principales de la aplicación."""
    rutas = {
        'Página principal': BASE_URL,
        'Login': LOGIN_URL,
        'Panel de administración': ADMIN_URL,
        'Dashboard de usuario': USER_URL,
        'Catálogos': CATALOGS_URL,
        'Tablas': TABLES_URL
    }
    
    resultados = {}
    
    for nombre, url in rutas.items():
        try:
            logger.info(f"Verificando acceso a {nombre} ({url})...")
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                titulo = soup.title.string if soup.title else "Sin título"
                
                # Verificar si hay mensajes de error en la página
                mensajes_error = [
                    "Error interno",
                    "ruta no encontrada",
                    "mal configurada",
                    "No tiene permisos",
                    "Acceso denegado",
                    "Forbidden",
                    "Not Found"
                ]
                
                error_encontrado = False
                for mensaje in mensajes_error:
                    if mensaje in response.text:
                        logger.error(f"❌ Acceso a {nombre} fallido: {mensaje}")
                        resultados[nombre] = {
                            'status': 'error',
                            'codigo': response.status_code,
                            'titulo': titulo,
                            'mensaje': mensaje
                        }
                        error_encontrado = True
                        break
                
                if not error_encontrado:
                    logger.info(f"✅ Acceso a {nombre} exitoso (código 200, título: {titulo})")
                    resultados[nombre] = {
                        'status': 'ok',
                        'codigo': response.status_code,
                        'titulo': titulo
                    }
            
            elif response.status_code == 302:
                # Redirección
                logger.warning(f"⚠️ Acceso a {nombre} redirige a: {response.headers.get('Location')}")
                resultados[nombre] = {
                    'status': 'redirect',
                    'codigo': response.status_code,
                    'location': response.headers.get('Location')
                }
            
            else:
                logger.error(f"❌ Acceso a {nombre} fallido: código {response.status_code}")
                resultados[nombre] = {
                    'status': 'error',
                    'codigo': response.status_code
                }
        
        except Exception as e:
            logger.error(f"❌ Error al verificar acceso a {nombre}: {str(e)}")
            resultados[nombre] = {
                'status': 'error',
                'mensaje': str(e)
            }
    
    return resultados

def verificar_formularios():
    """Verifica si los formularios de la aplicación funcionan correctamente."""
    formularios = {
        'Crear catálogo': {
            'url': f'{BASE_URL}/catalogs/create',
            'method': 'GET'
        },
        'Editar catálogo': {
            'url': f'{BASE_URL}/tables',
            'method': 'GET'
        },
        'Importar catálogo': {
            'url': f'{BASE_URL}/tables',
            'method': 'GET'
        }
    }
    
    resultados = {}
    
    for nombre, info in formularios.items():
        try:
            logger.info(f"Verificando formulario {nombre} ({info['url']})...")
            
            if info['method'] == 'GET':
                response = requests.get(info['url'], timeout=5)
            else:
                response = requests.post(info['url'], data={}, timeout=5)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                forms = soup.find_all('form')
                
                if forms:
                    logger.info(f"✅ Formulario {nombre} encontrado ({len(forms)} formularios en la página)")
                    resultados[nombre] = {
                        'status': 'ok',
                        'codigo': response.status_code,
                        'num_forms': len(forms)
                    }
                else:
                    logger.warning(f"⚠️ No se encontraron formularios en la página {nombre}")
                    resultados[nombre] = {
                        'status': 'warning',
                        'codigo': response.status_code,
                        'mensaje': 'No se encontraron formularios'
                    }
            
            elif response.status_code == 302:
                # Redirección
                logger.warning(f"⚠️ Acceso a formulario {nombre} redirige a: {response.headers.get('Location')}")
                resultados[nombre] = {
                    'status': 'redirect',
                    'codigo': response.status_code,
                    'location': response.headers.get('Location')
                }
            
            else:
                logger.error(f"❌ Acceso a formulario {nombre} fallido: código {response.status_code}")
                resultados[nombre] = {
                    'status': 'error',
                    'codigo': response.status_code
                }
        
        except Exception as e:
            logger.error(f"❌ Error al verificar formulario {nombre}: {str(e)}")
            resultados[nombre] = {
                'status': 'error',
                'mensaje': str(e)
            }
    
    return resultados

def verificar_botones_y_enlaces():
    """Verifica si los botones y enlaces de la aplicación funcionan correctamente."""
    paginas = {
        'Dashboard de usuario': USER_URL,
        'Panel de administración': ADMIN_URL,
        'Catálogos': CATALOGS_URL
    }
    
    resultados = {}
    
    for nombre, url in paginas.items():
        try:
            logger.info(f"Verificando botones y enlaces en {nombre} ({url})...")
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                enlaces = soup.find_all('a')
                botones = soup.find_all('button')
                
                logger.info(f"✅ Página {nombre}: {len(enlaces)} enlaces y {len(botones)} botones encontrados")
                
                # Verificar enlaces
                enlaces_info = []
                for enlace in enlaces:
                    href = enlace.get('href')
                    texto = enlace.get_text().strip()
                    if href and texto:
                        enlaces_info.append({
                            'href': href,
                            'texto': texto
                        })
                
                # Verificar botones
                botones_info = []
                for boton in botones:
                    tipo = boton.get('type')
                    texto = boton.get_text().strip()
                    if texto:
                        botones_info.append({
                            'tipo': tipo,
                            'texto': texto
                        })
                
                resultados[nombre] = {
                    'status': 'ok',
                    'codigo': response.status_code,
                    'enlaces': enlaces_info,
                    'botones': botones_info
                }
            
            elif response.status_code == 302:
                # Redirección
                logger.warning(f"⚠️ Acceso a {nombre} redirige a: {response.headers.get('Location')}")
                resultados[nombre] = {
                    'status': 'redirect',
                    'codigo': response.status_code,
                    'location': response.headers.get('Location')
                }
            
            else:
                logger.error(f"❌ Acceso a {nombre} fallido: código {response.status_code}")
                resultados[nombre] = {
                    'status': 'error',
                    'codigo': response.status_code
                }
        
        except Exception as e:
            logger.error(f"❌ Error al verificar botones y enlaces en {nombre}: {str(e)}")
            resultados[nombre] = {
                'status': 'error',
                'mensaje': str(e)
            }
    
    return resultados

def verificar_estructura_mongodb():
    """Verifica la estructura de la base de datos MongoDB."""
    client, db = conectar_mongodb()
    if client is None:
        logger.error("No se pudo conectar a MongoDB. Abortando verificación de estructura.")
        return None
    
    try:
        # Verificar colecciones
        colecciones = db.list_collection_names()
        logger.info(f"✅ Colecciones encontradas: {', '.join(colecciones)}")
        
        # Verificar usuarios
        usuarios = list(db.users.find({}, {'_id': 1, 'username': 1, 'email': 1, 'role': 1}))
        logger.info(f"✅ Usuarios encontrados: {len(usuarios)}")
        
        # Verificar catálogos
        catalogos = list(db.catalogs.find({}, {'_id': 1, 'name': 1, 'created_by': 1}))
        logger.info(f"✅ Catálogos encontrados: {len(catalogos)}")
        
        # Verificar tablas
        tablas = list(db.spreadsheets.find({}, {'_id': 1, 'name': 1, 'owner': 1}))
        logger.info(f"✅ Tablas encontradas: {len(tablas)}")
        
        return {
            'colecciones': colecciones,
            'usuarios': usuarios,
            'catalogos': catalogos,
            'tablas': tablas
        }
    
    except Exception as e:
        logger.error(f"❌ Error al verificar estructura de MongoDB: {str(e)}")
        return None
    
    finally:
        if client:
            client.close()
            logger.info("Conexión a MongoDB cerrada")

def verificar_permisos_rutas():
    """Verifica los permisos de las rutas de la aplicación."""
    rutas_admin = [
        '/admin/',
        '/admin/users',
        '/admin/catalogs'
    ]
    
    rutas_usuario = [
        '/dashboard_user',
        '/tables',
        '/catalogs/'
    ]
    
    resultados = {
        'admin': {},
        'usuario': {}
    }
    
    # Verificar rutas de administrador
    for ruta in rutas_admin:
        try:
            url = f"{BASE_URL}{ruta}"
            logger.info(f"Verificando acceso a ruta de administrador: {url}...")
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                logger.info(f"✅ Acceso a ruta de administrador {ruta} exitoso")
                resultados['admin'][ruta] = {
                    'status': 'ok',
                    'codigo': response.status_code
                }
            elif response.status_code == 302:
                logger.warning(f"⚠️ Ruta de administrador {ruta} redirige a: {response.headers.get('Location')}")
                resultados['admin'][ruta] = {
                    'status': 'redirect',
                    'codigo': response.status_code,
                    'location': response.headers.get('Location')
                }
            else:
                logger.error(f"❌ Acceso a ruta de administrador {ruta} fallido: código {response.status_code}")
                resultados['admin'][ruta] = {
                    'status': 'error',
                    'codigo': response.status_code
                }
        
        except Exception as e:
            logger.error(f"❌ Error al verificar ruta de administrador {ruta}: {str(e)}")
            resultados['admin'][ruta] = {
                'status': 'error',
                'mensaje': str(e)
            }
    
    # Verificar rutas de usuario
    for ruta in rutas_usuario:
        try:
            url = f"{BASE_URL}{ruta}"
            logger.info(f"Verificando acceso a ruta de usuario: {url}...")
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                logger.info(f"✅ Acceso a ruta de usuario {ruta} exitoso")
                resultados['usuario'][ruta] = {
                    'status': 'ok',
                    'codigo': response.status_code
                }
            elif response.status_code == 302:
                logger.warning(f"⚠️ Ruta de usuario {ruta} redirige a: {response.headers.get('Location')}")
                resultados['usuario'][ruta] = {
                    'status': 'redirect',
                    'codigo': response.status_code,
                    'location': response.headers.get('Location')
                }
            else:
                logger.error(f"❌ Acceso a ruta de usuario {ruta} fallido: código {response.status_code}")
                resultados['usuario'][ruta] = {
                    'status': 'error',
                    'codigo': response.status_code
                }
        
        except Exception as e:
            logger.error(f"❌ Error al verificar ruta de usuario {ruta}: {str(e)}")
            resultados['usuario'][ruta] = {
                'status': 'error',
                'mensaje': str(e)
            }
    
    return resultados

def verificar_funcionalidad_tablas():
    """Verifica la funcionalidad de creación y edición de tablas."""
    try:
        logger.info(f"Verificando acceso a la página de tablas ({TABLES_URL})...")
        response = requests.get(TABLES_URL, timeout=5)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            forms = soup.find_all('form')
            
            if forms:
                logger.info(f"✅ Página de tablas accesible ({len(forms)} formularios encontrados)")
                
                # Verificar formulario de creación de tabla
                form_crear = None
                for form in forms:
                    action = form.get('action', '')
                    if 'table' in action.lower() or not action:
                        form_crear = form
                        break
                
                if form_crear:
                    logger.info("✅ Formulario de creación de tabla encontrado")
                    
                    # Verificar campos del formulario
                    campos = form_crear.find_all(['input', 'textarea', 'select'])
                    logger.info(f"✅ Campos del formulario: {len(campos)}")
                    
                    # Verificar botón de envío
                    boton_envio = form_crear.find('button', {'type': 'submit'})
                    if boton_envio:
                        logger.info("✅ Botón de envío encontrado")
                    else:
                        logger.warning("⚠️ No se encontró botón de envío en el formulario")
                
                else:
                    logger.warning("⚠️ No se encontró formulario de creación de tabla")
            
            else:
                logger.warning("⚠️ No se encontraron formularios en la página de tablas")
            
            return {
                'status': 'ok',
                'codigo': response.status_code,
                'num_forms': len(forms) if forms else 0
            }
        
        elif response.status_code == 302:
            # Redirección
            logger.warning(f"⚠️ Acceso a página de tablas redirige a: {response.headers.get('Location')}")
            return {
                'status': 'redirect',
                'codigo': response.status_code,
                'location': response.headers.get('Location')
            }
        
        else:
            logger.error(f"❌ Acceso a página de tablas fallido: código {response.status_code}")
            return {
                'status': 'error',
                'codigo': response.status_code
            }
    
    except Exception as e:
        logger.error(f"❌ Error al verificar funcionalidad de tablas: {str(e)}")
        return {
            'status': 'error',
            'mensaje': str(e)
        }

def analizar_problemas_y_soluciones():
    """Analiza los problemas encontrados y propone soluciones."""
    problemas = []
    soluciones = []
    
    # Verificar rutas principales
    logger.info("\n=== VERIFICANDO RUTAS PRINCIPALES ===")
    rutas_principales = verificar_rutas_principales()
    
    # Verificar formularios
    logger.info("\n=== VERIFICANDO FORMULARIOS ===")
    formularios = verificar_formularios()
    
    # Verificar botones y enlaces
    logger.info("\n=== VERIFICANDO BOTONES Y ENLACES ===")
    botones_enlaces = verificar_botones_y_enlaces()
    
    # Verificar estructura de MongoDB
    logger.info("\n=== VERIFICANDO ESTRUCTURA DE MONGODB ===")
    estructura_mongodb = verificar_estructura_mongodb()
    
    # Verificar permisos de rutas
    logger.info("\n=== VERIFICANDO PERMISOS DE RUTAS ===")
    permisos_rutas = verificar_permisos_rutas()
    
    # Verificar funcionalidad de tablas
    logger.info("\n=== VERIFICANDO FUNCIONALIDAD DE TABLAS ===")
    funcionalidad_tablas = verificar_funcionalidad_tablas()
    
    # Analizar problemas en rutas principales
    for nombre, info in rutas_principales.items():
        if info.get('status') != 'ok':
            problemas.append(f"Problema de acceso a {nombre}: {info.get('mensaje', 'Error desconocido')}")
            
            if info.get('status') == 'redirect':
                soluciones.append(f"Corregir redirección de {nombre} a {info.get('location')}")
            else:
                soluciones.append(f"Verificar permisos y configuración de la ruta {nombre}")
    
    # Analizar problemas en formularios
    for nombre, info in formularios.items():
        if info.get('status') != 'ok':
            problemas.append(f"Problema con formulario {nombre}: {info.get('mensaje', 'Error desconocido')}")
            
            if info.get('status') == 'redirect':
                soluciones.append(f"Corregir redirección del formulario {nombre} a {info.get('location')}")
            else:
                soluciones.append(f"Verificar configuración del formulario {nombre}")
    
    # Analizar problemas en funcionalidad de tablas
    if funcionalidad_tablas.get('status') != 'ok':
        problemas.append(f"Problema con la funcionalidad de tablas: {funcionalidad_tablas.get('mensaje', 'Error desconocido')}")
        
        if funcionalidad_tablas.get('status') == 'redirect':
            soluciones.append(f"Corregir redirección de la página de tablas a {funcionalidad_tablas.get('location')}")
        else:
            soluciones.append("Verificar configuración de la funcionalidad de tablas")
    
    # Resumen
    logger.info("\n=== RESUMEN DE PROBLEMAS Y SOLUCIONES ===")
    
    if problemas:
        logger.info("Problemas encontrados:")
        for i, problema in enumerate(problemas, 1):
            logger.info(f"{i}. {problema}")
        
        logger.info("\nSoluciones propuestas:")
        for i, solucion in enumerate(soluciones, 1):
            logger.info(f"{i}. {solucion}")
    else:
        logger.info("No se encontraron problemas significativos.")
    
    return {
        'problemas': problemas,
        'soluciones': soluciones,
        'rutas_principales': rutas_principales,
        'formularios': formularios,
        'botones_enlaces': botones_enlaces,
        'estructura_mongodb': estructura_mongodb,
        'permisos_rutas': permisos_rutas,
        'funcionalidad_tablas': funcionalidad_tablas
    }

def main():
    """Función principal que ejecuta el diagnóstico completo."""
    logger.info("Iniciando diagnóstico completo...")
    
    resultados = analizar_problemas_y_soluciones()
    
    # Guardar resultados en un archivo JSON
    try:
        with open('diagnostico_completo_resultados.json', 'w') as f:
            json.dump(resultados, f, indent=2, default=str)
        logger.info("✅ Resultados guardados en diagnostico_completo_resultados.json")
    except Exception as e:
        logger.error(f"❌ Error al guardar resultados: {str(e)}")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
