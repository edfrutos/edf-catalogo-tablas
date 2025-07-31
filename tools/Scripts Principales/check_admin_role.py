#!/usr/bin/env python3
from pymongo import MongoClient
import os
from datetime import datetime
from dotenv import load_dotenv
from app.models import get_users_collection

# Cargar variables de entorno
load_dotenv()

# Conectar a MongoDB
client = MongoClient(os.getenv('MONGO_URI'))
db = client['app_catalogojoyero_nueva']
users_collection = get_users_collection()

def check_and_set_admin():
    # Buscar usuario por email o nombre de usuario
    user = users_collection.find_one({
        '$or': [
            {'email': 'edfrutos@gmail.com'},
            {'username': 'edefrutos'},
            {'nombre': 'edefrutos'}
        ]
    })

    if not user:
        print("❌ Usuario edefrutos no encontrado")
        return

    print("\nInformación actual del usuario:")
    print(f"Email: {user.get('email')}")
    print(f"Nombre: {user.get('nombre', user.get('username'))}")
    print(f"Rol actual: {user.get('role', 'No especificado')}")

    if user.get('role') == 'admin':
        print("\n✅ El usuario ya tiene privilegios de administrador")
        return

    # Actualizar a rol admin
    result = users_collection.update_one(
        {'_id': user['_id']},
        {
            '$set': {
                'role': 'admin',
                'updated_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        }
    )

    if result.modified_count > 0:
        print("\n✅ Rol actualizado correctamente a admin")
        
        # Verificar la actualización
        updated_user = users_collection.find_one({'_id': user['_id']})
        print("\nInformación actualizada del usuario:")
        print(f"Email: {updated_user.get('email')}")
        print(f"Nombre: {updated_user.get('nombre', updated_user.get('username'))}")
        print(f"Rol actual: {updated_user.get('role')}")
    else:
        print("\n❌ No se pudo actualizar el rol")

if __name__ == '__main__':
    check_and_set_admin()
