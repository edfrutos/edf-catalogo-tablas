#!/usr/bin/env python3
"""
Script para diagnosticar el caos de imágenes
"""

import os
import sys

# Añadir el directorio raíz al path
sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from bson.objectid import ObjectId

from app.models.database import get_mongo_db


def diagnose_image_chaos():
    """Diagnosticar problemas de imágenes en filas específicas"""
    print("🔍 DIAGNÓSTICO COMPLETO DE IMÁGENES")
    print("=" * 50)

    db = get_mongo_db()
    collection = db["spreadsheets"]

    # ID de la tabla Componentes ordenador
    table_id = "683833b6ea6f826c192b033c"

    table = collection.find_one({"_id": ObjectId(table_id)})
    if not table:
        print("❌ Tabla no encontrada")
        return

    data = table.get("data", [])

    print(f"📋 Tabla: {table.get('name', 'Sin nombre')}")
    print(f"📊 Total filas: {len(data)}")
    print()

    # Verificar las filas problemáticas
    filas_problema = [0, 3, 11, 12]  # Escáner, Cámara Web, LabelPrint, Conversor USB

    for fila_num in filas_problema:
        if len(data) > fila_num:
            fila = data[fila_num]
            nombre = fila.get("Nombre", "Sin nombre")

            print(f"🎯 FILA {fila_num + 1}: {nombre}")
            print(f"   Índice interno: {fila_num}")
            print()

            # Verificar todos los campos de imagen posibles
            campos_imagen = ["images", "imagenes", "imagen_data", "Imagen"]

            for campo in campos_imagen:
                valor = fila.get(campo)
                tipo = type(valor).__name__

                if valor:
                    if isinstance(valor, list):
                        print(f"   📸 {campo}: {len(valor)} elementos")
                        for i, img in enumerate(valor):
                            print(f"      [{i}] {img}")
                    else:
                        print(f"   📸 {campo}: '{valor}' (tipo: {tipo})")
                else:
                    print(f"   📸 {campo}: VACÍO (tipo: {tipo})")

            # Verificar si existen archivos localmente
            print(f"   🔍 VERIFICACIÓN LOCAL:")  # noqa: F541
            todas_imagenes = []

            # Recopilar todas las imágenes
            for campo in ["images", "imagenes", "imagen_data"]:
                valor = fila.get(campo)
                if isinstance(valor, list):
                    todas_imagenes.extend(valor)
                elif isinstance(valor, str) and valor and valor != "N/A":
                    todas_imagenes.append(valor)

            # Eliminar duplicados
            todas_imagenes = list(set(todas_imagenes))

            if todas_imagenes:
                for img in todas_imagenes:
                    if img.startswith("http"):
                        print(f"      ✅ URL externa: {img}")
                    else:
                        # Verificar local
                        local_path = f"/Users/edefrutos/edefrutos2025.xyz/edf_catalogotablas/app/static/uploads/{img}"
                        existe_local = os.path.exists(local_path)

                        if existe_local:
                            size = os.path.getsize(local_path)
                            print(f"      ✅ LOCAL: {img} ({size:,} bytes)")
                        else:
                            print(f"      ❌ FALTA LOCAL: {img}")
            else:
                print("      ⚠️ Sin imágenes encontradas")

            print("-" * 40)
            print()

    print()
    print("🔧 RECOMENDACIONES:")
    print("1. Unificar la lógica de búsqueda de imágenes")
    print("2. Estandarizar el campo de almacenamiento (usar 'images')")
    print("3. Implementar fallback S3 → Local → Error imagen")
    print("4. Verificar URLs en templates")


if __name__ == "__main__":
    diagnose_image_chaos()
