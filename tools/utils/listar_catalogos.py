#!/usr/bin/env python3
"""
Script para listar todos los catálogos disponibles
"""

import os
from datetime import datetime

from dotenv import load_dotenv
from pymongo import MongoClient


def listar_catalogos():
    """Lista todos los catálogos disponibles"""

    print("📋 LISTANDO CATÁLOGOS DISPONIBLES")
    print("=" * 50)

    load_dotenv()

    # Configuración MongoDB
    mongo_uri = "mongodb+srv://edfrutos:rYjwUC6pUNrLtbaI@cluster0.pmokh.mongodb.net/app_catalogojoyero_nueva?retryWrites=true&w=majority"

    try:
        # Conectar a MongoDB
        client = MongoClient(mongo_uri)
        db = client.get_default_database()

        # Buscar en spreadsheets
        print("   🔍 Buscando en colección 'spreadsheets'...")
        spreadsheets = list(db['spreadsheets'].find({}, {'_id': 1, 'name': 1, 'created_at': 1}).limit(10))

        print(f"   📊 Total encontrados: {len(spreadsheets)}")

        for i, doc in enumerate(spreadsheets):
            doc_id = str(doc['_id'])
            name = doc.get('name', 'Sin nombre')
            created_at = doc.get('created_at', 'Sin fecha')

            if isinstance(created_at, datetime):
                created_str = created_at.strftime('%Y-%m-%d %H:%M:%S')
            else:
                created_str = str(created_at)

            print(f"   [{i+1}] ID: {doc_id}")
            print(f"       📝 Nombre: {name}")
            print(f"       📅 Creado: {created_str}")
            print()

        # Buscar en catalogs también
        print("   🔍 Buscando en colección 'catalogs'...")
        catalogs = list(db['catalogs'].find({}, {'_id': 1, 'name': 1, 'created_at': 1}).limit(10))

        print(f"   📊 Total encontrados: {len(catalogs)}")

        for i, doc in enumerate(catalogs):
            doc_id = str(doc['_id'])
            name = doc.get('name', 'Sin nombre')
            created_at = doc.get('created_at', 'Sin fecha')

            if isinstance(created_at, datetime):
                created_str = created_at.strftime('%Y-%m-%d %H:%M:%S')
            else:
                created_str = str(created_at)

            print(f"   [{i+1}] ID: {doc_id}")
            print(f"       📝 Nombre: {name}")
            print(f"       📅 Creado: {created_str}")
            print()

        return True

    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    listar_catalogos()
