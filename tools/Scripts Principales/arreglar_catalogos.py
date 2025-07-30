#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para diagnosticar y corregir problemas con la funcionalidad de catálogos
"""

import os
import sys
import logging
import certifi
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from bson.objectid import ObjectId
import datetime
import json

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Obtener la URI de MongoDB
mongo_uri = os.getenv('MONGO_URI', 'mongodb+srv://edfrutos:rYjwUC6pUNrLtbaI@cluster0.pmokh.mongodb.net/app_catalogojoyero_nueva?retryWrites=true&w=majority')

def conectar_mongodb():
    """Conectar a MongoDB y devolver el cliente y la base de datos"""
    try:
        client = MongoClient(
            mongo_uri,
            tls=True,
            tlsCAFile=certifi.where(),
            server_api=ServerApi('1')
        )
        
        # Verificar conexión
        client.admin.command('ping')
        logger.info("✅ Conexión a MongoDB establecida correctamente")
        
        # Seleccionar base de datos
        db = client["app_catalogojoyero_nueva"]
        return client, db
    except Exception as e:
        logger.error(f"❌ Error al conectar a MongoDB: {str(e)}")
        sys.exit(1)

def listar_colecciones(db):
    """Listar todas las colecciones en la base de datos"""
    colecciones = db.list_collection_names()
    logger.info(f"Colecciones disponibles: {colecciones}")
    return colecciones

def verificar_colecciones_catalogo(db):
    """Verificar las colecciones relacionadas con catálogos"""
    colecciones = listar_colecciones(db)
    
    # Verificar colecciones relacionadas con catálogos
    colecciones_catalogo = [c for c in colecciones if 'catalog' in c.lower() or 'spreadsheet' in c.lower()]
    logger.info(f"Colecciones relacionadas con catálogos: {colecciones_catalogo}")
    
    # Verificar número de documentos en cada colección
    for coleccion in colecciones_catalogo:
        count = db[coleccion].count_documents({})
        logger.info(f"Colección {coleccion}: {count} documentos")
    
    return colecciones_catalogo

def verificar_coleccion_67b8c24a7fdc72dd4d8703cf(db):
    """Verificar la colección 67b8c24a7fdc72dd4d8703cf"""
    coleccion = "67b8c24a7fdc72dd4d8703cf"
    if coleccion in db.list_collection_names():
        count = db[coleccion].count_documents({})
        logger.info(f"Colección {coleccion}: {count} documentos")
        
        # Obtener una muestra de documentos
        documentos = list(db[coleccion].find().limit(3))
        for doc in documentos:
            if '_id' in doc:
                doc['_id'] = str(doc['_id'])
            logger.info(f"Muestra de documento: {doc}")
        
        return count, documentos
    else:
        logger.warning(f"⚠️ La colección {coleccion} no existe")
        return 0, []

def migrar_datos_a_catalogs(db):
    """Migrar datos de 67b8c24a7fdc72dd4d8703cf a catalogs"""
    origen = "67b8c24a7fdc72dd4d8703cf"
    destino = "catalogs"
    
    # Verificar si la colección de origen existe
    if origen not in db.list_collection_names():
        logger.warning(f"⚠️ La colección de origen {origen} no existe")
        return False
    
    # Verificar si la colección de destino está vacía
    if destino in db.list_collection_names() and db[destino].count_documents({}) > 0:
        logger.warning(f"⚠️ La colección de destino {destino} ya contiene documentos")
        respuesta = input("¿Deseas continuar y sobrescribir los datos? (s/n): ")
        if respuesta.lower() != 's':
            logger.info("Operación cancelada por el usuario")
            return False
    
    # Obtener todos los documentos de la colección de origen
    documentos = list(db[origen].find())
    logger.info(f"Se encontraron {len(documentos)} documentos en la colección {origen}")
    
    # Migrar documentos a la colección de destino
    if documentos:
        # Eliminar documentos existentes en la colección de destino
        if destino in db.list_collection_names():
            db[destino].delete_many({})
        
        # Insertar documentos en la colección de destino
        resultado = db[destino].insert_many(documentos)
        logger.info(f"✅ Se migraron {len(resultado.inserted_ids)} documentos a la colección {destino}")
        return True
    else:
        logger.warning(f"⚠️ No hay documentos para migrar desde {origen}")
        return False

def crear_catalogo_ejemplo(db):
    """Crear un catálogo de ejemplo"""
    catalogo = {
        "name": "Catálogo de Ejemplo",
        "headers": ["Nombre", "Descripción", "Precio", "Stock"],
        "rows": [
            {
                "Nombre": "Producto 1",
                "Descripción": "Descripción del producto 1",
                "Precio": "100",
                "Stock": "10",
                "imagenes": []
            },
            {
                "Nombre": "Producto 2",
                "Descripción": "Descripción del producto 2",
                "Precio": "200",
                "Stock": "20",
                "imagenes": []
            },
            {
                "Nombre": "Producto 3",
                "Descripción": "Descripción del producto 3",
                "Precio": "300",
                "Stock": "30",
                "imagenes": []
            }
        ],
        "created_by": "admin",
        "created_at": datetime.datetime.utcnow(),
        "updated_at": datetime.datetime.utcnow()
    }
    
    resultado = db["catalogs"].insert_one(catalogo)
    logger.info(f"✅ Catálogo de ejemplo creado con ID: {resultado.inserted_id}")
    return str(resultado.inserted_id)

def corregir_rutas_catalogo():
    """Corregir las rutas de catálogo en el archivo catalogs_routes.py"""
    archivo = "/app/routes/catalogs_routes.py"
    
    try:
        with open(archivo, 'r') as f:
            contenido = f.read()
        
        # Verificar si hay referencias a mongo.db.catalogs
        if "mongo.db.catalogs" in contenido:
            logger.info("✅ El archivo ya está utilizando la colección 'catalogs'")
        else:
            # Reemplazar mongo.db.catalogo_tablas por mongo.db.catalogs
            contenido_nuevo = contenido.replace("mongo.db.catalogo_tablas", "mongo.db.catalogs")
            
            # Guardar el archivo modificado
            with open(archivo, 'w') as f:
                f.write(contenido_nuevo)
            
            logger.info(f"✅ Se corrigieron las referencias a la colección en {archivo}")
        
        return True
    except Exception as e:
        logger.error(f"❌ Error al corregir las rutas de catálogo: {str(e)}")
        return False

def verificar_plantillas():
    """Verificar las plantillas relacionadas con catálogos"""
    directorio_plantillas = "/app/templates"
    plantillas_catalogo = [
        "catalogs.html",
        "ver_catalogo.html",
        "editar_catalogo.html",
        "agregar_fila.html",
        "editar_fila.html"
    ]
    
    plantillas_encontradas = []
    plantillas_faltantes = []
    
    for plantilla in plantillas_catalogo:
        ruta_plantilla = os.path.join(directorio_plantillas, plantilla)
        if os.path.exists(ruta_plantilla):
            plantillas_encontradas.append(plantilla)
        else:
            plantillas_faltantes.append(plantilla)
    
    logger.info(f"Plantillas encontradas: {plantillas_encontradas}")
    if plantillas_faltantes:
        logger.warning(f"⚠️ Plantillas faltantes: {plantillas_faltantes}")
    
    return plantillas_encontradas, plantillas_faltantes

def crear_plantillas_faltantes(plantillas_faltantes):
    """Crear las plantillas faltantes"""
    directorio_plantillas = "/app/templates"
    
    # Contenido básico para las plantillas
    contenidos = {
        "catalogs.html": """
{% extends "base.html" %}
{% block title %}Catálogos{% endblock %}
{% block content %}
<div class="container mt-4">
    <h1>Mis Catálogos</h1>
    <div class="mb-3">
        <a href="{{ url_for('catalogs.create') }}" class="btn btn-primary">Crear Nuevo Catálogo</a>
    </div>
    
    {% if catalogs %}
    <div class="row">
        {% for catalog in catalogs %}
        <div class="col-md-4 mb-4">
            <div class="card">
                <div class="card-body">
                    <h5 class="card-title">{{ catalog.name }}</h5>
                    <p class="card-text">Filas: {{ catalog.row_count }}</p>
                    <a href="{{ url_for('catalogs.view', catalog_id=catalog._id_str) }}" class="btn btn-info">Ver</a>
                </div>
            </div>
        </div>
        {% endfor %}
    </div>
    {% else %}
    <div class="alert alert-info">
        No hay catálogos disponibles. Crea uno para comenzar.
    </div>
    {% endif %}
</div>
{% endblock %}
        """,
        "ver_catalogo.html": """
{% extends "base.html" %}
{% block title %}Ver Catálogo{% endblock %}
{% block content %}
<div class="container mt-4">
    <h1>{{ catalog.name }}</h1>
    <div class="mb-3">
        <a href="{{ url_for('catalogs.list') }}" class="btn btn-secondary">Volver a la lista</a>
        <a href="{{ url_for('catalogs.add_row', catalog_id=catalog._id) }}" class="btn btn-primary">Agregar Fila</a>
    </div>
    
    {% if catalog.rows %}
    <div class="table-responsive">
        <table class="table table-striped">
            <thead>
                <tr>
                    {% for header in catalog.headers %}
                    <th>{{ header }}</th>
                    {% endfor %}
                    <th>Acciones</th>
                </tr>
            </thead>
            <tbody>
                {% for row in catalog.rows %}
                <tr>
                    {% for header in catalog.headers %}
                    <td>{{ row[header] }}</td>
                    {% endfor %}
                    <td>
                        <a href="{{ url_for('catalogs.edit_row', catalog_id=catalog._id, row_index=loop.index0) }}" class="btn btn-sm btn-warning">Editar</a>
                        <a href="{{ url_for('catalogs.delete_row', catalog_id=catalog._id, row_index=loop.index0) }}" class="btn btn-sm btn-danger">Eliminar</a>
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
    {% else %}
    <div class="alert alert-info">
        Este catálogo no tiene filas. Agrega una para comenzar.
    </div>
    {% endif %}
</div>
{% endblock %}
        """,
        "editar_catalogo.html": """
{% extends "base.html" %}
{% block title %}Editar Catálogo{% endblock %}
{% block content %}
<div class="container mt-4">
    <h1>Editar Catálogo</h1>
    <form method="post">
        <div class="mb-3">
            <label for="name" class="form-label">Nombre del Catálogo</label>
            <input type="text" class="form-control" id="name" name="name" value="{{ catalog.name }}" required>
        </div>
        <div class="mb-3">
            <label for="headers" class="form-label">Encabezados (separados por comas)</label>
            <input type="text" class="form-control" id="headers" name="headers" value="{{ catalog.headers|join(', ') }}" required>
        </div>
        <button type="submit" class="btn btn-primary">Guardar Cambios</button>
        <a href="{{ url_for('catalogs.view', catalog_id=catalog._id) }}" class="btn btn-secondary">Cancelar</a>
    </form>
</div>
{% endblock %}
        """,
        "agregar_fila.html": """
{% extends "base.html" %}
{% block title %}Agregar Fila{% endblock %}
{% block content %}
<div class="container mt-4">
    <h1>Agregar Fila a {{ catalog.name }}</h1>
    <form method="post" enctype="multipart/form-data">
        {% for header in catalog.headers %}
        <div class="mb-3">
            <label for="{{ header }}" class="form-label">{{ header }}</label>
            <input type="text" class="form-control" id="{{ header }}" name="{{ header }}">
        </div>
        {% endfor %}
        <div class="mb-3">
            <label for="imagenes" class="form-label">Imágenes (opcional)</label>
            <input type="file" class="form-control" id="imagenes" name="imagenes" multiple>
        </div>
        <button type="submit" class="btn btn-primary">Guardar</button>
        <a href="{{ url_for('catalogs.view', catalog_id=catalog._id) }}" class="btn btn-secondary">Cancelar</a>
    </form>
</div>
{% endblock %}
        """,
        "editar_fila.html": """
{% extends "base.html" %}
{% block title %}Editar Fila{% endblock %}
{% block content %}
<div class="container mt-4">
    <h1>Editar Fila de {{ catalog.name }}</h1>
    <form method="post" enctype="multipart/form-data">
        {% for header in catalog.headers %}
        <div class="mb-3">
            <label for="{{ header }}" class="form-label">{{ header }}</label>
            <input type="text" class="form-control" id="{{ header }}" name="{{ header }}" value="{{ fila[header] }}">
        </div>
        {% endfor %}
        <div class="mb-3">
            <label for="imagenes" class="form-label">Imágenes (opcional)</label>
            <input type="file" class="form-control" id="imagenes" name="imagenes" multiple>
        </div>
        <button type="submit" class="btn btn-primary">Guardar Cambios</button>
        <a href="{{ url_for('catalogs.view', catalog_id=catalog._id) }}" class="btn btn-secondary">Cancelar</a>
    </form>
</div>
{% endblock %}
        """
    }
    
    for plantilla in plantillas_faltantes:
        if plantilla in contenidos:
            ruta_plantilla = os.path.join(directorio_plantillas, plantilla)
            try:
                with open(ruta_plantilla, 'w') as f:
                    f.write(contenidos[plantilla])
                logger.info(f"✅ Plantilla {plantilla} creada correctamente")
            except Exception as e:
                logger.error(f"❌ Error al crear la plantilla {plantilla}: {str(e)}")
    
    return True

def main():
    """Función principal"""
    logger.info("Iniciando diagnóstico y corrección de problemas con la funcionalidad de catálogos...")
    
    # Conectar a MongoDB
    client, db = conectar_mongodb()
    
    # Verificar colecciones relacionadas con catálogos
    colecciones_catalogo = verificar_colecciones_catalogo(db)
    
    # Verificar la colección 67b8c24a7fdc72dd4d8703cf
    count_67b8c24a, docs_67b8c24a = verificar_coleccion_67b8c24a7fdc72dd4d8703cf(db)
    
    # Verificar la colección catalogs
    if "catalogs" in db.list_collection_names():
        count_catalogs = db["catalogs"].count_documents({})
        logger.info(f"Colección catalogs: {count_catalogs} documentos")
    else:
        count_catalogs = 0
        logger.warning("⚠️ La colección catalogs no existe")
    
    # Migrar datos si es necesario
    if count_67b8c24a > 0 and count_catalogs == 0:
        logger.info("Migrando datos de 67b8c24a7fdc72dd4d8703cf a catalogs...")
        migrar_datos_a_catalogs(db)
    
    # Crear catálogo de ejemplo si no hay catálogos
    if db["catalogs"].count_documents({}) == 0:
        logger.info("Creando catálogo de ejemplo...")
        crear_catalogo_ejemplo(db)
    
    # Corregir rutas de catálogo
    corregir_rutas_catalogo()
    
    # Verificar plantillas
    plantillas_encontradas, plantillas_faltantes = verificar_plantillas()
    
    # Crear plantillas faltantes
    if plantillas_faltantes:
        logger.info("Creando plantillas faltantes...")
        crear_plantillas_faltantes(plantillas_faltantes)
    
    # Resumen
    logger.info("\n=== RESUMEN DEL DIAGNÓSTICO Y CORRECCIÓN ===")
    logger.info(f"1. Colecciones relacionadas con catálogos: {colecciones_catalogo}")
    logger.info(f"2. Documentos en 67b8c24a7fdc72dd4d8703cf: {count_67b8c24a}")
    logger.info(f"3. Documentos en catalogs: {db['catalogs'].count_documents({})}")
    logger.info(f"4. Plantillas encontradas: {plantillas_encontradas}")
    logger.info(f"5. Plantillas creadas: {plantillas_faltantes}")
    
    logger.info("\n=== PRÓXIMOS PASOS ===")
    logger.info("1. Reinicia la aplicación Flask para aplicar los cambios:")
    logger.info("   $ pkill -f 'python.*ejecutar_flask_directo.py'")
    logger.info("   $ python3 ejecutar_flask_directo.py")
    logger.info("2. Accede a la aplicación en http://127.0.0.1:8002")
    logger.info("3. Navega a http://127.0.0.1:8002/catalogs para ver los catálogos")

if __name__ == "__main__":
    main()
