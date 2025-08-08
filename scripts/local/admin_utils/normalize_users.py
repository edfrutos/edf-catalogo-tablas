#!/usr/bin/env python3
"""
Script: normalize_users.py
Descripción: Herramienta de administración para normalizar y limpiar datos de usuarios
             en la base de datos MongoDB. Aplica formatos consistentes a emails,
             usernames y otros campos para mantener la integridad de los datos.

Funcionalidades:
  ✅ Backup automático antes de cualquier cambio
  ✅ Modo DRY RUN para revisar cambios sin aplicarlos
  ✅ Normalización de emails (minúsculas, espacios)
  ✅ Normalización de usernames (minúsculas, espacios)
  ✅ Confirmación interactiva antes de aplicar cambios
  ✅ Reporte detallado de modificaciones realizadas

Uso:
  python3 normalize_users.py

Requisitos:
  - pymongo
  - python-dotenv
  - MongoDB Atlas o servidor local

Variables de entorno:
  - MONGO_URI: URI de conexión a MongoDB

Autor: EDF Developer - 2025-06-09
Versión: 1.0
"""

import sys
import os
import pprint
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Agregar el directorio raíz del proyecto al path de Python
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from app.maintenance import normalize_users_in_db, backup_users_to_json
from app.models import get_users_collection

if __name__ == "__main__":
    print("🔧 NORMALIZACIÓN DE USUARIOS EN MONGODB")
    print("=" * 50)

    # Verificar conexión a la base de datos
    print("📡 Conectando a la base de datos...")
    collection = get_users_collection()
    if collection is None:
        print("❌ ERROR: No se pudo obtener la colección de usuarios.")
        print("   Verifique la variable de entorno MONGO_URI")
        sys.exit(1)
    print("✅ Conexión establecida correctamente")

    # Realizar backup
    print("\n💾 Creando backup de seguridad...")
    backup_file, total = backup_users_to_json(collection)
    print(f"✅ Backup realizado: {backup_file}")
    print(f"📊 Total de usuarios en backup: {total}")

    # Análisis en modo DRY RUN
    print("\n🔍 ANALIZANDO CAMBIOS (Modo DRY RUN)")
    print("-" * 40)
    summary = normalize_users_in_db(apply_changes=False)
    print(f"📈 Usuarios totales en BD: {summary['total_users']}")
    print(f"🔄 Usuarios a modificar: {summary['users_changed']}")

    if int(summary["users_changed"]) > 0:
        print("\n📋 Ejemplos de cambios que se aplicarían:")
        print("   (Campo: valor_actual → valor_nuevo)")
        try:
            for change in summary["changes"][:3]:  # Mostrar solo los primeros 3
                if isinstance(change, dict):
                    user_id = change.get("_id", "unknown")
                    changes_dict = change.get("changes", {})
                    if isinstance(changes_dict, dict):
                        for field, value_tuple in changes_dict.items():
                            if isinstance(value_tuple, tuple) and len(value_tuple) == 2:
                                old_val, new_val = value_tuple
                                print(
                                    f"   • Usuario {user_id[:8]}...: {field} = '{old_val}' → '{new_val}'"
                                )
        except Exception as e:
            print(f"   ⚠️  Error al mostrar cambios: {e}")
            print("   Los cambios se aplicarán correctamente.")

        if len(summary["changes"]) > 3:
            print(f"   ... y {len(summary['changes']) - 3} cambios más")
    else:
        print("✅ No se encontraron usuarios que requieran normalización.")
        print("   Los datos ya están en formato correcto.")
        sys.exit(0)

    # Confirmación del usuario
    print("\n" + "=" * 50)
    confirm = (
        input("❓ ¿Desea aplicar estos cambios en la base de datos? (s/N): ")
        .strip()
        .lower()
    )
    if confirm != "s":
        print("❌ Operación cancelada por el usuario.")
        print("   Los cambios NO se han aplicado.")
        sys.exit(0)

    # Aplicar cambios
    print("\n🚀 APLICANDO CAMBIOS...")
    print("-" * 30)
    summary = normalize_users_in_db(apply_changes=True)
    print(f"✅ Usuarios modificados exitosamente: {summary['users_changed']}")
    print("🎉 Proceso de normalización completado.")
    print("\n💡 Recomendación: Ejecute este script periódicamente para mantener")
    print("   la consistencia de los datos de usuarios.")
