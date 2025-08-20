#!/usr/bin/env python3

import datetime
import json
import logging
import os
import sys
import traceback

import certifi
import requests
from bson.objectid import ObjectId
from pymongo import MongoClient

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Cargar configuración
try:
    from config import Config
    MONGO_URI = Config.MONGO_URI
except ImportError:
    MONGO_URI = os.environ.get('MONGO_URI', 'mongodb+srv://admin:admin123@cluster0.pmokh.mongodb.net/app_catalogojoyero_nueva?retryWrites=true&w=majority')

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

def verificar_colecciones(db):
    """Verifica las colecciones disponibles en la base de datos."""
    colecciones = db.list_collection_names()
    logger.info(f"Colecciones disponibles: {colecciones}")

    # Identificar colecciones relacionadas con catálogos
    catalogs_collections = [col for col in colecciones if 'catalog' in col.lower() or 'spreadsheet' in col.lower()]
    logger.info(f"Colecciones relacionadas con catálogos: {catalogs_collections}")

    return colecciones, catalogs_collections

def verificar_documentos_catalogs(db):
    """Verifica los documentos en la colección catalogs."""
    catalogs_count = db.catalogs.count_documents({})
    logger.info(f"Colección catalogs: {catalogs_count} documentos")

    if catalogs_count > 0:
        # Mostrar un ejemplo de documento
        sample_doc = db.catalogs.find_one()
        logger.info(f"Ejemplo de documento en catalogs: {sample_doc}")

        # Verificar si los documentos tienen el campo created_by
        docs_sin_created_by = db.catalogs.count_documents({"created_by": {"$exists": False}})
        if docs_sin_created_by > 0:
            logger.warning(f"⚠️ Hay {docs_sin_created_by} documentos sin el campo created_by")
            return False

        # Verificar si los documentos tienen el campo rows
        docs_sin_rows = db.catalogs.count_documents({"rows": {"$exists": False}})
        if docs_sin_rows > 0:
            logger.warning(f"⚠️ Hay {docs_sin_rows} documentos sin el campo rows")
            return False

        # Verificar si los documentos tienen el campo headers
        docs_sin_headers = db.catalogs.count_documents({"headers": {"$exists": False}})
        if docs_sin_headers > 0:
            logger.warning(f"⚠️ Hay {docs_sin_headers} documentos sin el campo headers")
            return False

        return True
    else:
        logger.warning("⚠️ La colección catalogs está vacía")
        return False

def corregir_permisos_catalogs(db):
    """Corrige los problemas de permisos en la colección catalogs."""
    # 1. Asegurarse de que todos los documentos tengan el campo created_by
    docs_sin_created_by = list(db.catalogs.find({"created_by": {"$exists": False}}))

    if docs_sin_created_by:
        logger.info(f"Corrigiendo {len(docs_sin_created_by)} documentos sin created_by...")

        for doc in docs_sin_created_by:
            db.catalogs.update_one(
                {"_id": doc["_id"]},
                {"$set": {"created_by": "admin@example.com"}}
            )
        logger.info("✅ Documentos actualizados con created_by")
    else:
        logger.info("✅ Todos los documentos tienen el campo created_by")

    # 2. Verificar si hay catálogos sin filas (rows)
    docs_sin_rows = list(db.catalogs.find({"rows": {"$exists": False}}))

    if docs_sin_rows:
        logger.info(f"Corrigiendo {len(docs_sin_rows)} documentos sin el campo rows...")

        for doc in docs_sin_rows:
            db.catalogs.update_one(
                {"_id": doc["_id"]},
                {"$set": {"rows": []}}
            )
        logger.info("✅ Documentos actualizados con el campo rows")
    else:
        logger.info("✅ Todos los documentos tienen el campo rows")

    # 3. Verificar si hay catálogos sin headers
    docs_sin_headers = list(db.catalogs.find({"headers": {"$exists": False}}))

    if docs_sin_headers:
        logger.info(f"Corrigiendo {len(docs_sin_headers)} documentos sin el campo headers...")

        for doc in docs_sin_headers:
            # Asignar headers predeterminados
            db.catalogs.update_one(
                {"_id": doc["_id"]},
                {"$set": {"headers": ["Número", "Descripción", "Valor"]}}
            )
        logger.info("✅ Documentos actualizados con el campo headers")
    else:
        logger.info("✅ Todos los documentos tienen el campo headers")

    return True

def verificar_rutas_catalogs():
    """Verifica si las rutas de catálogos están funcionando correctamente."""
    try:
        # Verificar la ruta principal de catálogos
        response = requests.get('http://127.0.0.1:8002/catalogs/')
        logger.info(f"Respuesta de /catalogs/: Código {response.status_code}")

        if response.status_code == 200:
            logger.info("✅ La ruta /catalogs/ está funcionando correctamente")
            return True
        else:
            logger.warning(f"⚠️ La ruta /catalogs/ devolvió un código de estado {response.status_code}")
            logger.info(f"Contenido de la respuesta: {response.text[:500]}...")
            return False
    except Exception as e:
        logger.error(f"❌ Error al verificar rutas: {str(e)}")
        return False

def verificar_registro_blueprint():
    """Verifica si el blueprint de catálogos está registrado correctamente."""
    try:
        # Leer el archivo app.py
        with open('app.py') as f:
            contenido = f.read()

        # Verificar si el blueprint está importado
        if 'from app.routes.catalogs_routes import catalogs_bp' in contenido:
            logger.info("✅ El blueprint catalogs_bp está importado correctamente")
        else:
            logger.warning("⚠️ No se encontró la importación del blueprint catalogs_bp")
            return False

        # Verificar si el blueprint está registrado
        if 'app.register_blueprint(catalogs_bp)' in contenido:
            logger.info("✅ El blueprint catalogs_bp está registrado correctamente")
            return True
        else:
            logger.warning("⚠️ No se encontró el registro del blueprint catalogs_bp")
            return False
    except Exception as e:
        logger.error(f"❌ Error al verificar registro de blueprint: {str(e)}")
        return False

def verificar_plantillas():
    """Verifica si existen las plantillas necesarias para los catálogos."""
    templates_dir = "app/templates"
    plantillas_requeridas = [
        "catalogs.html",
        "ver_catalogo.html",
        "agregar_fila.html",
        "editar_fila.html",
        "editar_catalogo.html"
    ]

    plantillas_encontradas = []
    plantillas_faltantes = []

    for plantilla in plantillas_requeridas:
        ruta_plantilla = os.path.join(templates_dir, plantilla)
        if os.path.exists(ruta_plantilla):
            plantillas_encontradas.append(plantilla)
        else:
            plantillas_faltantes.append(plantilla)

    logger.info(f"Plantillas encontradas: {plantillas_encontradas}")

    if plantillas_faltantes:
        logger.warning(f"⚠️ Plantillas faltantes: {plantillas_faltantes}")
    else:
        logger.info("✅ Todas las plantillas requeridas están disponibles")

    return plantillas_encontradas, plantillas_faltantes

def crear_catalogo_prueba(db):
    """Crea un catálogo de prueba si no existe."""
    catalogo_prueba = db.catalogs.find_one({"name": "Catálogo de Prueba"})

    if not catalogo_prueba:
        # Crear catálogo de prueba
        catalogo = {
            "name": "Catálogo de Prueba",
            "description": "Catálogo creado para pruebas de acceso",
            "headers": ["Número", "Descripción", "Valor"],
            "rows": [
                {"Número": "1", "Descripción": "Item de prueba 1", "Valor": "100"},
                {"Número": "2", "Descripción": "Item de prueba 2", "Valor": "200"}
            ],
            "created_by": "admin@example.com",
            "created_at": datetime.datetime.now()
        }
        db.catalogs.insert_one(catalogo)
        logger.info("✅ Catálogo de prueba creado")
        return True
    else:
        logger.info("ℹ️ El catálogo de prueba ya existe")
        return False

def verificar_archivo_catalogs_routes():
    """Verifica el contenido del archivo catalogs_routes.py."""
    try:
        # Leer el archivo catalogs_routes.py
        with open('app/routes/catalogs_routes.py') as f:
            contenido = f.read()

        # Verificar si la función edit usa la plantilla correcta
        if 'return render_template("editar_catalogo.html"' in contenido:
            logger.info("✅ La función edit usa la plantilla correcta")
        else:
            logger.warning("⚠️ La función edit no usa la plantilla correcta")

            # Corregir la ruta de la plantilla
            contenido_corregido = contenido.replace(
                'return render_template("admin/editar_catalogo.html", catalog=catalog, session=session)',
                'return render_template("editar_catalogo.html", catalog=catalog, session=session)'
            )

            # Guardar el archivo corregido
            with open('app/routes/catalogs_routes.py', 'w') as f:
                f.write(contenido_corregido)

            logger.info("✅ Se ha corregido la ruta de la plantilla en la función edit")
            return True

        # Verificar si las funciones delete_row y delete_catalog están implementadas correctamente
        if 'mongo.db.catalogs.update_one(' in contenido and '"$pull": {' in contenido:
            logger.info("✅ La función delete_row está implementada correctamente")
        else:
            logger.warning("⚠️ La función delete_row no está implementada correctamente")
            return False

        if 'mongo.db.catalogs.delete_one(' in contenido:
            logger.info("✅ La función delete_catalog está implementada correctamente")
            return True
        else:
            logger.warning("⚠️ La función delete_catalog no está implementada correctamente")
            return False
    except Exception as e:
        logger.error(f"❌ Error al verificar archivo catalogs_routes.py: {str(e)}")
        return False

def main():
    """Función principal que ejecuta el diagnóstico y corrección."""
    logger.info("Iniciando diagnóstico y corrección de problemas con los catálogos...")

    # Conectar a MongoDB
    client, db = conectar_mongodb()
    if client is None:
        logger.error("No se pudo conectar a MongoDB. Abortando.")
        return False

    try:
        # 1. Verificar colecciones
        colecciones, catalogs_collections = verificar_colecciones(db)

        # 2. Verificar documentos en catalogs
        docs_ok = verificar_documentos_catalogs(db)

        # 3. Corregir permisos en catalogs
        permisos_corregidos = corregir_permisos_catalogs(db)

        # 4. Verificar plantillas
        plantillas_encontradas, plantillas_faltantes = verificar_plantillas()

        # 5. Verificar registro de blueprint
        blueprint_ok = verificar_registro_blueprint()

        # 6. Verificar archivo catalogs_routes.py
        routes_ok = verificar_archivo_catalogs_routes()

        # 7. Crear catálogo de prueba
        catalogo_creado = crear_catalogo_prueba(db)

        # 8. Verificar rutas de catálogos
        rutas_ok = verificar_rutas_catalogs()

        # Resumen
        logger.info("\n=== RESUMEN DEL DIAGNÓSTICO Y CORRECCIÓN ===")
        logger.info(f"1. Colecciones relacionadas con catálogos: {catalogs_collections}")
        logger.info(f"2. Estado de documentos en catalogs: {'✅ OK' if docs_ok else '❌ Con problemas'}")
        logger.info(f"3. Corrección de permisos: {'✅ Completada' if permisos_corregidos else '❌ Fallida'}")
        logger.info(f"4. Plantillas encontradas: {plantillas_encontradas}")
        logger.info(f"5. Plantillas faltantes: {plantillas_faltantes}")
        logger.info(f"6. Registro de blueprint: {'✅ OK' if blueprint_ok else '❌ Con problemas'}")
        logger.info(f"7. Archivo catalogs_routes.py: {'✅ OK' if routes_ok else '❌ Con problemas'}")
        logger.info(f"8. Catálogo de prueba: {'✅ Creado' if catalogo_creado else 'ℹ️ Ya existía'}")
        logger.info(f"9. Rutas de catálogos: {'✅ OK' if rutas_ok else '❌ Con problemas'}")

        # Próximos pasos
        logger.info("\n=== PRÓXIMOS PASOS ===")
        logger.info("1. Reinicia la aplicación Flask para aplicar los cambios:")
        logger.info("   $ pkill -f 'python.*ejecutar_flask_directo.py'")
        logger.info("   $ python3 ejecutar_flask_directo.py")
        logger.info("2. Accede a la aplicación en http://127.0.0.1:8002")
        logger.info("3. Inicia sesión con credenciales de administrador:")
        logger.info("   - Email: admin@example.com")
        logger.info("   - Contraseña: admin123")
        logger.info("4. Navega a http://127.0.0.1:8002/catalogs para ver los catálogos")

        return True

    except Exception as e:
        logger.error(f"Error durante el diagnóstico y corrección: {str(e)}")
        logger.error(traceback.format_exc())
        return False

    finally:
        if client:
            client.close()
            logger.info("Conexión a MongoDB cerrada")

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
