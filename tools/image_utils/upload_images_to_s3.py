#!/usr/bin/env python3
"""
Script para subir las imágenes corregidas a S3
"""

from utils.s3_utils import upload_file_to_s3
import os
import sys

from dotenv import load_dotenv

# Agregar el directorio app al path para importar las utilidades
sys.path.append(os.path.join(os.path.dirname(__file__), "app"))


# Cargar variables de entorno
load_dotenv()


def upload_corrected_images():
    """Sube las imágenes corregidas a S3"""

    # Archivos a subir (los hashes correctos)
    images_to_upload = [
        "04fde09d2bfb465688c14902e145ea5b_498620815.seagate-barracuda-3-5-2tb-7200rpm-256mb-sata3-st2000dm008.jpg",
        "5abe0ac45cf94a6490482372c9e9ba38_108465-2-pendrive_usb30_256gb_corsair_flash_voyager_slider_cmfsl3b_256gb-5.jpg",
    ]

    print("🚀 Subiendo imágenes corregidas a S3...")
    print("=" * 60)

    # Directorio base de uploads
    uploads_dir = (
        "/Users/edefrutos/edefrutos2025.xyz/edf_catalogotablas/app/static/uploads"
    )

    success_count = 0
    total_count = len(images_to_upload)

    for image_name in images_to_upload:
        local_path = os.path.join(uploads_dir, image_name)

        print(f"📤 Subiendo: {image_name}")

        # Verificar que el archivo existe localmente
        if not os.path.exists(local_path):
            print(f"   ❌ Archivo no encontrado localmente: {local_path}")
            continue

        # Obtener tamaño del archivo
        file_size = os.path.getsize(local_path)
        print(f"   📏 Tamaño: {file_size:,} bytes")

        # Subir a S3
        result = upload_file_to_s3(local_path, image_name)

        if result["success"]:
            print("   ✅ Subido exitosamente")
            print(f"   🔗 URL: {result['url']}")
            success_count += 1
        else:
            print(f"   ❌ Error: {result['error']}")

        print()

    # Resumen
    print("=" * 60)
    print("📊 RESUMEN DE SUBIDA:")
    print(f"✅ Exitosas: {success_count}")
    print(f"❌ Fallidas: {total_count - success_count}")
    print(f"📊 Total: {total_count}")

    if success_count == total_count:
        print("\n🎉 ¡Todas las imágenes se subieron correctamente a S3!")
        return True
    else:
        print(f"\n⚠️  {total_count - success_count} imágenes no se pudieron subir")
        return False


if __name__ == "__main__":
    print("🚀 Iniciando subida de imágenes a S3...")
    print()

    try:
        success = upload_corrected_images()
        if success:
            print("✅ Subida completada exitosamente")
            sys.exit(0)
        else:
            print("❌ Subida completada con errores")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Error inesperado: {str(e)}")
        sys.exit(1)
