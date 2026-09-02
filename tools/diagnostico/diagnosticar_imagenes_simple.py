#!/usr/bin/env python3
"""
Script simple para diagnosticar imágenes del catálogo
"""

import json
import os

from dotenv import load_dotenv
from pymongo import MongoClient


def diagnosticar_imagenes_simple():
    """Diagnostica imágenes del catálogo de forma simple"""

    print("🔍 DIAGNÓSTICO SIMPLE DE IMÁGENES")
    print("=" * 50)

    load_dotenv()

    # Configuración MongoDB
    mongo_uri = os.environ.get("MONGO_URI")
    if not mongo_uri:
        print("❌ Define MONGO_URI en el archivo .env")
        return False

    try:
        # Conectar a MongoDB
        client = MongoClient(mongo_uri)
        db = client.get_default_database()

        # ID del catálogo problemático
        catalog_id = "6898e9b1242211a1f3f4173c"

        print(f"   📋 Catálogo ID: {catalog_id}")

        # Obtener catálogo
        from bson import ObjectId

        catalog = db["catalogs"].find_one({"_id": ObjectId(catalog_id)})

        if not catalog:
            print("   ❌ Catálogo no encontrado")
            return False

        print(f"   ✅ Catálogo encontrado: {catalog.get('name', 'Sin nombre')}")
        print(f"   📅 Fecha: {catalog.get('created_at', 'Sin fecha')}")

        # Analizar filas
        rows = catalog.get("rows", [])
        print(f"   📊 Total filas: {len(rows)}")

        # Verificar directorio local
        local_path = (
            "/var/www/vhosts/edefrutos2025.xyz/httpdocs/app/static/imagenes_subidas"
        )
        print(f"\n   📁 Directorio local: {local_path}")
        print(f"   📂 Existe: {'✅ Sí' if os.path.exists(local_path) else '❌ No'}")

        if os.path.exists(local_path):
            local_files = os.listdir(local_path)
            print(f"   📄 Archivos locales: {len(local_files)}")

        # Analizar imágenes en cada fila
        for i, row in enumerate(rows[:3]):  # Solo primeras 3 filas
            print(f"\n   📄 Fila {i+1}:")

            # Obtener imágenes
            images = row.get("images", [])
            if isinstance(images, str):
                try:
                    images = json.loads(images)
                except BaseException:
                    images = [images]

            print(f"      🖼️  Imágenes: {len(images)}")

            # Verificar primeras 3 imágenes
            for j, img in enumerate(images[:3]):
                print(f"         [{j+1}] {img}")

                # Verificar local
                local_file = os.path.join(local_path, img)
                local_exists = os.path.exists(local_file)
                print(
                    f"            📁 Local: {'✅ Existe' if local_exists else '❌ No existe'}"
                )

                # Verificar S3 (simular)
                s3_url = (
                    f"https://edf-catalogo-tablas.s3.eu-central-1.amazonaws.com/{img}"
                )
                print(f"            🔗 S3 URL: {s3_url}")

                # Probar acceso S3
                import requests

                try:
                    response = requests.head(s3_url, timeout=5)
                    print(f"            🌐 S3 Status: {response.status_code}")
                except Exception as e:
                    print(f"            ❌ S3 Error: {e}")

        # Verificar configuración S3
        print("\n   ⚙️  CONFIGURACIÓN S3:")
        aws_access_key = os.environ.get("AWS_ACCESS_KEY_ID")
        aws_secret_key = os.environ.get("AWS_SECRET_ACCESS_KEY")
        s3_bucket = os.environ.get("S3_BUCKET_NAME")

        print(
            f"      🔑 Access Key: {'✅ Configurada' if aws_access_key else '❌ No configurada'}"
        )
        print(
            f"      🔑 Secret Key: {'✅ Configurada' if aws_secret_key else '❌ No configurada'}"
        )
        print(f"      📦 Bucket: {s3_bucket or '❌ No configurado'}")

        return True

    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    diagnosticar_imagenes_simple()
