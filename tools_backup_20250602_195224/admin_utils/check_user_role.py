#!/usr/bin/env python3
from pymongo import MongoClient
from dotenv import load_dotenv
import os
from bson import ObjectId
from app.models import get_users_collection

# Cargar variables de entorno
load_dotenv()

# Conectar a MongoDB
client = MongoClient(os.getenv('MONGO_URI'))
db = client['app_catalogojoyero_nueva']
users_collection = get_users_collection()

try:
    # Buscar el usuario por email
    user = users_collection.find_one({'email': 'edfrutos@gmail.com'})
    
    if user:
        print(f"Usuario encontrado: {user['email']}")
        print(f"Rol actual: {user.get('role', 'No tiene rol')}")
        
        # Actualizar el rol a admin
        result = users_collection.update_one(
            {'_id': user['_id']},
            {'$set': {'role': 'admin'}}
        )
        
        if result.modified_count > 0:
            print("Rol actualizado a admin")
        else:
            print("No se pudo actualizar el rol")
    else:
        print("Usuario no encontrado")
        
except Exception as e:
    print(f"Error: {str(e)}")
finally:
    client.close()
