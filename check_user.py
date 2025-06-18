# Script: check_user.py
# Descripción: [Explica brevemente qué hace el script]
# Uso: python3 check_user.py [opciones]
# Requiere: [librerías externas, si aplica]
# Variables de entorno: [si aplica]
# Autor: [Tu nombre o equipo] - 2025-06-09

import os
from dotenv import load_dotenv
from pymongo import MongoClient
from bson import ObjectId

# Cargar variables de entorno
load_dotenv()

def check_user(email):
    # Obtener la URI de conexión de MongoDB
    mongo_uri = os.getenv('MONGO_URI')
    if not mongo_uri:
        print("Error: MONGO_URI no está configurada en el archivo .env")
        return
    
    try:
        # Conectar a MongoDB
        client = MongoClient(mongo_uri, tlsAllowInvalidCertificates=True)
        db_name = os.getenv('MONGODB_DB', 'app_catalogojoyero_nueva')
        db = client[db_name]
        
        # Buscar el usuario por email
        user = db.users.find_one({"$or": [
            {"email": email},
            {"username": email},
            {"nombre": email}
        ]})
        
        if not user:
            print(f"Usuario '{email}' no encontrado en la base de datos.")
            return
            
        print("\n=== INFORMACIÓN DEL USUARIO ===")
        print(f"ID: {user.get('_id')}")
        print(f"Email: {user.get('email')}")
        print(f"Nombre: {user.get('nombre')}")
        print(f"Usuario: {user.get('username')}")
        print(f"Rol: {user.get('role', 'user')}")
        print(f"Cuenta activa: {not user.get('inactive', False)}")
        print(f"Cuenta bloqueada: {bool(user.get('locked_until'))}")
        print(f"Debe cambiar contraseña: {user.get('must_change_password', False)}")
        print(f"Contraseña: {'[PROTEGIDA]' if user.get('password') else '[NO DEFINIDA]'}")
        
        # Verificar si la cuenta está bloqueada
        if user.get('locked_until'):
            print("\n¡ATENCIÓN! La cuenta está bloqueada hasta:", user['locked_until'])
        
        # Verificar si la contraseña está en formato de reseteo
        if user.get('password') == 'RESET_REQUIRED':
            print("\n¡ATENCIÓN! El usuario debe restablecer su contraseña.")
            
    except Exception as e:
        print(f"Error al conectar con la base de datos: {str(e)}")
    finally:
        if 'client' in locals():
            client.close()

if __name__ == "__main__":
    check_user('edefrutos')
