#!/usr/bin/env python3
"""
Script para diagnosticar el problema de imágenes en el catálogo específico
"""

import os
import sys

from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def diagnosticar_imagenes_catalogo():
    """Diagnostica el problema de imágenes en el catálogo"""

    print("🔍 DIAGNÓSTICO DE IMÁGENES EN CATÁLOGO")
    print("=" * 50)

    load_dotenv()

    try:
        from bson import ObjectId
        from main_app import create_app

        from app.models import get_mongo_db
        from app.utils.image_manager import get_image_url

        app = create_app()

        with app.app_context():
            # ID del catálogo problemático
            catalog_id = "6898e9b1242211a1f3f4173c"

            print(f"   📋 Catálogo ID: {catalog_id}")

            # Obtener datos del catálogo
            db = get_mongo_db()
            catalog = db["spreadsheets"].find_one({"_id": ObjectId(catalog_id)})

            if not catalog:
                print("   ❌ Catálogo no encontrado")
                return False

            print(f"   ✅ Catálogo encontrado: {catalog.get('name', 'Sin nombre')}")
            print(f"   📅 Fecha: {catalog.get('created_at', 'Sin fecha')}")
            print(f"   📊 Filas: {len(catalog.get('rows', []))}")

            # Analizar imágenes en cada fila
            rows = catalog.get("rows", [])

            for i, row in enumerate(rows):
                print(f"\n   📄 Fila {i+1}:")

                # Obtener imágenes de la fila
                images = row.get("images", [])
                if isinstance(images, str):
                    # Si es string, intentar parsear como JSON
                    import json

                    try:
                        images = json.loads(images)
                    except BaseException:
                        images = [images]

                print(f"      🖼️  Imágenes encontradas: {len(images)}")

                for j, img in enumerate(images[:3]):  # Solo las primeras 3
                    print(f"         [{j+1}] {img}")

                    # Verificar si existe en S3
                    s3_url = f"https://edf-catalogo-tablas.s3.eu-central-1.amazonaws.com/{img}"
                    print(f"            🔗 S3 URL: {s3_url}")

                    # Verificar si existe localmente
                    local_path = f"/var/www/vhosts/edefrutos2025.xyz/httpdocs/app/static/imagenes_subidas/{img}"
                    local_exists = os.path.exists(local_path)
                    print(
                        f"            📁 Local: {'✅ Existe' if local_exists else '❌ No existe'}"
                    )

                    # Probar URL del gestor de imágenes
                    try:
                        image_url = get_image_url(img, use_s3=True)
                        print(f"            🎯 Gestor URL: {image_url}")
                    except Exception as e:
                        print(f"            ❌ Error gestor: {e}")

                if len(images) > 3:
                    print(f"         ... y {len(images) - 3} más")

            # Verificar configuración del gestor de imágenes
            print("\n   ⚙️  CONFIGURACIÓN DEL GESTOR:")
            try:
                from app.utils.image_manager import image_manager

                print(f"      📦 Bucket S3: {image_manager.s3_bucket}")
                print(f"      🌍 Región: {image_manager.aws_region}")
                print(f"      📁 Ruta local: {image_manager.local_path}")
                print(
                    f"      🔧 Cliente S3: {'✅ Disponible' if image_manager.s3_client else '❌ No disponible'}"
                )
            except Exception as e:
                print(f"      ❌ Error configurando gestor: {e}")

            return True

    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    diagnosticar_imagenes_catalogo()
