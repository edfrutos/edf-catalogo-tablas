#!/usr/bin/env python3
# Script: clean_old_database.py
# Descripción: [Explica brevemente qué hace el script]
# Uso: python3 clean_old_database.py [opciones]
# Requiere: [librerías externas, si aplica]
# Variables de entorno: [si aplica]
# Autor: EDF Equipo de Desarrollo - 2025-05-28

import os
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from dotenv import load_dotenv
import certifi

# Cargar variables de entorno
load_dotenv()

MONGO_URI = os.getenv('MONGO_URI')
if not MONGO_URI:
    raise RuntimeError('No se encontró la variable de entorno MONGO_URI')

# Conectar al cluster (no a una base concreta)
client = MongoClient(
    MONGO_URI,
    server_api=ServerApi('1'),
    tlsCAFile=certifi.where()
)

# Nombre de la base de datos antigua a eliminar
OLD_DB = 'app_catalogojoyero'

# Seguridad: pedir confirmación
confirm = input(f"¿Seguro que quieres eliminar la base de datos '{OLD_DB}'? Esta acción es irreversible. (escribe 'SI' para continuar): ")
if confirm.strip().upper() == 'SI':
    client.drop_database(OLD_DB)
    print(f"Base de datos '{OLD_DB}' eliminada correctamente.")
else:
    print("Operación cancelada. No se ha eliminado nada.") 