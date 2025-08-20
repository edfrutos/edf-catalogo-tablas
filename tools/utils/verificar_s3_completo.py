#!/usr/bin/env python3
"""
Script para verificar completamente la configuración de S3
"""

import os

import requests
from dotenv import load_dotenv


def verificar_s3_completo():
    """Verifica completamente la configuración de S3"""

    print("🔍 VERIFICACIÓN COMPLETA DE S3")
    print("=" * 50)

    load_dotenv()

    # Configuración
    bucket = os.environ.get('S3_BUCKET_NAME', 'edf-catalogo-tablas')
    region = os.environ.get('AWS_REGION', 'eu-central-1')

    print(f"   📦 Bucket: {bucket}")
    print(f"   🌍 Región: {region}")

    # Lista de imágenes para probar
    imagenes_test = [
        "3f75f6c5822d4f40aacc1667c7bf0024_cinematicphotohermosamujer_94172462.png",
        "b2003440d5f14f41abc5699f6362ac16_viaje_de_los_Reyes_Magos_de_Oriente_y_su_sequito.png",
        "7903341a544d40218c77ad020c21b4bc_Miguel_Angel_y_yo_de_ninos.jpg",
        "29927df302c54fb893e7e760cdbadf0f_spain.png",
        "11d8e25e334d4d369b2f5883acdf4a37_20250216_183605329_iOS.jpg",
        "00ce9bfffab84a6ab05e55f692a50f0f_20250216_151630506_iOS.jpg"
    ]

    print(f"\n   🖼️  Probando {len(imagenes_test)} imágenes...")

    resultados = {
        'total': len(imagenes_test),
        'exitosas': 0,
        'fallidas': 0,
        'detalles': []
    }

    for i, imagen in enumerate(imagenes_test, 1):
        url = f"https://{bucket}.s3.{region}.amazonaws.com/{imagen}"

        try:
            response = requests.head(url, timeout=10)

            if response.status_code == 200:
                resultados['exitosas'] += 1
                content_length = response.headers.get('Content-Length', 'N/A')
                content_type = response.headers.get('Content-Type', 'N/A')

                print(f"      ✅ [{i}/{len(imagenes_test)}] {imagen}")
                print(f"         📏 Tamaño: {content_length} bytes")
                print(f"         📄 Tipo: {content_type}")

                resultados['detalles'].append({
                    'imagen': imagen,
                    'status': 'OK',
                    'size': content_length,
                    'type': content_type
                })
            else:
                resultados['fallidas'] += 1
                print(f"      ❌ [{i}/{len(imagenes_test)}] {imagen} - Status: {response.status_code}")

                resultados['detalles'].append({
                    'imagen': imagen,
                    'status': f'ERROR {response.status_code}',
                    'size': 'N/A',
                    'type': 'N/A'
                })

        except Exception as e:
            resultados['fallidas'] += 1
            print(f"      ❌ [{i}/{len(imagenes_test)}] {imagen} - Error: {e}")

            resultados['detalles'].append({
                'imagen': imagen,
                'status': f'EXCEPTION: {str(e)}',
                'size': 'N/A',
                'type': 'N/A'
            })

    # Resumen
    print("\n📊 RESUMEN DE VERIFICACIÓN:")
    print(f"   📦 Bucket: {bucket}")
    print(f"   🌍 Región: {region}")
    print(f"   📄 Total probadas: {resultados['total']}")
    print(f"   ✅ Exitosas: {resultados['exitosas']}")
    print(f"   ❌ Fallidas: {resultados['fallidas']}")

    # Verificar configuración de variables de entorno
    print("\n⚙️  CONFIGURACIÓN DE VARIABLES:")
    aws_access_key = os.environ.get('AWS_ACCESS_KEY_ID')
    aws_secret_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
    use_s3 = os.environ.get('USE_S3')

    print(f"   🔑 AWS Access Key: {'✅ Configurada' if aws_access_key else '❌ No configurada'}")
    print(f"   🔑 AWS Secret Key: {'✅ Configurada' if aws_secret_key else '❌ No configurada'}")
    print(f"   🚀 USE_S3: {use_s3 or 'No configurado'}")

    # Verificar directorio local
    local_path = "/var/www/vhosts/edefrutos2025.xyz/httpdocs/app/static/imagenes_subidas"
    print("\n📁 DIRECTORIO LOCAL:")
    print(f"   📂 Ruta: {local_path}")
    print(f"   📂 Existe: {'✅ Sí' if os.path.exists(local_path) else '❌ No'}")

    if os.path.exists(local_path):
        archivos_locales = os.listdir(local_path)
        print(f"   📄 Archivos locales: {len(archivos_locales)}")

    # Conclusión
    print("\n🎯 CONCLUSIÓN:")
    if resultados['exitosas'] == resultados['total']:
        print("   ✅ S3 está configurado CORRECTAMENTE")
        print("   🚀 Todas las imágenes son accesibles públicamente")
        print("   💡 El sistema de imágenes está listo para producción")
    else:
        print("   ⚠️  S3 tiene problemas de configuración")
        print("   🔧 Revisa la configuración de permisos del bucket")

    return resultados['exitosas'] == resultados['total']

if __name__ == "__main__":
    verificar_s3_completo()
