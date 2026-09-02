#!/usr/bin/env python3
"""
Script para buscar todos los catálogos recientes
"""

import os
from datetime import datetime, timedelta

from dotenv import load_dotenv
from pymongo import MongoClient


def buscar_catalogos_recientes():
    """Busca todos los catálogos recientes"""

    print("🔍 BUSCANDO CATÁLOGOS RECIENTES")
    print("=" * 50)

    load_dotenv()

    # Configuración MongoDB
    mongo_uri = os.environ.get("MONGO_URI")
    if not mongo_uri:
        print("❌ Define MONGO_URI en el archivo .env")
        return

    try:
        # Conectar a MongoDB
        client = MongoClient(mongo_uri)
        db = client.get_default_database()

        # Buscar en catalogs (últimos 30 días)
        print("\n   🔍 Buscando en colección 'catalogs' (últimos 30 días)...")
        fecha_limite = datetime.now() - timedelta(days=30)

        catalogs = list(
            db["catalogs"]
            .find(
                {"created_at": {"$gte": fecha_limite}},
                {"_id": 1, "name": 1, "created_at": 1, "rows": 1},
            )
            .sort("created_at", -1)
        )

        print(f"   📊 Encontrados: {len(catalogs)}")

        for i, doc in enumerate(catalogs):
            doc_id = str(doc["_id"])
            name = doc.get("name", "Sin nombre")
            created_at = doc.get("created_at", "Sin fecha")
            rows = doc.get("rows", [])

            if isinstance(created_at, datetime):
                created_str = created_at.strftime("%Y-%m-%d %H:%M:%S")
            else:
                created_str = str(created_at)

            print(f"\n   [{i+1}] ID: {doc_id}")
            print(f"       📝 Nombre: {name}")
            print(f"       📅 Creado: {created_str}")
            print(f"       📊 Filas: {len(rows)}")

            # Mostrar primeras filas con imágenes
            for j, row in enumerate(rows[:2]):
                images = row.get("images", [])
                if isinstance(images, str):
                    import json

                    try:
                        images = json.loads(images)
                    except BaseException:
                        images = [images]

                if images:
                    print(f"       📄 Fila {j+1}: {len(images)} imágenes")
                    for k, img in enumerate(images[:3]):
                        print(f"          [{k+1}] {img}")
                    if len(images) > 3:
                        print(f"          ... y {len(images) - 3} más")

        # Buscar en spreadsheets también
        print("\n   🔍 Buscando en colección 'spreadsheets' (últimos 30 días)...")
        spreadsheets = list(
            db["spreadsheets"]
            .find(
                {"created_at": {"$gte": fecha_limite}},
                {"_id": 1, "name": 1, "created_at": 1, "rows": 1},
            )
            .sort("created_at", -1)
        )

        print(f"   📊 Encontrados: {len(spreadsheets)}")

        for i, doc in enumerate(spreadsheets):
            doc_id = str(doc["_id"])
            name = doc.get("name", "Sin nombre")
            created_at = doc.get("created_at", "Sin fecha")
            rows = doc.get("rows", [])

            if isinstance(created_at, datetime):
                created_str = created_at.strftime("%Y-%m-%d %H:%M:%S")
            else:
                created_str = str(created_at)

            print(f"\n   [{i+1}] ID: {doc_id}")
            print(f"       📝 Nombre: {name}")
            print(f"       📅 Creado: {created_str}")
            print(f"       📊 Filas: {len(rows)}")

            # Mostrar primeras filas con imágenes
            for j, row in enumerate(rows[:2]):
                images = row.get("images", [])
                if isinstance(images, str):
                    import json

                    try:
                        images = json.loads(images)
                    except BaseException:
                        images = [images]

                if images:
                    print(f"       📄 Fila {j+1}: {len(images)} imágenes")
                    for k, img in enumerate(images[:3]):
                        print(f"          [{k+1}] {img}")
                    if len(images) > 3:
                        print(f"          ... y {len(images) - 3} más")

        return True

    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    buscar_catalogos_recientes()
