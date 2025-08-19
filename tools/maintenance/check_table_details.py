#!/usr/bin/env python3
"""
Script para verificar detalles específicos de la tabla Componentes ordenador
"""

import os
import sys

# Añadir el directorio raíz al path
sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from app.models.database import get_mongo_db
from bson.objectid import ObjectId


def check_table_details():
    """Verificar detalles de la tabla Componentes ordenador"""
    print("🔍 Verificando detalles de la tabla Componentes ordenador...")

    db = get_mongo_db()
    collection = db["spreadsheets"]

    # ID de la tabla Componentes ordenador
    table_id = "683833b6ea6f826c192b033c"

    table = collection.find_one({"_id": ObjectId(table_id)})
    if not table:
        print("❌ Tabla no encontrada")
        return

    print(f"📋 Tabla: {table.get('name', 'Sin nombre')}")
    print(f"🔢 num_rows: {table.get('num_rows', 'N/A')}")

    # Verificar data y rows
    data = table.get("data", [])
    rows = table.get("rows", [])

    print(f"📊 len(data): {len(data)}")
    print(f"📊 len(rows): {len(rows)}")

    print("\n🔍 Filas en 'data':")
    for i, row in enumerate(data):
        nombre = row.get("Nombre", "Sin nombre")
        print(f"  {i}: {nombre}")

    print("\n🔍 Filas en 'rows':")
    for i, row in enumerate(rows):
        nombre = row.get("Nombre", "Sin nombre")
        print(f"  {i}: {nombre}")

    # Verificar si hay diferencias
    if len(data) != len(rows):
        print(
            f"\n❌ INCONSISTENCIA: data tiene {len(data)} filas, rows tiene {len(rows)} filas"
        )
    else:
        print(f"\n✅ data y rows tienen el mismo número de filas: {len(data)}")


if __name__ == "__main__":
    check_table_details()
