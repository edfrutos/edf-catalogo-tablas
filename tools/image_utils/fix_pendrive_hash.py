#!/usr/bin/env python3
"""
Script para corregir el hash de imagen del pendrive en la base de datos
"""

import os
import sys

from bson import ObjectId
from dotenv import load_dotenv
from pymongo import MongoClient

# Cargar variables de entorno
load_dotenv()


def fix_pendrive_hash():
    """Corrige el hash de imagen del pendrive en la base de datos"""

    # Conectar a MongoDB
    mongo_uri = os.getenv("MONGO_URI")
    if not mongo_uri:
        print("❌ Error: MONGO_URI no encontrado en las variables de entorno")
        return False

    try:
        client = MongoClient(mongo_uri)
        db = client.get_database()

        # Hash incorrecto que está en la base de datos
        hash_incorrecto = "db318c3111d84430badcfb59623825a3_108465-2-pendrive_usb30_256gb_corsair_flash_voyager_slider_cmfsl3b_256gb-5.jpg"

        # Hash correcto que existe en el filesystem (usamos el primero encontrado)
        hash_correcto = "5abe0ac45cf94a6490482372c9e9ba38_108465-2-pendrive_usb30_256gb_corsair_flash_voyager_slider_cmfsl3b_256gb-5.jpg"

        print(
            f"🔍 Buscando registros con hash incorrecto del pendrive: {hash_incorrecto}"
        )
        print(f"📋 Hash correcto a usar: {hash_correcto}")

        # Buscar en la colección spreadsheets
        spreadsheets_collection = db["spreadsheets"]

        # Buscar documentos que contengan el hash incorrecto
        query = {
            "$or": [{"rows.images": hash_incorrecto}, {"data.images": hash_incorrecto}]
        }

        documentos_encontrados = list(spreadsheets_collection.find(query))
        print(f"📊 Documentos encontrados: {len(documentos_encontrados)}")

        if not documentos_encontrados:
            print("✅ No se encontraron documentos con el hash incorrecto del pendrive")
            return True

        # Procesar cada documento encontrado
        for doc in documentos_encontrados:
            doc_id = doc["_id"]
            print(f"\n🔧 Procesando documento: {doc_id}")
            print(f"   Nombre: {doc.get('name', 'Sin nombre')}")
            print(f"   Owner: {doc.get('owner', 'Sin owner')}")

            actualizado = False

            # Actualizar en rows.images
            if "rows" in doc:
                for i, row in enumerate(doc["rows"]):
                    if "images" in row and hash_incorrecto in row["images"]:
                        print(
                            f"   📝 Actualizando row {i} - Item: {row.get('Nombre', 'Sin nombre')}"
                        )
                        # Reemplazar el hash incorrecto con el correcto
                        new_images = [
                            hash_correcto if img == hash_incorrecto else img
                            for img in row["images"]
                        ]

                        result = spreadsheets_collection.update_one(
                            {"_id": doc_id}, {"$set": {f"rows.{i}.images": new_images}}
                        )

                        if result.modified_count > 0:
                            print(f"   ✅ Row {i} actualizado correctamente")
                            actualizado = True
                        else:
                            print(f"   ❌ Error actualizando row {i}")

            # Actualizar en data.images
            if "data" in doc:
                for i, item in enumerate(doc["data"]):
                    if "images" in item and hash_incorrecto in item["images"]:
                        print(
                            f"   📝 Actualizando data item {i} - Item: {item.get('Nombre', 'Sin nombre')}"
                        )
                        # Reemplazar el hash incorrecto con el correcto
                        new_images = [
                            hash_correcto if img == hash_incorrecto else img
                            for img in item["images"]
                        ]

                        result = spreadsheets_collection.update_one(
                            {"_id": doc_id}, {"$set": {f"data.{i}.images": new_images}}
                        )

                        if result.modified_count > 0:
                            print(f"   ✅ Data item {i} actualizado correctamente")
                            actualizado = True
                        else:
                            print(f"   ❌ Error actualizando data item {i}")

            if actualizado:
                print(f"   🎉 Documento {doc_id} actualizado exitosamente")
            else:
                print(f"   ⚠️  No se realizaron cambios en documento {doc_id}")

        # Verificar que la corrección funcionó
        print("\n🔍 Verificando corrección...")
        documentos_verificacion = list(spreadsheets_collection.find(query))

        if len(documentos_verificacion) == 0:
            print(
                "✅ ¡Corrección exitosa! No quedan registros con el hash incorrecto del pendrive"
            )
            return True
        else:
            print(
                f"❌ Aún quedan {len(documentos_verificacion)} registros con el hash incorrecto"
            )
            return False

    except Exception as e:
        print(f"❌ Error conectando a MongoDB: {e}")
        return False
    finally:
        if "client" in locals():
            client.close()


if __name__ == "__main__":
    print("🚀 Iniciando corrección de hash de imagen del pendrive...")
    print("=" * 60)

    success = fix_pendrive_hash()

    print("=" * 60)
    if success:
        print("✅ Script ejecutado exitosamente")
        sys.exit(0)
    else:
        print("❌ Script terminó con errores")
        sys.exit(1)
