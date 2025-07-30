# Script: normalize_users.py
# Descripción: [Explica brevemente qué hace el script]
# Uso: python3 normalize_users.py [opciones]
# Requiere: [librerías externas, si aplica]
# Variables de entorno: [si aplica]
# Autor: EDF Developer - 2025-06-09

import sys
import pprint
from app.maintenance import normalize_users_in_db, backup_users_to_json
from app.models import get_users_collection

if __name__ == "__main__":
    print("== Normalización de usuarios en MongoDB ==")
    collection = get_users_collection()
    if collection is None:
        print("ERROR: No se pudo obtener la colección de usuarios.")
        sys.exit(1)

    backup_file, total = backup_users_to_json(collection)
    print(f"Backup realizado: {backup_file} ({total} usuarios)")

    print("\n[DRY RUN] Analizando cambios que se aplicarían...")
    summary = normalize_users_in_db(apply_changes=False)
    print(f"Usuarios totales: {summary['total_users']}")
    print(f"Usuarios a modificar: {summary['users_changed']}")
    if summary['users_changed'] > 0:
        print("Ejemplos de cambios:")
        pprint.pprint(summary['changes'])
    else:
        print("No se encontraron usuarios a modificar.")
        sys.exit(0)

    confirm = input("\n¿Desea aplicar los cambios en la base de datos? (s/N): ").strip().lower()
    if confirm != "s":
        print("Operación cancelada.")
        sys.exit(0)

    print("\nAplicando cambios...")
    summary = normalize_users_in_db(apply_changes=True)
    print(f"Usuarios modificados: {summary['users_changed']}")
    print("Proceso finalizado.")
