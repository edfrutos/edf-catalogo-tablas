#!/usr/bin/env python3
"""
Script para verificar imágenes de LabelPrint en MongoDB
"""

import os
import sys

sys.path.append("/Users/edefrutos/edefrutos2025.xyz/edf_catalogotablas")

import pymongo
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()


def get_mongo_db():
    """Conexión directa a MongoDB"""
    mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017/edefrutos2025")
    client = pymongo.MongoClient(mongo_uri)
    return client.get_default_database()


from bson import ObjectId  # noqa: E402


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

        # Buscar fila de LabelPrint (índice 11)
        data = table.get("data", [])
        if len(data) <= 11:
            print(f"❌ No hay suficientes filas. Total: {len(data)}")
            return

        labelprint_row = data[11]
        print(f"🏷️ FILA LABELPRINT (índice 11):")  # noqa: F541
        print(f"   Nombre: {labelprint_row.get('Nombre', 'N/A')}")
        print()

        # Verificar todos los campos de imagen
        campos_imagen = ["images", "imagenes", "imagen_data", "Imagen"]

        print("📸 CAMPOS DE IMAGEN:")
        for campo in campos_imagen:
            valor = labelprint_row.get(campo)
            if valor is not None:
                print(f"   {campo}: {valor} (tipo: {type(valor).__name__})")
            else:
                print(f"   {campo}: None")

        print()

        # Identificar imagen problemática
        imagen_problema = "9df6183624e747e5a5a401048bcaa8cf.jpg"
        print(f"🔍 BUSCANDO IMAGEN PROBLEMÁTICA: {imagen_problema}")

        found = False
        for campo in campos_imagen:
            valor = labelprint_row.get(campo)
            if valor and isinstance(valor, list) and imagen_problema in valor:
                print(f"   ❌ ENCONTRADA EN: {campo}")
                found = True
            elif valor and isinstance(valor, str) and imagen_problema in valor:
                print(f"   ❌ ENCONTRADA EN: {campo} (string)")
                found = True

        if not found:
            print("   ✅ Imagen problemática NO encontrada en MongoDB")

        print()
        print("🎯 RECOMENDACIÓN:")
        if found:
            print("   La imagen está en MongoDB pero no existe físicamente")
            print("   Necesitas eliminarla de la base de datos")
        else:
            print("   La imagen puede estar en caché del navegador")
            print("   Recarga sin caché (Ctrl+Shift+R)")

    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()
