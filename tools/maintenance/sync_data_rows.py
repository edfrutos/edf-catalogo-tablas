#!/usr/bin/env python3
"""
Script para sincronizar los campos 'data' y 'rows' en todas las tablas
"""

import os
import sys
from dotenv import load_dotenv
from pymongo import MongoClient
from bson import ObjectId  # noqa: F401

# Cargar variables de entorno
load_dotenv()


def sync_data_rows():
    """Sincroniza los campos data y rows en todas las tablas"""

    # Conectar a MongoDB
    mongo_uri = os.getenv("MONGO_URI")
    if not mongo_uri:
        print("❌ Error: MONGO_URI no encontrado en las variables de entorno")
        return False

    try:
        client = MongoClient(mongo_uri)
        db = client.get_database()

        print("🔍 Buscando tablas con inconsistencias entre 'data' y 'rows'...")

        # Buscar en la colección spreadsheets
        spreadsheets_collection = db["spreadsheets"]

        # Buscar documentos donde data y rows no coincidan
        documentos = list(spreadsheets_collection.find({}))
        print(f"📊 Total de documentos encontrados: {len(documentos)}")

        documentos_actualizados = 0

        for doc in documentos:
            doc_id = doc["_id"]
            nombre = doc.get("name", "Sin nombre")
            owner = doc.get("owner", "Sin owner")

            data = doc.get("data", [])
            rows = doc.get("rows", [])

            print(f"\n🔧 Procesando: {nombre} (ID: {doc_id}, Owner: {owner})")
            print(f"   📋 data: {len(data)} elementos")
            print(f"   📋 rows: {len(rows)} elementos")

            actualizado = False

            # Caso 1: data existe pero rows no existe o está vacío
            if data and not rows:
                print(f"   📝 Copiando {len(data)} elementos de 'data' a 'rows'")
                result = spreadsheets_collection.update_one(
                    {"_id": doc_id}, {"$set": {"rows": data}}
                )
                if result.modified_count > 0:
                    actualizado = True
                    print(f"   ✅ 'rows' actualizado desde 'data'")

            # Caso 2: rows existe pero data no existe o está vacío
            elif rows and not data:
                print(f"   📝 Copiando {len(rows)} elementos de 'rows' a 'data'")
                result = spreadsheets_collection.update_one(
                    {"_id": doc_id}, {"$set": {"data": rows}}
                )
                if result.modified_count > 0:
                    actualizado = True
                    print(f"   ✅ 'data' actualizado desde 'rows'")

            # Caso 3: ambos existen pero tienen diferentes longitudes
            elif len(data) != len(rows):
                # Usar el que tenga más elementos
                if len(data) > len(rows):
                    print(
                        f"   📝 'data' tiene más elementos ({len(data)} vs {len(rows)}), actualizando 'rows'"
                    )
                    result = spreadsheets_collection.update_one(
                        {"_id": doc_id}, {"$set": {"rows": data}}
                    )
                    if result.modified_count > 0:
                        actualizado = True
                        print(f"   ✅ 'rows' actualizado desde 'data'")
                else:
                    print(
                        f"   📝 'rows' tiene más elementos ({len(rows)} vs {len(data)}), actualizando 'data'"
                    )
                    result = spreadsheets_collection.update_one(
                        {"_id": doc_id}, {"$set": {"data": rows}}
                    )
                    if result.modified_count > 0:
                        actualizado = True
                        print(f"   ✅ 'data' actualizado desde 'rows'")
            else:
                print(f"   ✅ 'data' y 'rows' ya están sincronizados")

            if actualizado:
                documentos_actualizados += 1

        print(f"\n" + "=" * 60)
        print(f"📊 RESUMEN:")
        print(f"✅ Documentos procesados: {len(documentos)}")
        print(f"🔧 Documentos actualizados: {documentos_actualizados}")
        print(
            f"✅ Documentos ya sincronizados: {len(documentos) - documentos_actualizados}"
        )

        if documentos_actualizados > 0:
            print(
                f"\n🎉 ¡Sincronización completada! {documentos_actualizados} documentos corregidos"
            )
        else:
            print(f"\n✅ ¡Todas las tablas ya estaban sincronizadas!")

        return True

    except Exception as e:
        print(f"❌ Error conectando a MongoDB: {e}")
        return False
    finally:
        if "client" in locals():
            client.close()


if __name__ == "__main__":
    print("🚀 Iniciando sincronización de campos 'data' y 'rows'...")
    print("=" * 60)

    success = sync_data_rows()

    print("=" * 60)
    if success:
        print("✅ Script ejecutado exitosamente")
        sys.exit(0)
    else:
        print("❌ Script terminó con errores")
        sys.exit(1)
