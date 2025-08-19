#!/usr/bin/env python3
"""
Script para limpiar imagen huérfana de LabelPrint
"""

import sys
import os

sys.path.append("/Users/edefrutos/edefrutos2025.xyz/edf_catalogotablas")

import pymongo
from dotenv import load_dotenv
from bson import ObjectId

# Cargar variables de entorno
load_dotenv()


def get_mongo_db():
    """Conexión directa a MongoDB"""
    mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017/edefrutos2025")
    client = pymongo.MongoClient(mongo_uri)
    return client.get_default_database()


def main():
    try:
        # Conectar a MongoDB
        db = get_mongo_db()
        spreadsheets_collection = db["spreadsheets"]

        # Buscar la tabla específica
        tabla_id = "683833b6ea6f826c192b033c"
        table = spreadsheets_collection.find_one({"_id": ObjectId(tabla_id)})

        if not table:
            print("❌ Tabla no encontrada")
            return

        # Imagen problemática a eliminar
        imagen_problema = "9df6183624e747e5a5a401048bcaa8cf.jpg"

        print(f"🗑️ ELIMINANDO IMAGEN HUÉRFANA: {imagen_problema}")
        print()

        # Obtener datos actuales
        data = table.get("data", [])
        labelprint_row = data[11] if len(data) > 11 else None

        if not labelprint_row:
            print("❌ Fila LabelPrint no encontrada")
            return

        # Mostrar estado ANTES
        imagenes_antes = labelprint_row.get("imagenes", [])
        print(f"📸 ANTES: {len(imagenes_antes)} imágenes → {imagenes_antes}")

        # Eliminar imagen problemática
        if imagen_problema in imagenes_antes:
            imagenes_despues = [img for img in imagenes_antes if img != imagen_problema]

            # Actualizar en MongoDB
            update_result = spreadsheets_collection.update_one(
                {"_id": ObjectId(tabla_id)},
                {"$set": {f"data.11.imagenes": imagenes_despues}},
            )

            if update_result.modified_count > 0:
                print(
                    f"✅ DESPUÉS: {len(imagenes_despues)} imágenes → {imagenes_despues}"
                )
                print()
                print("🎉 ¡IMAGEN HUÉRFANA ELIMINADA EXITOSAMENTE!")
                print()
                print("🔄 RECOMENDACIÓN:")
                print("   1. Recarga la página de edición")
                print("   2. Ya no debería aparecer el error de imagen")
            else:
                print("❌ No se pudo actualizar la base de datos")
        else:
            print("⚠️ Imagen no encontrada en la lista actual")

    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    print("🧹 LIMPIEZA DE IMAGEN HUÉRFANA - LABELPRINT")
    print("=" * 50)
    main()
