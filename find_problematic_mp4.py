#!/usr/bin/env python3
"""
Búsqueda específica del archivo MP4 problemático en MongoDB
"""

import os
import sys
import json
from pathlib import Path


def load_environment():
    """Cargar variables de entorno desde archivos .env"""
    env_files = ['.env', '.env.local', '.env.production']
    env_vars = {}

    for env_file in env_files:
        env_path = Path(env_file)
        if env_path.exists():
            print(f'📁 Cargando {env_file}...')
            with open(env_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip().strip('"').strip("'")
                        env_vars[key] = value
                        os.environ[key] = value

    return env_vars

def main():
    # Cargar entorno
    env_vars = load_environment()

    from pymongo import MongoClient

    MONGODB_URI = os.getenv('MONGODB_URI')
    if not MONGODB_URI:
        print("❌ MONGODB_URI no encontrado")
        return

    client = MongoClient(MONGODB_URI)
    db = client['catalogo_tablas']
    
    problematic_file = 'cf342a562c104122a5ca9241bf1ef896_oUcGqQXIG8InPCfTAIeSA2gneLBJnRIInz4jwY.MP4'
    print(f'🔍 Búsqueda específica del archivo: {problematic_file}')
    
    # Listar todas las colecciones
    collections = db.list_collection_names()
    print(f'📚 Colecciones encontradas: {len(collections)}')

    found_any = False

    for collection_name in collections:
        if collection_name.startswith('system.'):
            continue

        print(f'\n🔍 Buscando en colección: {collection_name}')
        collection = db[collection_name]
        
        # Contar documentos
        count = collection.count_documents({})
        print(f'  📊 Documentos en {collection_name}: {count}')

        if count == 0:
            print(f'  ⚪ Colección vacía, omitiendo...')
            continue

        # Buscar el archivo específico
        query_results = list(collection.find({}, {'_id': 1, 'rows': 1, 'data': 1, 'nombre': 1, 'title': 1}))
        
        for doc in query_results:
            doc_id = str(doc.get('_id', 'Sin ID'))
            doc_name = doc.get('nombre', doc.get('title', 'Sin nombre'))

            # Buscar en el documento completo
            doc_str = str(doc)
            if problematic_file in doc_str:
                print(f'\n  ✅ ¡ENCONTRADO EN {collection_name}!')
                print(f'     📋 ID: {doc_id}')
                print(f'     📝 Nombre: {doc_name}')

                # Si hay rows, analizar cada fila
                if 'rows' in doc and isinstance(doc['rows'], list):
                    print(f'     📊 Total de filas: {len(doc["rows"])}')

                    for i, row in enumerate(doc['rows']):
                        if isinstance(row, dict):
                            row_str = str(row)
                            if problematic_file in row_str:
                                print(f'     🎯 FILA PROBLEMÁTICA #{i+1} (índice {i}):')
                                for key, value in row.items():
                                    if isinstance(value, str) and problematic_file in value:
                                        print(f'        🔑 Campo: {key}')
                                        print(f'        📄 Valor: {value}')
                                found_any = True

                # Buscar en otros campos también
                for key, value in doc.items():
                    if key not in ['_id', 'rows'] and isinstance(value, str) and problematic_file in value:
                        print(f'     🔑 Campo raíz: {key}')
                        print(f'     📄 Valor: {value}')
                        found_any = True

    if not found_any:
        print(f'\n❌ No se encontró el archivo {problematic_file} en ninguna colección')
        print(f'   Esto puede significar:')
        print(f'   1. El archivo fue eliminado de la BD pero permanece en cache del navegador')
        print(f'   2. El archivo está siendo referenciado desde localStorage')
        print(f'   3. Hay algún problema con la indexación/búsqueda')

        # Buscar cualquier archivo MP4 similar
        print(f'\n🔍 Buscando archivos MP4 similares...')
        for collection_name in collections:
            if collection_name.startswith('system.'):
                continue
            collection = db[collection_name]
            query_results = list(collection.find({}, {'_id': 1, 'rows': 1}))

            for doc in query_results:
                if 'rows' in doc and isinstance(doc['rows'], list):
                    for i, row in enumerate(doc['rows']):
                        if isinstance(row, dict):
                            for key, value in row.items():
                                if isinstance(value, str) and '.MP4' in value.upper():
                                    print(f'  📁 {collection_name} - Fila {i+1}: {key} = {value}')

    client.close()


if __name__ == "__main__":
    main()
