#!/usr/bin/env python3
# Script: clean_catalogs_collection.py
# Descripción: Borra todos los documentos de la colección 'catalogs'.
# Uso: python3 clean_catalogs_collection.py [--force]
# Autor: [Tu nombre o equipo] - 2025-05-28

import os
import certifi
from pymongo import MongoClient
import argparse

parser = argparse.ArgumentParser(description="Borra todos los documentos de la colección 'catalogs'.")
parser.add_argument('--force', action='store_true', help="Confirma el borrado sin preguntar.")
args = parser.parse_args()

MONGO_URI = os.getenv('MONGO_URI')
client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
db = client.get_database()

print('--- BORRADO SEGURO DE LA COLECCIÓN catalogs ---')

count = db['catalogs'].count_documents({})
print(f"Se van a eliminar {count} documentos de la colección 'catalogs'.")

if args.force:
    confirm = 'SI'
else:
    print("Para confirmar el borrado, ejecuta con --force")
    confirm = 'NO'

if confirm == 'SI':
    result = db['catalogs'].delete_many({})
    print(f"✔ Eliminados {result.deleted_count} documentos de 'catalogs'.")
else:
    print("❌ Operación cancelada. No se ha borrado nada.")
print('--- FIN DEL BORRADO ---') 