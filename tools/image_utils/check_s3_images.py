#!/usr/bin/env python3
"""
Script para verificar si las imágenes corregidas existen en S3
"""

from utils.s3_utils import get_s3_client, get_s3_url
import os
import sys

from dotenv import load_dotenv

# Agregar el directorio app al path para importar las utilidades
sys.path.append(os.path.join(os.path.dirname(__file__), "app"))


# Cargar variables de entorno
load_dotenv()


def check_images_in_s3():
    """Verifica si las imágenes corregidas existen en S3"""

    # Archivos a verificar (los hashes correctos)
    images_to_check = [
        "04fde09d2bfb465688c14902e145ea5b_498620815.seagate-barracuda-3-5-2tb-7200rpm-256mb-sata3-st2000dm008.jpg",
        "5abe0ac45cf94a6490482372c9e9ba38_108465-2-pendrive_usb30_256gb_corsair_flash_voyager_slider_cmfsl3b_256gb-5.jpg",
    ]

    print("🔍 Verificando imágenes en S3...")
    print("=" * 60)

    # Verificar configuración de S3
    bucket_name = os.environ.get("S3_BUCKET_NAME")
    aws_access_key = os.environ.get("AWS_ACCESS_KEY_ID")
    aws_secret_key = os.environ.get("AWS_SECRET_ACCESS_KEY")

    if not bucket_name:
        print("❌ S3_BUCKET_NAME no configurado")
        return False

    if not aws_access_key or not aws_secret_key:
        print("❌ Credenciales de AWS no configuradas")
        return False

    print(f"📦 Bucket configurado: {bucket_name}")
    print(f"🔑 AWS Access Key configurado: {aws_access_key[:10]}***")

    # Verificar cliente S3
    s3_client = get_s3_client()
    if not s3_client:
        print("❌ No se pudo crear el cliente S3")
        return False

    print("✅ Cliente S3 creado correctamente")
    print()

    # Verificar cada imagen
    results = {}
    for image_name in images_to_check:
        print(f"🔍 Verificando: {image_name}")

        # Verificar en S3
        s3_url = get_s3_url(image_name)

        if s3_url:
            print(f"   ✅ Encontrado en S3: {s3_url}")
            results[image_name] = {"s3_exists": True, "s3_url": s3_url}
        else:
            print("   ❌ NO encontrado en S3")
            results[image_name] = {"s3_exists": False, "s3_url": None}

        # Verificar en local
        local_path = f"/Users/edefrutos/edefrutos2025.xyz/edf_catalogotablas/app/static/uploads/{image_name}"
        if os.path.exists(local_path):
            file_size = os.path.getsize(local_path)
            print(f"   📁 Existe en local: {file_size:,} bytes")
            results[image_name]["local_exists"] = True
            results[image_name]["local_size"] = file_size
        else:
            print("   📁 NO existe en local")
            results[image_name]["local_exists"] = False

        print()

    # Resumen
    print("=" * 60)
    print("📊 RESUMEN DE VERIFICACIÓN:")
    print()

    for image_name, result in results.items():
        print(f"🖼️  {image_name}")
        print(f"   S3: {'✅ SÍ' if result['s3_exists'] else '❌ NO'}")
        print(f"   Local: {'✅ SÍ' if result['local_exists'] else '❌ NO'}")

        if result["local_exists"] and not result["s3_exists"]:
            print("   ⚠️  Recomendación: Subir a S3")
        elif result["s3_exists"] and not result["local_exists"]:
            print("   ⚠️  Recomendación: Descargar de S3")
        elif result["s3_exists"] and result["local_exists"]:
            print("   ✅ Sincronizado")
        else:
            print("   ❌ No encontrado en ningún lado")
        print()

    return True


if __name__ == "__main__":
    print("🚀 Iniciando verificación de imágenes en S3...")
    print()

    try:
        success = check_images_in_s3()
        if success:
            print("✅ Verificación completada")
        else:
            print("❌ Error en la verificación")
    except Exception as e:
        print(f"❌ Error inesperado: {str(e)}")
        sys.exit(1)
