#!/usr/bin/env python3
"""
Script para buscar el catálogo creado ayer
"""

import os
from datetime import datetime, timedelta

from dotenv import load_dotenv
from pymongo import MongoClient


def buscar_catalogo_ayer():
    """Busca el catálogo creado ayer"""

    print("🔍 BUSCANDO CATÁLOGO DE AYER")
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

        # Calcular fecha de ayer
        ayer = datetime.now() - timedelta(days=1)
        fecha_inicio = ayer.replace(hour=0, minute=0, second=0, microsecond=0)
        fecha_fin = ayer.replace(hour=23, minute=59, second=59, microsecond=999999)

        print(f"   📅 Buscando entre: {fecha_inicio} y {fecha_fin}")

        # Buscar en catalogs
        print("\n   🔍 Buscando en colección 'catalogs'...")
        catalogs = list(
            db["catalogs"].find(
                {"created_at": {"$gte": fecha_inicio, "$lte": fecha_fin}},
                {"_id": 1, "name": 1, "created_at": 1, "rows": 1},
            )
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

            # Mostrar primeras filas
            for j, row in enumerate(rows[:2]):
                images = row.get("images", [])
                if isinstance(images, str):
                    import json

                    try:
                        images = json.loads(images)
                    except BaseException:
                        images = [images]

                print(f"       📄 Fila {j+1}: {len(images)} imágenes")
                for k, img in enumerate(images[:3]):
                    print(f"          [{k+1}] {img}")
                if len(images) > 3:
                    print(f"          ... y {len(images) - 3} más")

        # Buscar en spreadsheets también
        print("\n   🔍 Buscando en colección 'spreadsheets'...")
        spreadsheets = list(
            db["spreadsheets"].find(
                {"created_at": {"$gte": fecha_inicio, "$lte": fecha_fin}},
                {"_id": 1, "name": 1, "created_at": 1, "rows": 1},
            )
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

        return True

    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    buscar_catalogo_ayer()
