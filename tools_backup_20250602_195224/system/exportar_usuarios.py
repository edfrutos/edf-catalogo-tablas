#!/usr/bin/env python3
"""
Script: exportar_usuarios.py
Descripción: Exporta todos los usuarios normales y admin con sus emails y roles a un fichero de texto y a un Excel.
Uso: python3 tools/exportar_usuarios.py
Autor: EDF EDF Equipo de desarrollo - 2024-05-28
"""
import os
import sys
import csv
from openpyxl import Workbook
from pymongo import MongoClient
from dotenv import load_dotenv
from datetime import datetime

# Cargar variables de entorno desde .env
load_dotenv()

# Configuración de conexión (ajusta según tu entorno)
MONGO_URI = os.environ.get('MONGO_URI', 'mongodb+srv://edfrutos:3Utitwr3piFt4LVf@cluster0.abpvipa.mongodb.net/')
DB_NAME = os.environ.get('MONGO_DBNAME', 'app_catalogojoyero_nueva')
COLLECTION = 'users'

# Verificar variables de entorno
if not MONGO_URI or not DB_NAME:
    print("[ERROR] Debes definir MONGO_URI y MONGO_DBNAME en tu archivo .env o en las variables de entorno.")
    sys.exit(1)

ALLOW_INVALID_CERTS = os.environ.get('MONGO_ALLOW_INVALID_CERTS', 'false').lower() in ['true', '1', 'yes']

# Conectar a MongoDB con manejo de errores
try:
    client = MongoClient(
        MONGO_URI,
        serverSelectionTimeoutMS=10000,
        tlsAllowInvalidCertificates=ALLOW_INVALID_CERTS
    )
    db = client[DB_NAME]
    users_col = db[COLLECTION]
    # Probar conexión
    client.server_info()
except Exception as e:
    print(f"[ERROR] No se pudo conectar a MongoDB: {e}")
    if not ALLOW_INVALID_CERTS:
        print("Si el error es de certificados, puedes probar a ejecutar el script con la variable de entorno MONGO_ALLOW_INVALID_CERTS=true (solo para pruebas)")
    sys.exit(2)

if ALLOW_INVALID_CERTS:
    print("""
[AVISO DE INSEGURIDAD]
--------------------------------------------------
La verificación de certificados SSL está DESACTIVADA.
Esto es INSEGURO y solo debe usarse para pruebas puntuales.
No uses esta opción en producción.
--------------------------------------------------
""")

# Buscar usuarios normales y admin
usuarios = list(users_col.find({"role": {"$in": ["user", "admin"]}}))

# Carpeta de salida
EXPORT_DIR = 'exportados'
os.makedirs(EXPORT_DIR, exist_ok=True)
fecha_str = datetime.now().strftime('%Y%m%d_%H%M%S')

# Exportar a texto plano
txt_path = os.path.join(EXPORT_DIR, f'usuarios_exportados_{fecha_str}.txt')
with open(txt_path, 'w', encoding='utf-8') as f:
    f.write('Nombre\tEmail\tRol\n')
    for u in usuarios:
        nombre = u.get('nombre') or u.get('username') or u.get('name') or ''
        email = u.get('email', '')
        rol = u.get('role', '')
        f.write(f'{nombre}\t{email}\t{rol}\n')
print(f"Exportado a {txt_path}")

# Exportar a Excel
excel_path = os.path.join(EXPORT_DIR, f'usuarios_exportados_{fecha_str}.xlsx')
wb = Workbook()
ws = wb.active
ws.title = 'Usuarios'
ws.append(['Nombre', 'Email', 'Rol'])
for u in usuarios:
    nombre = u.get('nombre') or u.get('username') or u.get('name') or ''
    email = u.get('email', '')
    rol = u.get('role', '')
    ws.append([nombre, email, rol])
wb.save(excel_path)
print(f"Exportado a {excel_path}") 