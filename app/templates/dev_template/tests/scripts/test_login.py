# Script: test_login.py
# Descripción: [Explica brevemente qué hace el script]
# Uso: python3 test_login.py [opciones]
# Requiere: [librerías externas, si aplica]
# Variables de entorno: [si aplica]
# Autor: EDF Developer - 2025-05-28

from pymongo import MongoClient
from dotenv import load_dotenv
import os
import bcrypt

# Cargar variables de entorno
load_dotenv()

# Conectar a MongoDB
client = MongoClient(os.getenv('MONGO_URI'))
db = client['app_catalogojoyero_nueva']
users_collection = db['users_unified']

try:
    # Buscar el usuario
    user = users_collection.find_one({'email': 'edfrutos@gmail.com'})
    
    if user:
        print(f"Usuario encontrado: {user['email']}")
        
        # Probar contraseña
        password = '34Maf15si$'
        if bcrypt.checkpw(password.encode('utf-8'), user['password']):
            print("Contraseña correcta")
        else:
            print("Contraseña incorrecta")
    else:
        print("Usuario no encontrado")
        
except Exception as e:
    print(f"Error: {str(e)}")
finally:
    client.close()
