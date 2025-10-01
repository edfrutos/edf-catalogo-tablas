#!/usr/bin/env python3
"""
Script para corregir el campo num_rows en todas las tablas.
El problema es que num_rows está desactualizado (ej. dice 3 pero hay 16 filas).
"""

from app.models.database import get_mongo_db
from bson.objectid import ObjectId
import os
import sys
from datetime import datetime

# Añadir el directorio raíz al path
sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)


def fix_num_rows():
    """Corregir el campo num_rows en todas las tablas"""
    print("🔧 Iniciando corrección del campo num_rows...")

    db = get_mongo_db()
    collection = db["spreadsheets"]

    # Obtener todas las tablas
    tables = list(collection.find({}))
    print(f"📊 Encontradas {len(tables)} tablas")

    updated_count = 0

    for table in tables:
        table_id = table["_id"]
        name = table.get("name", "Sin nombre")

        # Sincronizar data y rows
        if "rows" in table and table["rows"] is not None:
            table["data"] = table["rows"]
        elif "data" in table and table["data"] is not None:
            table["rows"] = table["data"]
        else:
            table["data"] = []
            table["rows"] = []

        # Calcular el número real de filas
        real_rows = len(table["data"])
        current_num_rows = table.get("num_rows", 0)

        print(f"📋 Tabla '{name}' (ID: {table_id})")
        print(f"   - num_rows actual: {current_num_rows}")
        print(f"   - Filas reales: {real_rows}")

        if current_num_rows != real_rows:
            print(f"   ❌ Inconsistencia detectada: {current_num_rows} != {real_rows}")

            # Actualizar la tabla
            result = collection.update_one(
                {"_id": table_id},
                {
                    "$set": {
                        "data": table["data"],
                        "rows": table["rows"],
                        "num_rows": real_rows,
                        "updated_at": datetime.utcnow(),
                    }
                },
            )

            if result.modified_count > 0:
                print(f"   ✅ Corregido: num_rows = {real_rows}")
                updated_count += 1
            else:
                print("   ❌ Error al actualizar")
        else:
            print("   ✅ Ya está correcto")

        print()

    print(f"🎉 Proceso completado. {updated_count} tablas actualizadas.")


if __name__ == "__main__":
    fix_num_rows()
